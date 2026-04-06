# 🚀 AntiGravity AI - Invoice Automation

A full-stack, AI-powered invoice automation system that extracts data from invoices using OCR, categorizes expenses using machine learning, and visualizes spending trends.

## ✨ Features

- **OCR Extraction**: Automatically extract Company, Date, and Total from PDF/Image invoices.
- **AI Categorization**: Expenses are automatically categorized (Transport, Food, Supplies, Software) using a Scikit-Learn model.
- **Interactive Dashboard**: View spending insights with Pie and Bar charts.
- **AI Chatbot**: Query your expenses using natural language (e.g., "How much did I spend on food?").
- **Modern UI**: Sleek, glassmorphism-inspired dark mode interface built with React & Vite.

---

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Axios, Chart.js, Lucide React, Framer Motion.
- **Backend**: Flask (Python), MongoDB (PyMongo).
- **AI/ML**: Scikit-Learn (Categorization), Pytesseract (OCR), OpenCV.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.8+**
- **Node.js 18+**
- **MongoDB** (running locally or a connection string)
- **Tesseract OCR** (Optional but recommended for real OCR)
  ```bash
  sudo apt install tesseract-ocr
  ```

### 2. Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Create a `.env` file for your OpenAI API key or custom MongoDB URI:
   ```env
   MONGO_URI=mongodb://localhost:27017/
   OPENAI_API_KEY=your_key_here
   ```
4. Run the server:
   ```bash
   python3 app.py
   ```
   *The API will be available at `http://localhost:5000`.*

### 3. Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *The app will be available at `http://localhost:5173`.*

---

## 💡 Demo Mode
If you don't have Tesseract installed, you can test the extraction by uploading files with these names (case-insensitive):
- `amazon.pdf` / `amazon.png`
- `uber.pdf` / `uber.png`
- `google.pdf` / `google.png`

The system will return pre-defined mock data to demonstrate the dashboard and categorization.

---

## 📝 License
Built by Peter with love and AntiGravity AI.
