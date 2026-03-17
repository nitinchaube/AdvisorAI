<div align="center">

# AdvisorAI


### Intelligent Academic Advising Chatbot for Stevens Institute of Technology

**Multi-Agent RAG Pipeline · Fine-Tuned LLaMA-2-7B · LangGraph Orchestration**

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange)](https://www.trychroma.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Firebase](https://img.shields.io/badge/Firebase-Auth_%26_Hosting-FFCA28?logo=firebase&logoColor=black)](https://firebase.google.com)
[![Docker](https://img.shields.io/badge/Docker-Cloud_Run-2496ED?logo=docker&logoColor=white)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Live Demo](https://advisoraii.web.app) · [Research Paper](/AdvisorAI_Research_Paper.pdf) · [Fine-Tuning & Dataset](https://github.com/nitinchaube/StevensDomainFineTunedLM) . [HuggingFace] (https://huggingface.co/datasets/chauben/stevens-qa-finetuning-87k)

</div>

---

## Authors

| Name | Github |
|---|---|
| **Nitin Chaube** | https://github.com/nitinchaube |
| **Paras Jadhav** | https://github.com/parasjadhav2610 |
| **Keval Sompura** | https://github.com/keval-som |

## Overview

AdvisorAI is a production-grade academic advising chatbot that answers questions about courses, professors, programs, admissions, and campus life at **Stevens Institute of Technology** — with zero hallucination.

Unlike a simple ChatGPT wrapper, AdvisorAI uses a **multi-agent RAG (Retrieval-Augmented Generation) pipeline** orchestrated by LangGraph, with entity-aware hybrid retrieval, self-reflection quality gates, and real-time SSE streaming. In parallel, we have fine-tuned **LLaMA-2-7B** using QLoRA on **87,000+ Q&A pairs** for future self-hosted generation.

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-Agent RAG** | LangGraph orchestrator coordinates ChromaDB retrieval, web search, and conversation history agents in parallel |
| **Entity-Aware Hybrid Retrieval** | Regex-based course code & faculty name detection routes to targeted ChromaDB collections in sub-millisecond time |
| **Self-Reflection Quality Gate** | LLM critiques its own answers (1-10 score); refines if quality < 7/10 |
| **Real-Time Streaming** | SSE token-by-token streaming with source citations (Perplexity-style) |
| **Fine-Tuned LLaMA-2-7B** | QLoRA fine-tuning on 87K domain-specific Q&A pairs for future self-hosted generation |
| **Multi-Provider LLM** | Gemini 2.0 Flash (primary) + GPT-4o-mini (fallback) with automatic failover |
| **Multi-Layer Safety** | Regex blocking + LLM classification + identity protection + tech stack shielding |
| **Admin Dashboard** | Manage courses, faculty, users, web scraper, jobs/internships |
| **Resume Processing** | AI-powered resume parsing for personalized academic advising |
| **Jobs & Internships** | Automated scraping and search for career opportunities |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│          Presentation Layer (React 19 + Vite 5)      │
│   ChatInterface · Sessions · Admin Dashboard · Auth  │
└────────────────────────┬─────────────────────────────┘
                         │ HTTPS / SSE Streaming
                         ▼
┌──────────────────────────────────────────────────────┐
│             API Layer (FastAPI )               │
│   /api/chat/stream (SSE) · /api/chat/query · REST    │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│    Intelligence Layer (LangGraph Orchestrator)        │
│                                                      │
│    Router → Gather → Evaluate → Generate →           │
│    Reflect → [Refine if <7] → Save                   │
│       │        │                                     │
│    Safety   ChromaAgent · WebAgent · HistoryAgent     │
│                │                                     │
│            HybridRetriever                           │
│            ├─ Entity Detection (sub-ms)              │
│            └─ Semantic Search (BGE embeddings)       │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│                    Data Layer                         │
│  ChromaDB · MongoDB Atlas · Web Scraper · LLM APIs   │
└──────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 5, Tailwind CSS, Framer Motion |
| Authentication | Firebase Auth (email/password + verification) |
| Backend (Async) | FastAPI + Uvicorn |
| Database | MongoDB Atlas |
| Vector Database | ChromaDB 0.5.23 |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| LLM (Primary) | Google Gemini 2.0 Flash |
| LLM (Fallback) | OpenAI GPT-4o-mini, Claude 3.5 Haiku |
| Orchestration | LangGraph (StateGraph) |
| Fine-Tuning | QLoRA on LLaMA-2-7B |
| Deployment | Docker, Google Cloud Run, Firebase Hosting |
| Web Search | DuckDuckGo, SerpAPI |

---

## How It Works

When a user sends a message, it flows through a **7-node LangGraph pipeline**:

1. **Router** — Classifies the query as `general`, `domain`, or `blocked`. Runs regex safety checks (violence, profanity, tech probing) and LLM classification. Generates a chat session name.

2. **Gather** — For domain queries, runs three agents **in parallel** using `asyncio.gather()`:
   - **ChromaAgent**: Entity-aware hybrid retrieval — detects course codes (80+ Stevens prefixes) and faculty names via regex, routes to targeted ChromaDB collections with metadata filters. Falls back to multi-collection semantic search using BAAI/bge-small-en-v1.5.
   - **WebAgent**: Searches DuckDuckGo/SerpAPI, scrapes top results, cleans content.
   - **HistoryAgent**: Retrieves recent conversation context from memory.

3. **Evaluate** — ReAct "think" step: assesses whether gathered info is sufficient.

4. **Generate** — Synthesizes the answer from all context (history + ChromaDB docs + web results) using Gemini 2.0 Flash, with strict identity rules and source grounding.

5. **Reflect** — Self-critique scoring (1-10) on relevance, accuracy, completeness, tone, and tech leakage. If score < 7, triggers refinement.

6. **Refine** (conditional) — Improves the answer using reflection feedback.

7. **Save** — Persists to in-memory store and MongoDB.

Responses are streamed **token-by-token via SSE** with source citations displayed at the end.

---

## Fine-Tuning (Parallel Research)

We fine-tuned **Meta's LLaMA-2-7B** using QLoRA for future self-hosted generation. The complete fine-tuning pipeline, dataset, and model checkpoints are available in a dedicated repository:

**[github.com/nitinchaube/StevensDomainFineTunedLM](https://github.com/nitinchaube/StevensDomainFineTunedLM)**

| Parameter | Value |
|---|---|
| Dataset | 87,782 Q&A pairs scraped from Stevens website |
| Method | QLoRA (4-bit NF4 quantization) |
| LoRA Rank / Alpha | 16 / 32 |
| Target Modules | All 7 linear layers (q, k, v, o, gate, up, down) |
| Training | 6 epochs, lr=2e-4, cosine scheduler, effective batch size 32 |
| Infrastructure | Google Colab GPU |
| Best Checkpoint | Step 7,500 |

The fine-tuning repository includes:
- **Data collection pipeline** — async web crawler for Stevens website (`crawler.py`)
- **Data cleaning & preprocessing** — JSONL cleaning and validation (`clean_jsonl.py`)
- **Q&A generation** — context-to-QA pair generation (`DataGeneration/`)
- **QLoRA training notebook** — complete fine-tuning pipeline (`FinetuningProcess/Fine_tuning.ipynb`)
- **Model inference** — loading and running the fine-tuned model
- **Sample dataset** — `stevens_qa_finetuning_sample.jsonl` for reference

The fine-tuned model is designed for drop-in replacement via the `LLMRouter`'s provider abstraction in the production system.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB Atlas account
- Firebase project
- API keys: Google Gemini, OpenAI (optional), Anthropic (optional)

### Backend Setup

```bash
cd AdvisorAI-Web/backend
pip install -r requirements.txt

# Create .env file with required variables:
# MONGO_URI=your_mongodb_uri
# GEMINI_API_KEY=your_gemini_key
# OPENAI_API_KEY=your_openai_key  (optional)
# VECTORDB_DIR=./VectorDB_v2
# EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Frontend Setup

```bash
cd AdvisorAI-Web/frontend
npm install
npm run dev
```

### Docker Deployment

```bash
cd AdvisorAI-Web/backend
docker build -t advisorai .
docker run -p 8080:8080 --env-file .env advisorai
```

---

## Project Structure

```
AdvisorAI/
├── README.md
├── AdvisorAI-Web/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/          # ChatInterface, AdminDashboard, etc.
│   │   │   ├── contexts/            # AuthContext
│   │   │   ├── services/            # API service layer
│   │   │   └── config/              # Firebase config
│   │   └── package.json
│   ├── backend/
│   │   ├── main.py                  # FastAPI entry, SSE chat endpoints
│   │   ├── app.py                   # Flask app, ~50 REST routes
│   │   ├── chatbot_integration.py   # Bridge between API and LangGraph
│   │   ├── chatbot/
│   │   │   ├── core/
│   │   │   │   ├── langgraph_graph.py   # ReAct + Reflection pipeline
│   │   │   │   ├── llm_router.py        # Multi-provider LLM abstraction
│   │   │   │   └── memory_store.py      # Conversation memory
│   │   │   ├── agents/              # Chroma, Web, History, General agents
│   │   │   ├── tools/               # ChromaTool, WebTool, GeneralTool
│   │   │   └── config/settings.py   # Centralized configuration
│   │   ├── newprocessingdata/
│   │   │   ├── hybrid_retriever.py  # Entity-aware hybrid retrieval
│   │   │   └── build_vectordb.py    # ChromaDB indexing pipeline
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── data/
│   │   ├── stevens_qa_finetuning.jsonl  # 87K Q&A dataset
│   │   └── Fine_tuning.ipynb            # QLoRA training notebook
│   ├── AdvisorAI_Research_Paper.tex     # LaTeX research paper
│   └── AdvisorAI_Research_Paper.md      # Markdown research paper
```

---

## Research Paper

We have written a detailed research paper documenting the architecture, fine-tuning methodology, hybrid retrieval design, and evaluation:

**"AdvisorAI: A Retrieval-Augmented Generation System with Fine-Tuned LLaMA for Domain-Specific Academic Advising"**

> [LaTeX Source](AdvisorAI-Web/AdvisorAI_Research_Paper.tex) · [Markdown Version](AdvisorAI-Web/AdvisorAI_Research_Paper.md)

---

## Related Repositories

| Repository | Description |
|---|---|
| [AdvisorAI](https://github.com/nitinchaube/AdvisorAI) (this repo) | Production chatbot — RAG pipeline, multi-agent orchestration, full-stack web app |
| [StevensDomainFineTunedLM](https://github.com/nitinchaube/StevensDomainFineTunedLM) | Fine-tuning pipeline — web scraping, data generation, QLoRA training on LLaMA-2-7B |

---



*Stevens Institute of Technology, Hoboken, NJ*

---



<div align="center">

**Built at Stevens Institute of Technology**



</div>
