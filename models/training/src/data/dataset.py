"""
src/data/dataset.py
───────────────────
Handles loading, preprocessing, and tokenizing data
for FLAN-T5 summarization fine-tuning.
"""

import logging
from typing import Optional, Dict, Any

from datasets import load_dataset, DatasetDict
from transformers import PreTrainedTokenizer

logger = logging.getLogger(__name__)

# ── FLAN-T5 instruction prefix ─────────────────────────────────────────────
INSTRUCTION_PREFIX = "summarize: "


def load_hf_dataset(
    dataset_name: str,
    dataset_config: Optional[str] = None,
    num_train_samples: Optional[int] = None,
    num_val_samples: Optional[int] = None,
    seed: int = 42,
) -> DatasetDict:
    """Load a dataset from HuggingFace Hub."""
    logger.info(f"Loading dataset: {dataset_name} (config={dataset_config})")
    dataset = load_dataset(dataset_name, dataset_config)

    if num_train_samples:
        dataset["train"] = dataset["train"].shuffle(seed=seed).select(range(num_train_samples))
    if num_val_samples and "validation" in dataset:
        dataset["validation"] = dataset["validation"].select(range(num_val_samples))

    logger.info(f"Train size: {len(dataset['train'])} | Val size: {len(dataset.get('validation', []))}")
    return dataset


def load_custom_dataset(
    csv_path: str,
    text_col: str,
    summary_col: str,
    val_size: float = 0.1,
    seed: int = 42,
) -> DatasetDict:
    """
    Load a custom CSV file as a dataset.

    Expected CSV format:
        text_col        | summary_col
        "Full article…" | "Short summary…"
    """
    import pandas as pd
    from datasets import Dataset
    from sklearn.model_selection import train_test_split

    logger.info(f"Loading custom CSV: {csv_path}")
    df = pd.read_csv(csv_path)[[text_col, summary_col]].dropna()

    train_df, val_df = train_test_split(df, test_size=val_size, random_state=seed)
    return DatasetDict({
        "train": Dataset.from_pandas(train_df.reset_index(drop=True)),
        "validation": Dataset.from_pandas(val_df.reset_index(drop=True)),
    })


# ── Tokenization ─────────────────────────────────────────────────────────────

def build_preprocess_fn(
    tokenizer: PreTrainedTokenizer,
    text_column: str,
    summary_column: str,
    max_input_length: int = 512,
    max_target_length: int = 128,
):
    """
    Returns a preprocessing function compatible with dataset.map().
    Adds the FLAN-T5 instruction prefix to every input.
    """

    def preprocess(examples: Dict[str, Any]) -> Dict[str, Any]:
        # Add instruction prefix so FLAN-T5 knows the task
        inputs = [INSTRUCTION_PREFIX + text for text in examples[text_column]]
        targets = examples[summary_column]

        # Tokenize inputs
        model_inputs = tokenizer(
            inputs,
            max_length=max_input_length,
            truncation=True,
            padding=False,          # DataCollator handles dynamic padding
        )

        # Tokenize targets (labels)
        labels = tokenizer(
            text_target=targets,
            max_length=max_target_length,
            truncation=True,
            padding=False,
        )

        # Replace padding token id in labels with -100 so loss ignores them
        model_inputs["labels"] = [
            [(token if token != tokenizer.pad_token_id else -100) for token in label]
            for label in labels["input_ids"]
        ]

        return model_inputs

    return preprocess


def tokenize_dataset(
    dataset: DatasetDict,
    tokenizer: PreTrainedTokenizer,
    text_column: str,
    summary_column: str,
    max_input_length: int,
    max_target_length: int,
    num_workers: int = 4,
) -> DatasetDict:
    """Apply tokenization across all splits."""
    preprocess_fn = build_preprocess_fn(
        tokenizer, text_column, summary_column,
        max_input_length, max_target_length
    )

    cols_to_remove = dataset["train"].column_names

    tokenized = dataset.map(
        preprocess_fn,
        batched=True,
        num_proc=num_workers,
        remove_columns=cols_to_remove,
        desc="Tokenizing dataset",
    )

    logger.info("Tokenization complete.")
    return tokenized
