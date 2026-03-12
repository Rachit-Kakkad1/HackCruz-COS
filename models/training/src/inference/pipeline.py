"""
src/inference/pipeline.py
─────────────────────────
Summarization pipeline — load a fine-tuned FLAN-T5 model
and run inference on raw text.

Usage (standalone):
    python -m src.inference.pipeline \\
        --model_path outputs/checkpoints/best \\
        --text "Your long article text here…"
"""

import argparse
import logging
from typing import List, Union

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

INSTRUCTION_PREFIX = "summarize: "


class SummarizationPipeline:
    """
    Lightweight wrapper around a fine-tuned FLAN-T5 model
    for single-text or batch summarization.
    """

    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        max_input_length: int = 512,
        max_new_tokens: int = 128,
        num_beams: int = 4,
        no_repeat_ngram_size: int = 3,
    ):
        self.max_input_length = max_input_length
        self.max_new_tokens = max_new_tokens
        self.num_beams = num_beams
        self.no_repeat_ngram_size = no_repeat_ngram_size

        # ── Device selection ───────────────────────────────────────────────
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Loading model from: {model_path}  (device={self.device})")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(self.device)
        self.model.eval()
        logger.info("Model ready.")

    # ── Public API ────────────────────────────────────────────────────────────

    def summarize(self, text: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Summarize one string or a list of strings.

        Parameters
        ----------
        text : str | List[str]
            Raw text(s) to summarize.

        Returns
        -------
        str | List[str]
            Summary / list of summaries.
        """
        single = isinstance(text, str)
        texts = [text] if single else text

        prefixed = [INSTRUCTION_PREFIX + t for t in texts]

        inputs = self.tokenizer(
            prefixed,
            return_tensors="pt",
            max_length=self.max_input_length,
            truncation=True,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                num_beams=self.num_beams,
                no_repeat_ngram_size=self.no_repeat_ngram_size,
                early_stopping=True,
            )

        summaries = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        return summaries[0] if single else summaries


# ── CLI entry point ───────────────────────────────────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(description="FLAN-T5 Summarization Inference")
    parser.add_argument("--model_path", type=str, required=True, help="Path to fine-tuned model directory")
    parser.add_argument("--text", type=str, help="Text to summarize (use --file for longer texts)")
    parser.add_argument("--file", type=str, help="Path to a .txt file containing the text")
    parser.add_argument("--max_input_length", type=int, default=512)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--num_beams", type=int, default=4)
    parser.add_argument("--device", type=str, default="auto")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    args = _parse_args()

    pipeline = SummarizationPipeline(
        model_path=args.model_path,
        device=args.device,
        max_input_length=args.max_input_length,
        max_new_tokens=args.max_new_tokens,
        num_beams=args.num_beams,
    )

    if args.file:
        with open(args.file) as f:
            raw_text = f.read()
    elif args.text:
        raw_text = args.text
    else:
        raise ValueError("Provide either --text or --file")

    summary = pipeline.summarize(raw_text)
    print("\n" + "─" * 60)
    print("📄 SUMMARY:")
    print("─" * 60)
    print(summary)
    print("─" * 60)
