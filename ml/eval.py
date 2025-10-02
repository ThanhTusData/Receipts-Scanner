#ml/eval.py

import argparse, json
from pathlib import Path
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt

from category_classifier import CategoryClassifier

def load_texts_labels(path: str):
    df = pd.read_csv(path)
    if 'item_name' in df.columns and 'category' in df.columns:
        texts = (df['item_name'].fillna('') + ' ' + df.get('store_name','').fillna('')).astype(str).tolist()
        labels = df['category'].astype(str).tolist()
    elif 'raw_text' in df.columns and 'category' in df.columns:
        texts = df['raw_text'].fillna('').astype(str).tolist()
        labels = df['category'].astype(str).tolist()
    else:
        texts = df.iloc[:,0].astype(str).tolist()
        labels = df.iloc[:,-1].astype(str).tolist()
    return texts, labels

def plot_confusion(cm, classes, out_path):
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=range(len(classes)), yticks=range(len(classes)), xticklabels=classes, yticklabels=classes, ylabel='True label', xlabel='Predicted label', title='Confusion matrix')
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-dir', type=str, default='models/category_clf_v001')
    p.add_argument('--data-path', type=str, default='/mnt/data/items_train_200.csv')
    args = p.parse_args()

    clf = CategoryClassifier(model_dir=args.model_dir)
    clf.load(args.model_dir)

    texts, labels = load_texts_labels(args.data_path)
    preds = clf.predict(texts, top_k=1)
    y_pred = [p['predicted_label'] for p in preds]

    report = classification_report(labels, y_pred, output_dict=True, zero_division=0)
    # confusion
    classes = clf.encoder.classes_.tolist() if clf.encoder is not None else sorted(list(set(labels)))
    cm = confusion_matrix(labels, y_pred, labels=classes)
    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    # save report and confusion
    with open(Path(args.model_dir)/'eval_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    np.savetxt(Path(args.model_dir)/'confusion_matrix.csv', cm, delimiter=",", fmt='%d')
    # plot confusion matrix image
    try:
        plot_confusion(cm, classes, Path(args.model_dir)/'confusion_matrix.png')
    except Exception as e:
        print("Could not plot confusion matrix:", e)
    print("Evaluation complete. Report saved to:", args.model_dir)

if __name__ == "__main__":
    main()
