# tests/test_retrain.py
import json
import tempfile
import subprocess
from pathlib import Path
import shutil
import time

def test_retrain_creates_model_and_metadata(tmp_path):
    # prepare minimal receipts + corrections
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    receipts = [
        {"id": "r1", "raw_text": "Cafe A banh mi 50k", "category": "Ăn uống", "confidence": 0.4},
        {"id": "r2", "raw_text": "Xang 95 200k", "category": "Xăng dầu", "confidence": 0.8}
    ]
    with open(data_dir / "receipts.json", "w", encoding="utf-8") as f:
        json.dump(receipts, f, ensure_ascii=False, indent=2)
    corrections = [
        {"raw_text": "Cafe A banh mi 50k", "category": "Ăn uống"}
    ]
    with open(data_dir / "corrections.json", "w", encoding="utf-8") as f:
        json.dump(corrections, f, ensure_ascii=False, indent=2)

    # run retrain
    models_root = tmp_path / "models"
    cmd = ["python", "-m", "ml.retrain", "--receipts-json", str(data_dir / "receipts.json"), "--corrections-file", str(data_dir / "corrections.json"), "--models-root", str(models_root)]
    res = subprocess.run(cmd, cwd=".", capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, f"Retrain failed: {res.stdout}\n{res.stderr}"

    # check models_metadata.json
    meta_file = models_root / "models_metadata.json"
    assert meta_file.exists(), "models_metadata.json should be created"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert isinstance(meta, list)
    assert len(meta) >= 1
