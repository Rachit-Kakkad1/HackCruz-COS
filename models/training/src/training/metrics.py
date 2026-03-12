"""
src/training/metrics.py
────────────────────────
ROUGE metric computation for Seq2SeqTrainer.
"""

import logging
import numpy as np
from typing import Callable

import evaluate
from transformers import PreTrainedTokenizer

logger = logging.getLogger(__name__)


def build_compute_metrics(tokenizer: PreTrainedTokenizer) -> Callable:
    """
    Returns a compute_metrics function for Seq2SeqTrainer
    that calculates ROUGE-1, ROUGE-2, ROUGE-L.
    """
    rouge = evaluate.load("rouge")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds

        # Replace -100 (masked padding) in labels
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

        # Decode predictions & labels
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        # Strip whitespace
        decoded_preds = [p.strip() for p in decoded_preds]
        decoded_labels = [l.strip() for l in decoded_labels]

        result = rouge.compute(
            predictions=decoded_preds,
            references=decoded_labels,
            use_stemmer=True,
        )

        # Scale to percentage for readability
        result = {k: round(v * 100, 4) for k, v in result.items()}

        # Add mean prediction length
        prediction_lens = [np.count_nonzero(p != tokenizer.pad_token_id) for p in preds]
        result["gen_len"] = np.mean(prediction_lens)

        logger.info(f"ROUGE — R1: {result['rouge1']:.2f} | R2: {result['rouge2']:.2f} | RL: {result['rougeL']:.2f}")
        return result

    return compute_metrics
