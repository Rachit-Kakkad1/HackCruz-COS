import subprocess
import sqlite3
import json
import time
import schedule
import sys
from pathlib import Path
from datetime import datetime

def load_latest_model(models_dir="models/embedding"):
    base_model = "BAAI/bge-small-en-v1.5"
    m_dir = Path(models_dir)
    if not m_dir.exists():
        return base_model
    
    versions = []
    for d in m_dir.iterdir():
        if d.is_dir() and d.name.startswith("cos-embedding-v"):
            if (d / "READY").exists():
                try:
                    ver = int(d.name.replace("cos-embedding-v", ""))
                    versions.append((ver, d))
                except ValueError:
                    continue
    
    if not versions:
        return base_model
    
    return str(sorted(versions, key=lambda x: x[0])[-1][1])

def get_new_context_count(db_path, last_run_file="data/last_run.json"):
    last_run_path = Path(last_run_file)
    last_ts = 0
    if last_run_path.exists():
        with last_run_path.open("r", encoding="utf-8") as f:
            try:
                last_ts = json.load(f).get("timestamp", 0)
            except json.JSONDecodeError:
                pass
    
    if not Path(db_path).exists():
        return 0

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contexts WHERE timestamp > ?", (last_ts,))
        return cursor.fetchone()[0]

def run_pipeline(db_path):
    print(f"[{datetime.now()}] Starting pipeline execution...")
    
    # 1. Dataset Builder
    print("Running dataset_builder.py...")
    res = subprocess.run([sys.executable, "training/dataset_builder.py", str(db_path)], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    
    # 2. Hard Negative Mining
    print("Running hard_negative_mining.py...")
    res = subprocess.run([sys.executable, "training/hard_negative_mining.py"], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    
    # 3. Train Embeddings
    print("Running train_embeddings.py...")
    res = subprocess.run([sys.executable, "training/train_embeddings.py"], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        print("Training failed or skipped. Aborting pipeline.")
        return

    # 4. Find models for evaluation
    models_dir = Path("models/embedding")
    versions = []
    if models_dir.exists():
        for d in models_dir.iterdir():
            if d.is_dir() and d.name.startswith("cos-embedding-v"):
                if (d / "READY").exists():
                    try:
                        v = int(d.name.replace("cos-embedding-v", ""))
                        versions.append((v, d))
                    except ValueError:
                        continue
    
    sorted_vers = sorted(versions, key=lambda x: x[0])
    if not sorted_vers:
        print("No versioned models found for evaluation.")
        return
        
    new_model_path = str(sorted_vers[-1][1])
    if len(sorted_vers) >= 2:
        old_model_path = str(sorted_vers[-2][1])
    else:
        old_model_path = "BAAI/bge-small-en-v1.5"

    # 5. Evaluate
    print(f"Evaluating: New={new_model_path} vs Old={old_model_path}")
    res = subprocess.run([
        sys.executable, "training/evaluate_model.py", 
        "--new-model", new_model_path, 
        "--old-model", old_model_path
    ], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    
    if res.returncode == 0:
        # DEPLOY status from evaluate_model.py
        last_run_path = Path("data/last_run.json")
        last_run_path.parent.mkdir(parents=True, exist_ok=True)
        with last_run_path.open("w", encoding="utf-8") as f:
            json.dump({"timestamp": int(time.time())}, f)
        print("Pipeline Result: NEW MODEL DEPLOYED")
    elif res.returncode == 2:
        print("Pipeline Result: EVAL SET CREATED — re-run when threshold met again")
    else:
        print("Pipeline Result: KEPT CURRENT MODEL")

def check_and_run():
    # Use the established DB path in this project
    db_path = Path("cos-backend-lite/data/cos.db")
    
    count = get_new_context_count(db_path)
    print(f"[{datetime.now()}] New contexts since last run: {count}")
    
    if count > 2000:
        run_pipeline(db_path)
    else:
        print("Threshold (2000) not met. Skipping run.")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Training Scheduler started.")
    
    # Startup check
    check_and_run()
    
    # Schedule every 6 hours
    schedule.every(6).hours.do(check_and_run)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
