# 🎬 CinematIX – AI-Powered Movie Recommendation System

> A decoupled, production-grade, and secure-by-default AI movie recommendation portal built with **Next.js**, **FastAPI**, **PostgreSQL**, and **PyTorch**.
> 
> Leverages a **Neural Collaborative Filtering (NCF)** network with custom user & movie embedding layers trained on the MovieLens dataset.

---

## 🤖 Built in Partnership with Agentic AI

This application stands as a testament to the future of software development: a complete architectural migration from a monolithic Flask+SQLite script prototype to a fully decoupled, production-hardened modern web stack (**Next.js App Router + FastAPI + SQLModel + PostgreSQL**), completed in **less than an hour** through the power of **Agentic AI Pair-Programming (Google DeepMind's Antigravity)**.

### ⚡ The AI Productivity Multiplier: 10x to 100x

By utilizing advanced agentic coding systems, a development lifecycle that normally takes days of design, database modeling, schema scripting, and security auditing was compressed into minutes:

* **Instant Architecture Redesign:** Boilerplate generation for SQLModel schemas, Pydantic type validation models, FastAPI lifespan migrations, and JWT cookie cryptographical signing was completed in seconds.
* **Proactive Defect Mitigation:** The AI successfully executed dry-run builds on Next.js, catching a production-breaking compilation bug (`useSearchParams() React Suspense boundary bailout`) and refactoring the component *before* triggering a failed deployment in Vercel CI/CD.
* **Flawless Bug Resolution:** Resolved runtime PyTorch state dict shape mismatches and Windows console `UnicodeEncodeError` logs seamlessly, converting raw log statements to robust ASCII formats.
* **Security-First Focus:** Hardened critical credentials, secured API keys through backend proxy patterns, enforced HttpOnly cookies, and injected security parameters natively.

---

## 🚀 Key Features

| Feature | Technical Details |
| :--- | :--- |
| **🤖 AI NCF Engine** | Neural Collaborative Filtering model utilizing user + movie embeddings inside PyTorch. |
| **🎯 confidence Scores** | Displays a real-time `0-100%` model-evaluated match rating for each recommended item. |
| **🎨 Netflix-Dark UI** | A premium, glassmorphic dark interface styled with custom **Vanilla CSS** animations and Outfit typography. |
| **🔍 Debounced AJAX Search** | High-performance search in the navigation bar with debounced, live AJAX suggestions. |
| **🔒 Hardened Sessions** | Cryptographically signed JWT tokens stored strictly in **HttpOnly, SameSite=Strict cookies**. |
| **🛡️ Secure Poster Proxy** | Streams poster assets from TMDB via a secure backend proxy, completely shielding external API keys. |
| **⏳ Prediction History** | Keeps a secure persistent log of recommendation sessions to audit model precision. |
| **⚙️ Admin Control Panel** | Displays real-time database stats, triggers async PyTorch retraining, and draws live SVG learning curves. |

---

## 🏗️ Architecture

```
                       ┌─────────────────────────┐
                       │   Next.js Web Client    │ (HTML5 / React / Vanilla CSS)
                       │  http://localhost:3000  │
                       └───────────┬─────────────┘
                                   │
                     Secure HTTPS / HttpOnly Cookie
                                   │
                       ┌───────────▼─────────────┐
                       │  FastAPI Backend API    │ (Pydantic / slowapi / CORS)
                       │  http://localhost:8000  │
                       └───────────┬─────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
     ┌────────▼────────┐                       ┌────────▼────────┐
     │   PostgreSQL    │                       │  PyTorch Model  │
     │   (SQLModel)    │                       │  (NCF Weights)  │
     └─────────────────┘                       └─────────────────┘
```

---

## 📁 Project Structure

```
movie_recommender/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # Lifespan startup, seeds, CORS policies, & error handlers
│   │   ├── config.py         # Secure Pydantic configuration validation
│   │   ├── database.py       # SQLModel database engine connection pool
│   │   ├── models.py         # PostgreSQL schemas & validation shapes
│   │   ├── auth.py           # Bcrypt password hashing & JWT cookie validation dependencies
│   │   ├── routes/           # REST Router endpoints
│   │   │   ├── auth.py       # Secure login, registration, and logout
│   │   │   ├── movies.py     # Ratings, bookmarks watchlist, recommendations, & poster proxy
│   │   │   └── admin.py      # Background retraining trigger, stats, & history curves
│   │   └── services/         # PyTorch AI Services
│   │       ├── recommender.py# Model checkpoint loader & top-n collaborative inference
│   │       ├── preprocessing.py # Contiguous label encoder mapping
│   │       └── train_job.py  # Model fit training loop with callbacks & matplotlib charts
│   └── requirements.txt
│
├── frontend/                 # Next.js Frontend Client (App Router)
│   ├── src/
│   │   ├── app/              # Client-side views & page routes
│   │   │   ├── context/      # AuthContext session provider
│   │   │   ├── components/   # Navbar with debounced AJAX search, MovieCard with rating controls
│   │   │   ├── globals.css   # Premium dark glassmorphic variables, glows, and animations
│   │   │   ├── layout.js     # Base global shell framework
│   │   │   ├── page.js       # Home Landing view with trending sections
│   │   │   ├── recommendations/ # Live feed page with active genre sidebar menus
│   │   │   ├── bookmarks/    # Userwatchlist with interactive removal triggers
│   │   │   ├── history/      # Audit log of generated recommendations and confidence metrics
│   │   │   ├── search/       # Search results page wrapped in React Suspense boundary
│   │   │   └── dashboard/    # Control panel with live training progress and SVG learning curves
│   │   └── vercel.json       # Production-grade HSTS, CORS, Clickjacking, and CSP headers
│   └── package.json
│
└── .gitignore                # Root-level ignore (blocks .env leaks and venv repository bloat)
```

---

## ⚙️ Quick Start Setup

### 1. Configure the Backend
Navigate to the `backend/` directory:
```bash
# Activate your virtual environment
cd backend
..\venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --port 8000 --host 127.0.0.1 --reload
```
* The database schemas will automatically migrate, and a secure master admin account is automatically seeded:
  * **Admin Email:** `bikikalita1000@gmail.com`
  * **Admin Password:** `Mistbigg4010`

### 2. Configure the Frontend
Navigate to the `frontend/` directory:
```bash
cd ../frontend

# Start the Next.js Dev Server (runs under blazing-fast Turbopack compiler)
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser and experience **CinematIX**!
