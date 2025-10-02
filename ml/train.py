# ml/train.py
import argparse
import json
import os
import hashlib
import subprocess
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

from category_classifier import CategoryClassifier

# optional MLflow
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except Exception:
    MLFLOW_AVAILABLE = False


def file_sha256(path: str, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def git_commit_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return "unknown"


def load_data(path: str):
    df = pd.read_csv(path)
    # try to find text and label columns
    if 'item_name' in df.columns and 'category' in df.columns:
        texts = (df['item_name'].fillna('') + ' ' + df.get('store_name','').fillna('')).astype(str).tolist()
        labels = df['category'].astype(str).tolist()
    elif 'raw_text' in df.columns and 'category' in df.columns:
        texts = df['raw_text'].fillna('').astype(str).tolist()
        labels = df['category'].astype(str).tolist()
    else:
        # fallback: treat first col as text and 'label' or last column as label
        texts = df.iloc[:,0].astype(str).tolist()
        if 'label' in df.columns:
            labels = df['label'].astype(str).tolist()
        else:
            labels = df.iloc[:,-1].astype(str).tolist()
    return texts, labels


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-path', type=str, default='/mnt/data/items_train_200.csv')
    p.add_argument('--model-dir', type=str, default='models/category_clf_v001')
    p.add_argument('--test-size', type=float, default=0.15)
    p.add_argument('--random-state', type=int, default=42)
    p.add_argument('--mlflow-uri', type=str, default=os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns'))
    args = p.parse_args()

    texts, labels = load_data(args.data_path)
    if not texts:
        raise SystemExit("No training data found at: " + args.data_path)

    # compute data hash for reproducibility
    data_hash = None
    try:
        data_hash = file_sha256(args.data_path)
    except Exception:
        data_hash = "unknown"

    git_hash = git_commit_hash()

    # split
    stratify = labels if len(set(labels))>1 else None
    X_train, X_val, y_train, y_val = train_test_split(texts, labels, test_size=args.test_size, random_state=args.random_state, stratify=stratify)

    clf = CategoryClassifier(model_dir=args.model_dir)
    print("Encoding & training... (this may download sentence-transformers model if not present)")
    meta = clf.fit(X_train, y_train)
    # save classifier objects
    cls_save_dir = Path(args.model_dir)
    cls_save_dir.mkdir(parents=True, exist_ok=True)
    clf.save(args.model_dir)

    # evaluate on validation set
    preds = clf.predict(X_val, top_k=1)
    y_pred = [p['predicted_label'] for p in preds]
    report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)

    # save metrics locally
    with open(cls_save_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # MLflow logging (if available)
    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(args.mlflow_uri)
        try:
            with mlflow.start_run():
                mlflow.log_param("data_path", args.data_path)
                mlflow.log_param("data_hash", data_hash)
                mlflow.log_param("git_commit", git_hash)
                mlflow.log_param("model_dir", args.model_dir)
                mlflow.log_param("test_size", args.test_size)
                # log metadata returned by classifier if any
                if isinstance(meta, dict):
                    for k, v in meta.items():
                        try:
                            mlflow.log_param(f"meta_{k}", str(v))
                        except Exception:
                            pass
                # log metrics: macro avg f1
                try:
                    macro_f1 = report.get("macro avg", {}).get("f1-score", None)
                    if macro_f1 is not None:
                        mlflow.log_metric("val_macro_f1", float(macro_f1))
                except Exception:
                    pass
                # log whole metrics.json as artifact and all model files
                mlflow.log_artifacts(str(cls_save_dir), artifact_path="model_artifacts")
        except Exception as e:
            print("Warning: mlflow logging failed:", e)
    else:
        print("MLflow not available. To enable, install mlflow and set MLFLOW_TRACKING_URI.")

    print("Training complete. Model saved to:", args.model_dir)
    print("Validation Macro F1:", report.get('macro avg', {}).get('f1-score'))


if __name__ == "__main__":
    main()
