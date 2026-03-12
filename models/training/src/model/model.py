"""
src/model/model.py
──────────────────
Load FLAN-T5 Small model and tokenizer from HuggingFace.
"""

import logging
from typing import Tuple

from transformers import T5ForConditionalGeneration, AutoTokenizer

logger = logging.getLogger(__name__)


def load_model_and_tokenizer(
    model_name: str = "google/flan-t5-small",
) -> Tuple[T5ForConditionalGeneration, AutoTokenizer]:
    """
    Download (or load from local cache) the FLAN-T5 model and tokenizer.

    Parameters
    ----------
    model_name : str
        HuggingFace model card ID or local path.

    Returns
    -------
    model, tokenizer
    """
    logger.info(f"Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    logger.info(f"Loading model: {model_name}")
    model = T5ForConditionalGeneration.from_pretrained(model_name)

    num_params = sum(p.numel() for p in model.parameters()) / 1e6
    logger.info(f"Model loaded — {num_params:.1f}M parameters")

    return model, tokenizer
