# DRCode AI Resume Analyzer – Project Overview

This document provides a comprehensive breakdown of the technical work completed, the architecture of the application, and the entire technology stack used to build the DRCode AI Resume Analyzer.

---

## 🏗️ Architecture Summary

The project is built using a **service-oriented architecture**. It heavily decouples completely separate concerns—such as extracting text from PDFs, performing NLP data extraction, running semantic matching, interacting with Telegram users, and serving the frontend.

### 1. The Telegram Bot (`bot/`)
The primary user interface. We use `python-telegram-bot` to create a conversational flow (using a `ConversationHandler`). The bot guides the user through providing a Job Description (JD) and a Resume. Once both documents are received, it forwards them to the backend API via HTTP requests. 

### 2. The FastAPI Backend (`app/`)
The core processing engine of the application. The FastAPI backend exposes endpoints (e.g., `/analyze`) that orchestrate the internal services to process files, score them, and generate improved variations. It also serves the frontend statics.

### 3. The Services Layer (`app/services/`)
This is where the heavy lifting happens. We built a series of isolated modules:
- **`file_parser.py`**: Extracts raw text from uploaded `.pdf` and `.docx` files.
- **`nlp_processor.py`**: Uses spaCy to analyze text, tokenizes sentences, and extracts hard skills, tools, and experience snippets utilizing entity recognition and custom heuristics.
- **`matcher.py`**: Compares the resume against the JD using **Sentence-BERT (SBERT)** for semantic similarity and deep keyword overlap extraction.
- **`scorer.py`**: Calculates an objective `x/10` score. It uses a weighted formula based on Skill Match (40%), Experience Relevance (20%), Keyword Match (20%), and Semantic Similarity (20%).
- **`recommender.py`**: Finds missing skills and generates actionable ATS (Applicant Tracking System) layout tips.
- **`improver.py`**: Integrates with the **OpenAI GPT API** (or falls back to a mock improver if no API key is provided) to rewrite the resume text, injecting missing keywords intelligently, and strengthening the impact of existing bullet points using metrics.
- **`resume_gen.py`**: Re-generates the newly improved text back into actual downloadable PDF and DOCX file formats.

### 4. The Web Frontend (`web/`)
A premium, mobile-first overview website that serves as a landing page for users wanting an introduction to the product. 

---

## 🛠️ Complete Technology Stack

### Backend Web Server
- **FastAPI**: The high-performance asynchronous web framework used for the main API.
- **Uvicorn**: ASGI web server implementation used to run FastAPI.
- **Pydantic**: Provides data validation and serialization (used for all request/response schemas).
- **HTTPX**: Used for async HTTP requests between the Telegram bot and the backend API.

### Bot Engine
- **python-telegram-bot (v20+)**: Async wrapper for the Telegram Bot API. Handles users, inline keyboards, message processing, and document downloads.

### AI / Natural Language Processing
- **spaCy (`en_core_web_sm`)**: A powerful NLP library used for Named Entity Recognition (NER), tokenization, and linguistic analysis to detect skills and calculate experience durations.
- **Sentence-Transformers (Sentence-BERT)**: Powered by HuggingFace implementations (using the lightweight `all-MiniLM-L6-v2` model). We use this to understand the *meaning* of sentences, rather than just doing naive keyword matching between the JD and the Resume.
- **OpenAI GPT API**: The generative AI used to rewrite and improve the resume. (Includes a rule-based fallback).

### File Parsing and Generation
- **PyMuPDF (`fitz`)**: For extremely fast and accurate text extraction from uploaded PDFs.
- **python-docx**: Used for reading text from `.docx` files and generating/formatting the final improved resume exports.
- **ReportLab**: Used for rendering raw text into a newly generated `.pdf` document for final download.

### Frontend Web UI
- **Vanilla HTML5 & CSS3**: Custom CSS using CSS Custom Properties (Variables) to create a dark mode, premium "Glassmorphism" aesthetic with vibrant gradients.
- **Vanilla JavaScript**: Used strictly for interactions, responsive navigation, IntersectionObserver scroll animations, and the particle network background on the `canvas` element.

### Utilities
- **python-dotenv**: To load and manage secure secrets (API Keys, Bot Tokens).
- **logging**: Native Python asynchronous logging built into helper modules across the stack to track operations.

---

## 🚀 Key Features Built From Scratch
1. **Semantic Matching Engine**: Bypasses traditional ATS systems that look for exact keyword matches by understanding the spatial meaning of words (e.g. knowing that "UI/UX" and "Interface Design" are highly related).
2. **Auto-Improver**: Using generative AI, the system actually rewrites the CV for the user and spits the document back out so they don't have to manually copy-paste tips.
3. **Lazy-Loading ML Models**: The heavy ML models (`spaCy` and `Sentence-BERT`) are only loaded into memory when first requested by the routes, saving startup speed and RAM capacity.
4. **Resilient Fallbacks**: If OpenAI is rate-limited or the API key runs out, the code natively falls back to a rule-based mock improver without throwing hard errors to the user.
