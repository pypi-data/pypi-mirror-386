# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, TypedDict, Union, cast

from datasets import Dataset, DatasetDict, load_dataset
from tqdm import tqdm

from megatron.bridge.data.builders.finetuning_dataset import FinetuningDatasetBuilder
from megatron.bridge.data.datasets.packed_sequence import PackedSequenceSpecs
from megatron.bridge.data.datasets.sft import get_dataset_root
from megatron.bridge.training.config import FinetuningDatasetConfig
from megatron.bridge.training.tokenizers.tokenizer import MegatronTokenizer
from megatron.bridge.utils.common_utils import print_rank_0


logger = logging.getLogger(__name__)


class ProcessExampleOutput(TypedDict):
    """Expected output structure from a `ProcessExampleFn`."""

    input: str
    output: str
    original_answers: list[str]


class ProcessExampleFn(Protocol):
    """Protocol defining the signature for a function that processes a single dataset example."""

    def __call__(
        self, example: dict[str, Any], tokenizer: Optional[MegatronTokenizer] = None
    ) -> ProcessExampleOutput: ...


@dataclass(kw_only=True)
class HFDatasetConfig(FinetuningDatasetConfig):
    """Configuration specific to using Hugging Face datasets for finetuning.

    Inherits from FinetuningDatasetConfig and adds HF-specific options.

    Attributes:
        dataset_name: Name of the dataset on the Hugging Face Hub.
        process_example_fn: A callable conforming to ProcessExampleFn protocol
                            to process raw examples into the desired format.
        dataset_subset: Optional subset name if the dataset has multiple subsets.
        dataset_dict: Optional pre-loaded DatasetDict to use instead of downloading.
        split: Optional specific split to load (e.g., 'train[:10%]').
        download_mode: Download mode for load_dataset (e.g., 'force_redownload').
        val_proportion: Proportion of the training set to use for validation if
                        no validation set is present.
        split_val_from_train: If True, creates validation set from training set.
                              If False, uses test set to create validation set.
        delete_raw: If True, delete the raw downloaded dataset files after processing.
        rewrite: If True, rewrite existing processed files.
        hf_kwargs: Additional keyword arguments to pass to `load_dataset`.
        hf_filter_lambda: Optional function to filter the loaded dataset.
        hf_filter_lambda_kwargs: Optional keyword arguments for `hf_filter_lambda`.
    """

    dataset_name: str
    process_example_fn: ProcessExampleFn
    dataset_subset: Optional[str] = None
    dataset_dict: Optional[DatasetDict] = None
    split: Optional[str] = None
    download_mode: Optional[str] = None
    val_proportion: Optional[float] = 0.05
    split_val_from_train: bool = True
    delete_raw: bool = False
    rewrite: bool = True
    hf_kwargs: Optional[dict[str, Any]] = None
    hf_filter_lambda: Optional[Callable] = None
    hf_filter_lambda_kwargs: Optional[dict[str, Any]] = None


def preprocess_and_split_data(
    dset: DatasetDict,
    dataset_name: str,
    dataset_root: Path,
    tokenizer: MegatronTokenizer,
    process_example_fn: ProcessExampleFn,
    split_val_from_train: bool = True,
    val_proportion: Optional[float] = None,
    train_aliases: tuple[str] = ("train", "training"),
    test_aliases: tuple[str] = ("test", "testing"),
    val_aliases: tuple[str] = ("val", "validation", "valid", "eval"),
    delete_raw: bool = False,
    seed: int = 1234,
    rewrite: bool = False,
    do_test: bool = True,
    do_validation: bool = True,
):
    """Download, preprocess, split, and save a Hugging Face dataset to JSONL files.

    Handles splitting into train/validation/test sets based on available splits
    and the `val_proportion` parameter. Processes each example using the
    provided `process_example_fn` and saves the results.

    Args:
        dset: The loaded Hugging Face DatasetDict.
        dataset_name: Name of the dataset (for logging).
        dataset_root: The root directory to save the processed JSONL files.
        tokenizer: The tokenizer instance.
        process_example_fn: Function to process individual examples.
        split_val_from_train: If True, split validation from train set.
                              Otherwise, split from test set (if available).
        val_proportion: Proportion of data to use for validation split.
        train_aliases: Tuple of possible names for the training split.
        test_aliases: Tuple of possible names for the test split.
        val_aliases: Tuple of possible names for the validation split.
        delete_raw: If True, delete raw HF dataset cache after processing.
        seed: Random seed for splitting.
        rewrite: If True, overwrite existing processed files.
    """
    logger.info(f"Preprocessing {dataset_name} to jsonl format and splitting...")
    save_splits = {}
    train_set: Dataset | None = None
    val_set: Dataset | None = None
    test_set: Dataset | None = None

    for alias in train_aliases:
        train_set = dset.get(alias)
        if train_set is not None:
            break

    if do_validation:
        for alias in val_aliases:
            val_set = dset.get(alias)
            if val_set is not None:
                break

    if do_test:
        for alias in test_aliases:
            test_set = dset.get(alias)
            if test_set is not None:
                break

    assert train_set, f"Train set with aliases: {train_aliases} not found in dataset"
    train_set = cast(Dataset, train_set)

    if val_proportion:
        if split_val_from_train:
            split_dataset = train_set.train_test_split(test_size=val_proportion, seed=seed)
            save_splits["training"] = split_dataset["train"]
            save_splits["validation"] = split_dataset["test"]
            if val_set:
                save_splits["test"] = val_set
        else:
            assert val_set, f"Validation set with aliases: {val_aliases} not found in dataset"
            val_set = cast(Dataset, val_set)
            split_dataset = val_set.train_test_split(test_size=val_proportion, seed=seed)
            save_splits["training"] = train_set
            save_splits["validation"] = split_dataset["test"]
            save_splits["test"] = split_dataset["train"]
    else:
        save_splits["training"] = train_set
        if val_set:
            save_splits["validation"] = val_set
        if test_set:
            save_splits["test"] = test_set

    if test_set:
        test_set = cast(Dataset, test_set)
        save_splits["test"] = test_set

    for split_name, dataset in save_splits.items():
        output_file = dataset_root / f"{split_name}.jsonl"

        if output_file.exists() and output_file.is_file():
            if not rewrite:
                logger.info(f"{output_file} exists, skipping...")
                continue
            else:
                logger.info(f"{output_file} exists, deleting and rewriting...")
                os.remove(output_file)
                for p in glob.glob(str(output_file) + "*"):
                    if os.path.exists(p):
                        os.remove(p)

        with output_file.open("w", encoding="utf-8") as f:
            for example in tqdm(dataset, desc=f"Processing {split_name} split"):
                json_line = {}

                processed_example = process_example_fn(example, tokenizer)
                # Write each example as a JSON line in the output file
                json_line["input"] = processed_example["input"]
                json_line["output"] = processed_example["output"]
                if split_name == "test":
                    json_line["original_answers"] = processed_example["original_answers"]
                f.write(json.dumps(json_line) + "\n")

        logger.info(f"{split_name} split saved to {output_file}")

    if delete_raw:
        for p in dataset_root.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
            elif ".jsonl" not in str(p.name):
                p.unlink()


class HFDatasetBuilder(FinetuningDatasetBuilder):
    """Builder class for Hugging Face datasets.

    This class extends FinetuningDatasetBuilder to work with Hugging Face datasets instead of file paths.
    It provides methods to build datasets from Hugging Face's datasets library.
    """

    def __init__(
        self,
        dataset_name: str,
        tokenizer,
        process_example_fn: ProcessExampleFn,
        dataset_dict: Optional[DatasetDict] = None,
        dataset_subset: Optional[str] = None,
        dataset_root: Optional[Union[str, Path]] = None,
        split=None,
        seq_length=1024,
        seed: int = 1234,
        memmap_workers: int = 1,
        max_train_samples: Optional[int] = None,
        packed_sequence_specs: Optional[PackedSequenceSpecs] = None,
        download_mode: Optional[str] = None,
        val_proportion: Optional[float] = 0.05,
        split_val_from_train: bool = True,
        rewrite: bool = True,
        delete_raw: bool = False,
        hf_kwargs: Optional[dict[str, Any]] = None,
        dataset_kwargs: Optional[dict[str, Any]] = None,
        hf_filter_lambda: Optional[Callable] = None,
        hf_filter_lambda_kwargs: Optional[dict[str, Any]] = None,
        do_validation: bool = True,
        do_test: bool = True,
    ) -> None:
        """Initializes the HFDatasetBuilder.

        Args:
            dataset_name: Name of the dataset on Hugging Face Hub.
            tokenizer: The tokenizer instance.
            is_built_on_rank: Callable to determine if data should be built on the current rank.
            process_example_fn: Function conforming to ProcessExampleFn protocol.
            dataset_dict: Optional pre-loaded DatasetDict.
            dataset_subset: Optional dataset subset name.
            dataset_root: Optional root directory for data; defaults based on dataset_name.
            split: Optional specific split to load.
            seq_length: Sequence length for processing.
            seed: Random seed.
            memmap_workers: Number of workers for memmapping.
            max_train_samples: Optional maximum number of training samples.
            packed_sequence_specs: Optional PackedSequenceSpecs for packed sequence datasets.
            download_mode: Download mode for `load_dataset`.
            val_proportion: Proportion for validation split.
            split_val_from_train: Whether to split validation from train set.
            rewrite: Whether to rewrite existing processed files.
            delete_raw: Whether to delete raw downloaded files.
            hf_kwargs: Additional kwargs for `load_dataset`.
            dataset_kwargs: Additional kwargs for the underlying dataset constructor.
            hf_filter_lambda: Optional function to filter the dataset.
            hf_filter_lambda_kwargs: Optional kwargs for the filter function.
            do_validation: Whether to build the validation set.
            do_test: Whether to build the test set.
        """
        dataset_root = Path(dataset_root) if dataset_root else get_dataset_root(dataset_name)

        # Initialize the parent class with common parameters
        super().__init__(
            dataset_root=dataset_root,
            tokenizer=tokenizer,
            seq_length=seq_length,
            seed=seed,
            memmap_workers=memmap_workers,
            dataset_kwargs=dataset_kwargs,
            max_train_samples=max_train_samples,
            packed_sequence_specs=packed_sequence_specs,
            do_validation=do_validation,
            do_test=do_test,
        )

        # HF-specific attributes
        self.dataset_name = dataset_name
        self.dataset_subset = dataset_subset
        self.dataset_dict = dataset_dict
        self.split = split
        self.download_mode = download_mode
        self.hf_kwargs = hf_kwargs or {}
        self.val_proportion = val_proportion
        self.split_val_from_train = split_val_from_train
        self.delete_raw = delete_raw
        self.process_example_fn = process_example_fn
        self.hf_filter_lambda = hf_filter_lambda
        self.hf_filter_lambda_kwargs = hf_filter_lambda_kwargs or {}
        self.rewrite = rewrite

        if not val_proportion:
            self.do_validation = False
            self.do_test = False

        print_rank_0(f"Building HFDataset {self.dataset_name}")

    def prepare_data(self) -> None:
        """Loads/downloads the dataset, filters it, preprocesses/splits it, and prepares memmaps."""
        if self.download_mode != "force_redownload" and self.hf_filter_lambda:
            raise ValueError("`hf_filter_lambda` is not supported when `download_mode` is not `force_redownload`")

        if self.dataset_dict:
            dataset = self.dataset_dict
        else:
            dataset = self._load_dataset()

        if self.hf_filter_lambda:
            dataset = dataset.filter(self.hf_filter_lambda, **self.hf_filter_lambda_kwargs)

        preprocess_and_split_data(
            dataset,
            self.dataset_name,
            self.dataset_root,
            tokenizer=self.tokenizer,
            process_example_fn=self.process_example_fn,
            split_val_from_train=self.split_val_from_train,
            val_proportion=self.val_proportion,
            delete_raw=self.delete_raw,
            seed=self.seed,
            rewrite=self.rewrite,
            do_test=self.do_test,
            do_validation=self.do_validation,
        )
        super().prepare_data()

    def _load_dataset(self) -> DatasetDict:
        """Load the dataset from Hugging Face or use the provided dataset."""
        if isinstance(self.dataset_name, str):
            logger.info(f"Loading HF dataset from {self.dataset_name} to {self.dataset_root}")
            dataset = load_dataset(
                self.dataset_name,
                name=self.dataset_subset,
                cache_dir=str(self.dataset_root),
                split=self.split,
                **self.hf_kwargs,
                download_mode=self.download_mode,
            )
        else:
            raise ValueError("Expected `dataset_name` to be str, got " + str(type(self.dataset_name)))

        return dataset
