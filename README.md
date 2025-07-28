# 🧾 ReceiptsScanner

**ReceiptsScanner** is a Streamlit-based intelligent receipt scanner and expense analyzer that allows users to capture receipt images, automatically extract data, categorize spending, and visualize personal financial insights.

---

## 🚀 Features

### 📸 Smart Receipt Scanning
- Uses **Tesseract OCR** with **OpenCV** preprocessing (simple + enhanced) to extract:
  - Store name
  - Total amount
  - Purchase date
  - Phone number & address
  - List of purchased items
- Multiple OCR configurations are combined for improved accuracy.
- Assigns a **confidence score** (0–100) to scanned receipts.

### 🧠 Category Classification (Rule-based + ML)
- Hybrid classification approach:
  - **Rule-based keyword matching** via regex patterns
  - **Naive Bayes + TF-IDF** for text classification
- Predicts categories like: *Food & Drink*, *Shopping*, *Fuel*, *Health*, etc.
- Current accuracy: **~65%**
- Manual corrections are supported.

### ✏️ Manual Review & Editing
- After scanning, users can:
  - Preview extracted data
  - Edit incorrect fields
  - Select category
  - Save the receipt

### 📊 Expense Analytics
- Visualizes spending patterns using **Plotly** charts:
  - Pie chart by category
  - Bar chart by month
  - Daily/weekly spending trends
  - Top stores and categories
- Shows insights like:
  - Total and average spending
  - Monthly average
  - Trend changes
  - Receipt confidence metrics

### 💾 Data Management
- Data is stored in a local JSON file.
- Features include:
  - View, filter, sort, and search receipts
  - Export to CSV
  - Bulk delete/reset functionality

---

## 📁 Sample Data

- The project includes **sample receipt data** stored in the `data/` directory.
- You can explore features and analytics even without scanning real images.

---

## ⚠️ Known Limitations

- ⏳ **Slow processing** with large image files or many receipts
- 📉 **Low accuracy (~65%)** on some receipts, especially with poor quality or unusual formats
- 🧠 **Basic ML model**, not adaptive or personalized
- 🔧 **No database/cloud integration** (all data is stored locally)
- 🧩 **UI is functional but not yet optimized** for performance

---

## 🔭 Planned Improvements

- Boost OCR accuracy with:
  - Binarization, de-noising, deskewing
  - Better selection of best OCR result
- Improve ML model using:
  - Embedding-based classification
  - Feedback learning loop (user correction integration)
- Cloud integration (MongoDB/PostgreSQL)
- REST API or mobile/web support
- Multilingual OCR or integration with **Google Vision API**

---

## 📦 Tech Stack

| Component       | Tool / Library                  |
|----------------|----------------------------------|
| Web App        | [Streamlit](https://streamlit.io) |
| OCR            | [Tesseract OCR](https://github.com/tesseract-ocr/tesseract), OpenCV |
| ML Classifier  | scikit-learn (Naive Bayes + TF-IDF) |
| Charts         | Plotly                           |
| Data Storage   | JSON (local)                     |

---

## 🛠 Setup Instructions

```bash
# 1. Create and activate virtual environment
python -m venv receipts_env
source receipts_env/bin/activate  # or receipts_env\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

---

## 📌 Summary

> **ReceiptsScanner** is a smart yet simple receipt-scanning and expense-tracking system designed for personal use. It combines OCR, rule-based NLP, and machine learning to automate financial logging from receipts. Though the current version is limited, it serves as a strong foundation for future enhancements in performance, intelligence, and usability.

---
