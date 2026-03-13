import json
import time
import sys
from pathlib import Path
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses

def train_embedding_model():
    data_path = Path("data/training_dataset.jsonl")
    if not data_path.exists():
        print(f"Error: {data_path} not found")
        return

    triplets = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            triplets.append(json.loads(line))

    if len(triplets) < 500:
        print(f"Warning: Only {len(triplets)} triplets found. Minimum 500 required for training. Skipping.")
        sys.exit(1)

    # Convert to InputExample
    train_examples = [InputExample(texts=[t['anchor'], t['positive'], t['negative']]) for t in triplets]
    
    # Logic for finding latest version or base
    models_dir = Path("models/embedding")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    versions = []
    for d in models_dir.iterdir():
        if d.is_dir() and d.name.startswith("cos-embedding-v"):
            if (d / "READY").exists():
                try:
                    v = int(d.name.replace("cos-embedding-v", ""))
                    versions.append(v)
                except ValueError:
                    continue
    
    if versions:
        latest_v = max(versions)
        base_model_path = str(models_dir / f"cos-embedding-v{latest_v}")
        next_v = latest_v + 1
    else:
        base_model_path = "BAAI/bge-small-en-v1.5"
        next_v = 1
        
    output_path = models_dir / f"cos-embedding-v{next_v}"
    
    print(f"Loading base model: {base_model_path}")
    model = SentenceTransformer(base_model_path)
    
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=32, pin_memory=False)
    train_loss = losses.TripletLoss(model=model)
    
    print(f"Starting training on {len(triplets)} triplets...")
    start_time = time.time()
    
    # Train
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=1,
        warmup_steps=100,
        show_progress_bar=True
    )
    
    # Save model and sentinel
    model.save(str(output_path))
    (output_path / "READY").touch()
    
    end_time = time.time()
    
    print(f"version saved: cos-embedding-v{next_v}")
    print(f"triplets used: {len(triplets)}")
    print(f"time taken: {int(end_time - start_time)}s")

if __name__ == "__main__":
    train_embedding_model()
