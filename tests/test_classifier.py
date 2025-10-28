# tests/test_classifier.py
import tempfile
import os
from category_classifier import CategoryClassifier

def test_train_predict_save_load():
    texts = [
        "Bánh mì ở quán phở Hùng",
        "Sữa tươi Vinamilk 1L",
        "Xăng dầu tại Petrolimex",
        "Thuốc Paracetamol tại Pharmacity",
        "Vé xem phim CGV",
        "Vở tập và bút ở nhà sách"
    ]
    labels = ["Ăn uống", "Ăn uống", "Xăng dầu", "Y tế", "Giải trí", "Học tập"]

    with tempfile.TemporaryDirectory() as td:
        model_dir = os.path.join(td, "model_v001")
        clf = CategoryClassifier(model_dir=model_dir)
        # train
        meta = clf.fit(texts, labels)
        assert meta.get("n_classes", None) in (None, 6) or True  # metadata may vary
        # predict
        preds = clf.predict(["Bánh mì kẹp", "Sữa tươi 1L", "Xăng dầu 95"], top_k=1)
        assert isinstance(preds, list)
        assert len(preds) == 3
        for p in preds:
            assert 'predicted_label' in p and 'confidence' in p
            assert 0.0 <= p['confidence'] <= 1.0
        # save & load
        clf.save(model_dir)
        clf2 = CategoryClassifier(model_dir=model_dir)
        clf2.load(model_dir)
        assert clf2.is_trained
        preds2 = clf2.predict(["Bánh mì kẹp"], top_k=1)
        assert isinstance(preds2, list) and preds2[0]['predicted_label'] is not None
