# SocialCommerce Comment Intelligence Platform

> A rule-based multilingual comment interpretation system for social media sellers in Sri Lanka.

---

## Overview

This is the research prototype developed as part of an undergraduate research project at **NSBM Green University**. The system assists social media sellers in Sri Lanka to interpret and understand customer interactions that occur through product-related comments on social media platforms.

Customer comments are written in **Sinhala**, **Singlish**, **English**, or mixed language forms. This platform processes those comments using a rule-based classification engine and provides structured interaction insights to sellers through a dashboard interface.

---

## Research Context

**Title:** Designing and Evaluating a Rule-Based Multilingual Comment Interpretation System for Social Media Sellers in Sri Lanka

**Author:** Sahan Yasas

**Institution:** NSBM Green University, Sri Lanka

**Type:** Undergraduate Research Project — Prototype System

---

## Key Features

- **Multilingual Comment Classification** — Handles Sinhala, Singlish, English, and mixed-language comments
- **Intent Detection** — Identifies comment types including:
  - Product Inquiries
  - Purchase Intent
  - Delivery Inquiries
  - Price Inquiries
  - Warranty Inquiries
  - Positive / Negative Feedback
  - Order Confirmations
  - Location / Availability Requests
- **Sentiment Analysis** — Positive, Negative, Neutral, Mixed
- **Seller Dashboard** — Summarised interaction insights per product post
- **Simulated Social Commerce Environment** — Product post and comment interface for evaluation purposes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Backend | Python / FastAPI |
| Classifier Engine | Python (Rule-based) |
| Database | SQLite |

---

## Project Structure

```
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page views (Product Post, Seller Dashboard)
│   │   └── App.jsx
│   └── package.json
│
├── backend/                # FastAPI backend
│   ├── main.py             # API entry point
│   ├── classifier/         # Rule-based classification engine
│   │   ├── intent.py       # Intent detection rules
│   │   ├── sentiment.py    # Sentiment rules
│   │   └── language.py     # Language detection
│   ├── models/             # Database models
│   ├── routes/             # API route handlers
│   └── requirements.txt
│
├── dataset/                # Annotated research datasets
│   ├── clothing/           # Clothing category comments
│   └── electronics/        # Electronics category comments
│
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js v18+
- Python 3.10+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/sahanyasas/social-commerce-comment-intelligence.git
cd social-commerce-comment-intelligence
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

---

## Dataset

The annotated datasets used in this research are located in the `/dataset` directory. Comments were manually collected from Sri Lankan social media selling pages across the following product categories:

| Category | Comments | Language Mix |
|---|---|---|
| Clothing (Moose) | 100 | English, Singlish |
| Electronics (Lenovo Headset) | 100 | Sinhala, Singlish, English |

All comments have been **anonymized** — personal names, phone numbers, and addresses have been removed or replaced prior to inclusion in this repository.

Each comment is labeled with:
- **Language Type** — English / Sinhala / Singlish
- **Intent Category** — 9 categories
- **Sentiment** — Positive / Negative / Neutral / Mixed
- **Annotation Notes** — Explanation of labeling decision

---

## Disclaimer

This system is a **research prototype** developed for academic evaluation purposes only. It does not integrate with any live social media platform, process real user data, or facilitate actual commercial transactions.

---

## License

Copyright (c) 2025 Sahan Yasas — NSBM Green University

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

Supervised by the Department of Computing, NSBM Green University, Sri Lanka.
