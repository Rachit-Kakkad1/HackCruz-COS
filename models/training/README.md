# 🧠 FLAN-T5 Small — Summarization Fine-Tuning

Fine-tune `google/flan-t5-small` (80MB) for semantic text summarization.
Designed to slot into the **Context Capsule pipeline**:

```
Raw Window Text → FLAN-T5 → Semantic Summary → Embedding Model → Vector DB
```

---

## 📁 Folder Structure

```
models/training/
├── configs/
│   └── train_config.yaml        ← All hyperparameters & settings
│
├── data/
│   ├── raw/                     ← Drop your raw CSVs here
│   └── processed/               ← Auto-generated tokenized cache
│
├── src/
│   ├── data/dataset.py          ← Load, preprocess & tokenize
│   ├── model/model.py           ← Load FLAN-T5 & tokenizer
│   ├── training/
│   │   ├── trainer.py           ← Build Seq2SeqTrainer
│   │   └── metrics.py           ← ROUGE metric computation
│   └── inference/pipeline.py   ← SummarizationPipeline class
│
├── scripts/
│   └── export_onnx.py           ← Export encoder to ONNX
│
├── outputs/
│   ├── checkpoints/             ← Model checkpoints (auto-created)
│   │   └── best/                ← Best model saved here after training
│   └── logs/                    ← TensorBoard logs
│
├── train.py                     ← 🚀 Main training entry point
├── evaluate.py                  ← 📊 ROUGE evaluation on test set
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train on CNN/DailyMail (default)

```bash
python train.py
```

### 3. Train on your own CSV

```bash
python train.py --custom_csv data/raw/my_data.csv
```

### 4. Run inference

```bash
python -m src.inference.pipeline \
  --model_path outputs/checkpoints/best \
  --text "Your long article text here..."
```

### 5. Evaluate on test set

```bash
python evaluate.py --model_path outputs/checkpoints/best
```

### 6. Export to ONNX

```bash
python scripts/export_onnx.py --model_path outputs/checkpoints/best
```

---

## 🔌 Use in COS Pipeline

```python
from src.inference.pipeline import SummarizationPipeline

summarizer = SummarizationPipeline(model_path="outputs/checkpoints/best")

raw_text = "... your captured window text ..."
summary = summarizer.summarize(raw_text)

# summary → embedding model → vector DB
```

---

## 📊 Expected ROUGE Scores (CNN/DailyMail, 3 epochs)

| Metric | Approx. Score |
|--------|--------------|
| ROUGE-1 | ~0.38 |
| ROUGE-2 | ~0.17 |
| ROUGE-L | ~0.35 |
