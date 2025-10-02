# ml/retrain.py
import argparse
import json
import os
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
import tempfile

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from category_classifier import CategoryClassifier

# optional MLflow
try:
    import mlflow
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

def load_receipts_json(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    return data

def build_dataframe(base_csv: Path = None, receipts_json: Path = None, corrections_file: Path = None):
    rows = []
    # 1) from base csv if provided
    if base_csv and base_csv.exists():
        df = pd.read_csv(base_csv)
        # try to find columns like in train.py
        if 'item_name' in df.columns and 'category' in df.columns:
            texts = (df['item_name'].fillna('') + ' ' + df.get('store_name','').fillna('')).astype(str)
            for t,c in zip(texts.tolist(), df['category'].astype(str).tolist()):
                rows.append({"text": t, "category": str(c)})
        elif 'raw_text' in df.columns and 'category' in df.columns:
            for t,c in zip(df['raw_text'].fillna('').astype(str).tolist(), df['category'].astype(str).tolist()):
                rows.append({"text": t, "category": str(c)})
        else:
            for _, r in df.iterrows():
                text = str(r.iloc[0])
                label = str(r.iloc[-1]) if 'label' not in df.columns else str(r['label'])
                rows.append({"text": text, "category": label})

    # 2) from receipts.json
    if receipts_json and receipts_json.exists():
        receipts = load_receipts_json(receipts_json)
        for r in receipts:
            # prefer raw_text else combine items/store_name
            txt = r.get("raw_text") or (" ".join(r.get("items", []) ) if isinstance(r.get("items"), list) else "")
            # fallback: store_name + notes
            if not txt:
                txt = f"{r.get('store_name','')} {r.get('notes','')}"
            cat = r.get("category", "") or "Khác"
            rows.append({"text": txt, "category": str(cat)})

    # 3) from corrections file (these are authoritative)
    if corrections_file and corrections_file.exists():
        try:
            with open(corrections_file, "r", encoding="utf-8") as f:
                corrections = json.load(f)
        except Exception:
            corrections = []
        for c in corrections:
            # expectation: correction items have 'raw_text' or 'item_name' and 'category'
            txt = c.get("raw_text") or c.get("item_name") or c.get("text") or ""
            cat = c.get("category") or c.get("corrected_category") or ""
            if not txt or not cat:
                # skip malformed
                continue
            rows.append({"text": txt, "category": str(cat)})

    # build df and dedupe by text content (keep last = corrections override)
    if not rows:
        return pd.DataFrame(columns=["text","category"])
    df = pd.DataFrame(rows)
    # normalize whitespace
    df['text'] = df['text'].astype(str).str.strip()
    # keep last occurrence (corrections usually appended later)
    df = df.drop_duplicates(subset=['text'], keep='last').reset_index(drop=True)
    return df

def save_models_metadata(models_root: Path, metadata_entry: dict):
    meta_file = models_root / "models_metadata.json"
    meta = []
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = []
    meta.append(metadata_entry)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base-csv', type=str, default=None, help="Optional: training csv")
    p.add_argument('--receipts-json', type=str, default='data/receipts.json', help="Receipts JSON to include")
    p.add_argument('--corrections-file', type=str, default='data/corrections.json', help="Corrections JSON file (appended by /feedback)")
    p.add_argument('--models-root', type=str, default='models', help="Root folder where models are saved")
    p.add_argument('--test-size', type=float, default=0.15)
    p.add_argument('--random-state', type=int, default=42)
    p.add_argument('--mlflow-uri', type=str, default=os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns'))
    args = p.parse_args()

    receipts_json = Path(args.receipts_json)
    corrections_file = Path(args.corrections_file)
    base_csv = Path(args.base_csv) if args.base_csv else None
    models_root = Path(args.models_root)
    models_root.mkdir(parents=True, exist_ok=True)

    df = build_dataframe(base_csv=base_csv, receipts_json=receipts_json, corrections_file=corrections_file)
    if df.empty:
        print("No training data found. Exiting.")
        return 1

    texts = df['text'].tolist()
    labels = df['category'].tolist()

    # compute data fingerprint: use corrections file + receipts file hashes when available
    data_hashes = {}
    try:
        if receipts_json.exists():
            data_hashes['receipts_sha256'] = file_sha256(str(receipts_json))
    except Exception:
        pass
    try:
        if corrections_file.exists():
            data_hashes['corrections_sha256'] = file_sha256(str(corrections_file))
    except Exception:
        pass

    git_hash = git_commit_hash()

    # split
    stratify = labels if len(set(labels))>1 else None
    X_train, X_val, y_train, y_val = train_test_split(texts, labels, test_size=args.test_size, random_state=args.random_state, stratify=stratify)

    # new model dir versioned by timestamp
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    model_dir = models_root / f"category_clf_v{ts}"
    model_dir = str(model_dir)

    clf = CategoryClassifier(model_dir=model_dir)
    print("Retrain: encoding & training...")
    meta = clf.fit(X_train, y_train)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    clf.save(model_dir)

    # evaluate
    preds = clf.predict(X_val, top_k=1)
    y_pred = [p['predicted_label'] for p in preds]
    report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)

    # save metrics
    with open(Path(model_dir)/'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # mlflow log
    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(args.mlflow_uri)
        try:
            with mlflow.start_run():
                mlflow.log_param("receipts_json", str(receipts_json))
                mlflow.log_param("corrections_file", str(corrections_file))
                for k,v in data_hashes.items():
                    mlflow.log_param(k, v)
                mlflow.log_param("git_commit", git_hash)
                if isinstance(meta, dict):
                    for k,v in meta.items():
                        try:
                            mlflow.log_param(f"meta_{k}", str(v))
                        except Exception:
                            pass
                try:
                    macro_f1 = report.get("macro avg", {}).get("f1-score", None)
                    if macro_f1 is not None:
                        mlflow.log_metric("val_macro_f1", float(macro_f1))
                except Exception:
                    pass
                mlflow.log_artifacts(str(Path(model_dir)), artifact_path="model_artifacts")
        except Exception as e:
            print("MLflow logging failed:", e)

    # update models metadata
    metadata_entry = {
        "model_dir": model_dir,
        "timestamp": ts,
        "git_commit": git_hash,
        "data_hashes": data_hashes,
        "metrics": report,
    }
    save_models_metadata(Path(args.models_root), metadata_entry)

    print("Retrain complete. Model saved to:", model_dir)
    return 0

if __name__ == "__main__":
    main()
