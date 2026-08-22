# SocialCommerce Comment Intelligence Platform

A hybrid rule-based + AI multilingual comment interpretation system for social media sellers in Sri Lanka.

## Overview

This is the research prototype developed as part of an undergraduate research project at NSBM Green University. The system assists social media sellers in Sri Lanka to interpret and prioritize customer interactions that occur through product-related comments on Facebook.

Customer comments are written in Sinhala, Singlish, English, or mixed language forms. The system fetches comments from a seller's Facebook posts via the Graph API, classifies each one into one of 14 intent categories using an evidence-based hybrid rule engine with an AI fallback layer, and presents sellers with a prioritized, browsable dashboard organized by category — including the ability to reply directly to comments from within the tool.

## Research Context

**Title:** Designing and Evaluating a Rule-Based Multilingual Comment Interpretation System for Social Media Sellers in Sri Lanka

**Author:** Sahan Yasas Maitipe

**Institution:** NSBM Green University, Sri Lanka

**Type:** Undergraduate Research Project — Prototype System

## Key Features

- **Multilingual Comment Classification** — Detects English, Sinhala, Singlish, mixed-language, and emoji-only comments using script-range detection and a curated Singlish lexicon.
- **14-Category Intent Detection**, including:
  - Purchase Intent
  - Product Inquiry
  - Price Inquiry / Price Complaint
  - Delivery Inquiry
  - Payment Method Inquiry
  - Warranty/Service Inquiry
  - Order/Purchase Confirmation
  - Location/Availability
  - Positive Feedback
  - Negative Feedback/Complaint
  - Suggestion
  - Contact Request
  - Noise/Off-topic
- **Evidence-Based Hybrid Classification Engine** — A rule-based layer scores each comment against a weighted keyword matrix. Routing confidence (`rules_only`, `rules_ai_verify`, `ai_only`) is determined by how many annotated corpus examples exist for that (category, language) combination — not by a fixed heuristic. Categories with insufficient annotated evidence are explicitly deferred to the AI layer rather than guessed at.
- **AI Fallback Layer** - Google Gemini API classifies comments the rule layer cannot confidently resolve, using the same 14-category taxonomy.
- **Linguistic Guards** - Dedicated logic for negation (e.g. "not the best," "wada na"), question-form detection (e.g. "hodaida?" routes to Product Inquiry, not praise), and order-confirmation context (e.g. "gaththa eka wada na" routes to AI rather than being force-classified as a confirmation).
- **Live Facebook Graph API Integration** - Fetches comments from a connected Facebook Page, posts replies (single or bulk), and can programmatically hide comments containing customer-submitted personal details (e.g. delivery address) to protect privacy.
- **Incremental Sync Pipeline** - Re-syncing a tracked post only processes genuinely new comments, using Facebook comment IDs for deduplication.
- **Seller Dashboard** - Category-grid overview per post with comment-activity trend chart and language-distribution breakdown, drilling into a per-category comment browser with unread/replied status tracking and bulk reply.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Create React App) |
| Backend | Python / FastAPI |
| Classification Engine | Python (rule-based + Google Gemini AI fallback) |
| Database | SQLite (WAL mode) |
| Social Platform Integration | Facebook Graph API |

## Project Structure
```bash
frontend/                           # React frontend application
├── src/
│   ├── components/                 # Sidebar, TopBar, charts, cards, bulk reply bar, etc.
│   ├── pages/                      # Home, PostAnalysis, CategoryComments, etc.
│   ├── config/                     # Intent taxonomy config, current-user placeholder
│   └── services/
│       └── api.js                  # Backend API client
└── package.json

backend/                            # FastAPI backend
├── app/
│   ├── main.py                     # API entry point
│   ├── database.py                 # SQLite schema + queries
│   ├── models.py                   # Pydantic request/response models
│   ├── rules/
│   │   ├── classifier.py           # Evidence-based hybrid rule engine
│   │   ├── routing_guards.py       # AI-only risk detection guards
│   │   └── ai_fallback.py          # Gemini API integration
│   ├── routers/
│   │   └── posts.py                # Post/comment/reply API routes
│   └── graph/
│       ├── fb_graph_fetcher.py     # Facebook Graph API client
│       └── pipeline.py             # Fetch → classify → save orchestration
└── requirements.txt

dataset/                            # Annotated research corpus
LICENSE
README.md
```
## Getting Started

### Prerequisites

- Node.js v18+
- Python 3.10+
- pip
- A Facebook Page access token with `pages_read_engagement` and `pages_manage_engagement` permissions
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/symaitipe/SocialCommerceResearch.git
cd SocialCommerceResearch
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with:
FB_ACCESS_TOKEN=your_facebook_page_access_token
FB_API_VERSION=v25.0
GEMINI_API_KEY=your_gemini_api_key


```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` (interactive docs at `http://localhost:8000/docs`).

### 3. Set up the frontend

```bash
cd frontend
npm install
npm start
```

The app will be available at `http://localhost:3000`.

## Dataset

The rule engine's evidence matrix is derived from **588 manually annotated comments**, collected from Sri Lankan Facebook social commerce pages:

- **Corpus A:** 536 comments across 5 product verticals, collected sequentially
- **Corpus B:** 52 targeted negative/complaint examples, collected to strengthen coverage of that category

Each comment is labeled with:

- **Language Type** - English / Sinhala / Singlish / Mixed / Emoji
- **Intent Category** - one of 14 categories (see Key Features)
- **Annotation Notes** - rationale for the labeling decision where relevant

All comments processed by the live system are sourced from a seller's own public Facebook posts, accessed via an authorized Page access token.

## Scope Notes
- The system integrates with a live Facebook Page via the official Graph API for the connected test account(s) used during development and evaluation. It does not scrape Facebook or use browser automation.
- Customer-submitted personal details (e.g. delivery address, phone number) shared in reply to an order-confirmation prompt are automatically hidden from public view on Facebook and stored only in the system's private database.

## License

Copyright (c) 2025 Sahan Yasas Maitipe - NSBM Green University

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

Supervised by Department of Computing, NSBM Green University, Sri Lanka.
