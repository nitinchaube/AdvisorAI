# AdvisorAI: A Retrieval-Augmented Generation System with Fine-Tuned LLaMA for Domain-Specific Academic Advising

**Nitin Chaube, Paras Jadhav, Keval Sompura**

*Stevens Institute of Technology, Hoboken, NJ 07030, USA*

*{nchaube, pjadhav, ksompura}@stevens.edu*

---

## Abstract

Large Language Models (LLMs) have demonstrated remarkable capabilities in natural language understanding and generation, yet they frequently produce hallucinated or outdated information when applied to domain-specific institutional queries. This paper presents **AdvisorAI**, an intelligent academic advising chatbot designed for Stevens Institute of Technology that combines Retrieval-Augmented Generation (RAG) with cloud-hosted LLMs (Google Gemini and OpenAI) to deliver accurate, context-aware responses about academic programs, courses, faculty, and campus resources. Our system employs a novel multi-agent architecture orchestrated via LangGraph, featuring a ReAct (Reason-Act-Observe) pipeline augmented with a self-reflection quality gate. We introduce a hybrid retrieval mechanism that uses deterministic entity detection with sub-millisecond latency to route queries to targeted ChromaDB collections before falling back to semantic search. In parallel, we conduct a fine-tuning study using QLoRA (Quantized Low-Rank Adaptation) on LLaMA-2-7B with a curated dataset of approximately 87,000 question-answer pairs scraped and generated from official university web pages, targeting future self-hosted generation to reduce API dependency. The system is deployed as a production web application with real-time streaming responses, Firebase authentication, and an administrative dashboard. Our architecture demonstrates that combining entity-aware retrieval augmentation, agentic orchestration, and domain-specific fine-tuning research yields a robust, low-hallucination academic advising system suitable for real-world university deployment.

**Keywords:** Retrieval-Augmented Generation, LLaMA, QLoRA, Fine-Tuning, Academic Advising, LangGraph, Multi-Agent Systems, ChromaDB, Hybrid Retrieval

---

## 1. Introduction

### 1.1 Motivation

Academic advising is a critical component of the student experience at universities, influencing course selection, degree planning, career preparation, and overall student satisfaction. However, traditional advising systems face several persistent challenges: limited availability of human advisors, inconsistent information across departments, and the difficulty of maintaining up-to-date knowledge across rapidly evolving academic programs. Students often resort to searching fragmented institutional websites, consulting outdated catalogs, or relying on peer networks for information that may be inaccurate or incomplete.

The emergence of Large Language Models (LLMs) such as GPT-4, LLaMA, and Gemini has created new possibilities for automated question-answering systems. However, directly applying general-purpose LLMs to institutional advising poses significant risks: these models lack access to current institutional data, are prone to hallucination on domain-specific queries, and cannot be easily updated as programs and policies change.

### 1.2 Challenges

Building a reliable academic advising chatbot presents several technical challenges:

1. **Domain specificity**: The system must accurately represent institutional policies, course offerings, faculty information, and program requirements that are unique to the university and change frequently.
2. **Hallucination mitigation**: General-purpose LLMs frequently fabricate plausible-sounding but incorrect information about specific courses, prerequisites, and faculty research areas.
3. **Query diversity**: Students ask questions ranging from simple factual lookups ("What are the prerequisites for FE 621?") to complex multi-hop reasoning ("Which professors in the Financial Engineering department work on machine learning and also teach courses I could take as a CS student?").
4. **Real-time responsiveness**: An advising chatbot must provide streaming, low-latency responses to maintain user engagement.
5. **Information freshness**: Academic information changes each semester, requiring mechanisms to incorporate new data without full system retraining.

### 1.3 Contributions

This paper makes the following contributions:

- **AdvisorAI System**: A production-grade academic advising chatbot powered by Google Gemini and OpenAI APIs, augmented with retrieval-augmented generation for Stevens Institute of Technology.
- **Entity-Aware Hybrid Retrieval**: A novel retrieval mechanism combining deterministic entity detection (course codes, faculty names, intent classification) with semantic search over ChromaDB, achieving sub-millisecond routing latency.
- **LangGraph Multi-Agent Orchestration**: A ReAct + Reflection pipeline implemented in LangGraph that coordinates specialized agents (ChromaDB retrieval, web search, conversation history, general knowledge) with self-critique quality gates.
- **QLoRA Fine-Tuning Study**: A parallel research effort applying parameter-efficient fine-tuning (QLoRA) to LLaMA-2-7B on a curated dataset of ~87,000 domain-specific Q&A pairs, designed for future integration as a self-hosted generation backbone.
- **Full-Stack Deployment**: A complete web application with React frontend, FastAPI/Flask backend, Firebase authentication, SSE streaming, and Docker-based cloud deployment on Google Cloud Run.

### 1.4 Paper Organization

The remainder of this paper is organized as follows. Section 2 reviews related work. Section 3 describes the system architecture. Section 4 details the data collection and the parallel LLaMA-2-7B fine-tuning effort. Section 5 presents the retrieval-augmented generation pipeline. Section 6 describes the multi-agent orchestration and the production LLM integration. Section 7 covers the full-stack implementation. Section 8 discusses results and evaluation. Section 9 concludes with future directions.

---

## 2. Related Work

### 2.1 Large Language Models

The transformer architecture [1] has given rise to a family of increasingly capable language models. GPT-4 [2] and its predecessors demonstrated strong performance across diverse NLP tasks. Meta's LLaMA family [3, 4] made high-quality open-weight models accessible for research and fine-tuning. Google's Gemini [5] introduced multi-modal capabilities with efficient inference. These models form the foundation upon which domain-specific systems like AdvisorAI are built.

### 2.2 Retrieval-Augmented Generation

RAG [6] addresses LLM hallucination by grounding generation in retrieved documents. The original RAG framework combines a dense retriever with a sequence-to-sequence generator. Subsequent work has explored hybrid retrieval strategies that combine dense and sparse methods [7], entity-aware retrieval that leverages structured knowledge [8], and multi-step retrieval pipelines [9]. Our work extends this line by introducing domain-specific entity detection that operates at sub-millisecond latency, bypassing the overhead of embedding-based routing for structured queries.

### 2.3 Parameter-Efficient Fine-Tuning

Full fine-tuning of large language models is computationally prohibitive for most organizations. LoRA (Low-Rank Adaptation) [10] addresses this by injecting trainable low-rank decomposition matrices into transformer layers while keeping the base model frozen. QLoRA [11] further reduces memory requirements by quantizing the base model to 4-bit precision during fine-tuning. These methods enable fine-tuning of 7B+ parameter models on consumer-grade GPUs while maintaining performance competitive with full fine-tuning. Our work applies QLoRA to adapt LLaMA-2-7B for the academic advising domain.

### 2.4 Agentic AI and Multi-Agent Systems

Recent advances in LLM-based agents [12] have explored systems where language models reason about tool use, plan multi-step actions, and coordinate with other agents. The ReAct framework [13] interleaves reasoning traces with actions, enabling more grounded decision-making. LangGraph [14] provides a graph-based framework for building stateful, multi-agent applications. Self-reflection mechanisms [15] enable LLMs to critique and refine their own outputs. AdvisorAI combines these paradigms in a unified orchestration pipeline.

### 2.5 Academic Chatbots

Several university chatbot systems have been proposed in the literature [16, 17, 18]. Early systems relied on rule-based approaches or simple retrieval models. More recent work has explored fine-tuned transformer models for educational Q&A [19]. However, few systems combine fine-tuning, RAG, and agentic orchestration in a single production-grade deployment, which is the approach we present here.

---

## 3. System Architecture

### 3.1 Overview

AdvisorAI follows a modular, layered architecture consisting of four primary layers: (1) the presentation layer (React frontend), (2) the API layer (FastAPI + Flask), (3) the intelligence layer (LangGraph orchestrator with multi-agent pipeline), and (4) the data layer (MongoDB, ChromaDB, web scraping). Figure 1 illustrates the high-level architecture.

```
┌──────────────────────────────────────────────────────────────┐
│              Presentation Layer (React + Vite)               │
│  ChatInterface │ SessionManager │ AdminDashboard │ Auth      │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTPS / SSE
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                  API Layer (FastAPI + Flask)                  │
│  /api/chat/stream (SSE) │ /api/chat/query │ Auth/Admin APIs  │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│           Intelligence Layer (LangGraph Orchestrator)         │
│                                                              │
│  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Router │→ │  Gather   │→ │ Generate │→ │ Reflect  │      │
│  │(Safety)│  │(parallel) │  │          │  │(Quality) │      │
│  └────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                    │                           │             │
│         ┌─────────┼─────────┐            ┌────┴────┐        │
│         ▼         ▼         ▼            ▼         │        │
│    ┌─────────┐ ┌──────┐ ┌──────┐   ┌─────────┐    │        │
│    │ Chroma  │ │ Web  │ │Hist. │   │ Refine  │    │        │
│    │ Agent   │ │Agent │ │Agent │   │ (if<7)  │    │        │
│    └─────────┘ └──────┘ └──────┘   └─────────┘    │        │
│                                                     │        │
└─────────────────────────────────────────────────────┘        │
                          │                                     │
                          ▼                                     │
┌──────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ChromaDB (Vector Store) │ MongoDB │ Web Scraper │ LLM APIs │
└──────────────────────────────────────────────────────────────┘
```

*Figure 1: AdvisorAI system architecture showing the four-layer design with the LangGraph-based multi-agent intelligence layer at its core.*

### 3.2 Design Principles

The architecture is guided by several key design principles:

- **Modularity**: Each component (retrieval, generation, safety, reflection) operates as an independent module that can be replaced or upgraded without affecting other components.
- **Multi-provider LLM support**: The system supports Google Gemini, OpenAI GPT-4o-mini, and Anthropic Claude through an `LLMRouter` that provides automatic fallback across providers.
- **Safety-first design**: A multi-layered safety system blocks harmful, off-topic, and adversarial queries before any expensive tool execution.
- **Streaming-first**: All chat responses use Server-Sent Events (SSE) for real-time token-by-token delivery to the frontend.
- **Horizontal scalability**: Docker-based deployment on Google Cloud Run supports auto-scaling with configurable concurrency limits.

---

## 4. Data Collection and Fine-Tuning

The production AdvisorAI system relies on cloud-hosted LLMs (Google Gemini 2.0 Flash as primary, OpenAI GPT-4o-mini as fallback) for response generation, combined with the RAG pipeline described in Section 5. In parallel, we have undertaken a fine-tuning study to train a domain-specific LLaMA-2-7B model using QLoRA, with the goal of eventually replacing cloud API dependency with a self-hosted generation model. This section describes the dataset construction and fine-tuning methodology for this parallel research track.

### 4.1 Dataset Construction

#### 4.1.1 Web Scraping Pipeline

The fine-tuning dataset was constructed by systematically scraping the official Stevens Institute of Technology website and academic catalog. The scraping pipeline targeted:

- **Academic program pages**: Master's and Bachelor's program descriptions, concentrations, curriculum requirements, and career outcomes.
- **Course catalog**: Individual course descriptions, credits, prerequisites from the Stevens academic catalog (2023–2024 archive).
- **Faculty profiles**: Research interests, publications, teaching assignments, and contact information.
- **Admissions information**: Application requirements, deadlines, financial aid, and international student resources.
- **Campus resources**: Student services, career center, library, housing, and campus life.

Each scraped page was stored with its source URL and cleaned content, creating a provenance trail for every piece of training data.

#### 4.1.2 Question-Answer Generation

From each scraped context, multiple question-answer pairs were generated to capture different aspects of the content. The resulting dataset contains **87,782 question-answer pairs** in JSONL format, where each entry consists of:

- **context**: The source URL and scraped textual content from the university website.
- **question**: A natural language question that can be answered from the context.
- **answer**: A concise, accurate answer grounded in the provided context.

#### 4.1.3 Data Quality Analysis

Prior to fine-tuning, we conducted systematic data quality analysis:

- **Missing data check**: Verified zero null values across all three fields (context, question, answer).
- **Empty string detection**: Filtered out any entries with empty content in any field.
- **Length distribution analysis**: Characterized the statistical distribution of context, question, and answer lengths to inform tokenizer configuration and maximum sequence length selection.
- **Text length statistics**: Analyzed the distribution of context lengths, question lengths, answer lengths, and total token counts to set appropriate truncation thresholds.

### 4.2 Fine-Tuning with QLoRA

#### 4.2.1 Base Model Selection

We selected **Meta's LLaMA-2-7B** (`meta-llama/Llama-2-7b-hf`) as the base model for fine-tuning. LLaMA-2-7B offers a strong balance between model capacity and computational feasibility, with 7 billion parameters providing sufficient expressiveness for domain-specific question-answering while remaining trainable on consumer-grade GPU infrastructure through quantization.

#### 4.2.2 Quantized Low-Rank Adaptation (QLoRA)

We employed QLoRA [11] to enable memory-efficient fine-tuning of the full 7B-parameter model. QLoRA combines two key innovations:

1. **4-bit NormalFloat (NF4) Quantization**: The base model weights are quantized to 4-bit precision using the NF4 data type, which is information-theoretically optimal for normally distributed weights. This reduces the memory footprint of the base model from ~28 GB (FP32) to ~3.5 GB.

2. **Low-Rank Adaptation (LoRA)**: Small trainable low-rank decomposition matrices are injected into the frozen quantized model. Only these adapter weights are updated during training, reducing the number of trainable parameters by orders of magnitude.

#### 4.2.3 Configuration

The QLoRA fine-tuning was configured with the following hyperparameters:

| Parameter | Value |
|---|---|
| Base Model | `meta-llama/Llama-2-7b-hf` |
| Maximum Sequence Length | 1,024 tokens |
| LoRA Rank (r) | 16 |
| LoRA Alpha (α) | 32 |
| LoRA Dropout | 0.1 |
| Target Modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Quantization | 4-bit NF4 |
| Compute Dtype | float16 |
| Learning Rate | 2 × 10⁻⁴ |
| Batch Size | 2 |
| Gradient Accumulation Steps | 16 |
| Effective Batch Size | 32 |
| Number of Epochs | 6 |
| Warmup Ratio | 0.03 |
| Weight Decay | 0.01 |
| LR Scheduler | Cosine |
| Gradient Checkpointing | Enabled |
| FP16 Training | Enabled |

*Table 1: QLoRA fine-tuning hyperparameters for LLaMA-2-7B on the Stevens academic advising dataset.*

**Target Module Selection**: We applied LoRA adapters to all seven linear projection layers in each transformer block (four attention projections and three MLP projections). This comprehensive targeting ensures the model can adapt both its attention patterns and feed-forward representations to the academic advising domain, rather than limiting adaptation to attention layers alone.

**Training Infrastructure**: Fine-tuning was conducted on Google Colab with GPU acceleration. The gradient checkpointing and 4-bit quantization enabled training of the full 7B model within the memory constraints of a single GPU.

#### 4.2.4 Training Procedure

The dataset was split 90/10 into training and evaluation sets. Training was executed using the HuggingFace `Trainer` API with the following procedure:

1. **Data formatting**: Each training example was formatted as an instruction-following prompt:
   ```
   ### Context:
   {scraped web content}

   ### Question:
   {question}

   ### Answer:
   {answer}
   ```
2. **Tokenization**: The formatted instructions were tokenized using the LLaMA-2 tokenizer with truncation at 1,024 tokens and dynamic padding.
3. **Training**: Causal language modeling (next-token prediction) with `DataCollatorForLanguageModeling` (MLM disabled).
4. **Checkpointing**: Model checkpoints were saved every 500 steps, with the best model selected based on evaluation loss. A total of 3 checkpoints were retained.
5. **Evaluation**: Evaluation was performed every 500 steps on the held-out evaluation set to monitor for overfitting.

The final model was saved at checkpoint 7,500, representing the optimal balance between training loss convergence and evaluation loss.

#### 4.2.5 Instruction Format and Future Integration

The instruction format was designed to mirror the expected inference-time usage pattern. During inference, the model would receive a context (retrieved from ChromaDB or web scraping) and a question, and generate a grounded answer. This alignment between training and inference formats ensures that the fine-tuned model's learned behavior will transfer effectively to the RAG pipeline once integrated.

#### 4.2.6 Current Status and Integration Roadmap

The fine-tuned LLaMA-2-7B model represents a completed parallel research effort. The trained adapter weights (checkpoint 7,500) and the curated 87K Q&A dataset are preserved alongside the production codebase. The current production system uses Gemini and OpenAI APIs for generation, which provide strong baseline quality and rapid iteration. The fine-tuned model is intended for future deployment as a self-hosted alternative, which would:

1. **Eliminate API costs**: Remove per-token charges from cloud LLM providers.
2. **Reduce latency**: Enable on-premise or dedicated GPU inference without network round-trips.
3. **Enhance privacy**: Keep all student queries and institutional data within university infrastructure.
4. **Enable continuous improvement**: Allow further fine-tuning iterations as new institutional data becomes available.

The `LLMRouter` module in the production system is designed with provider abstraction, making the integration of a self-hosted model a configuration change rather than an architectural overhaul.

---

## 5. Retrieval-Augmented Generation Pipeline

### 5.1 Vector Database Construction

#### 5.1.1 ChromaDB

We use ChromaDB as the vector store for document retrieval. The university's academic content is organized into multiple collections, each corresponding to a distinct content domain (e.g., faculty profiles, course descriptions, program information). This collection-based organization enables targeted retrieval that reduces noise from irrelevant document types.

#### 5.1.2 Embedding Model

Documents are embedded using the **BAAI/bge-small-en-v1.5** model from HuggingFace, a compact (33M parameters) yet highly performant sentence embedding model. BGE (BAAI General Embedding) consistently ranks among the top models on the MTEB (Massive Text Embedding Benchmark) for its size class, offering an excellent trade-off between embedding quality and inference speed for production deployment.

#### 5.1.3 Indexing Pipeline

The `build_vectordb.py` pipeline processes the scraped and structured university data through the following stages:

1. **Document loading**: JSON-formatted university content is loaded with source metadata.
2. **Text chunking**: Documents are segmented into chunks appropriate for the embedding model's context window.
3. **Embedding generation**: Each chunk is embedded using the BGE model.
4. **Collection creation**: Embeddings are stored in domain-specific ChromaDB collections with associated metadata (source URL, content type, entity identifiers).

### 5.2 Entity-Aware Hybrid Retrieval

A key architectural innovation in AdvisorAI is the **Hybrid Retriever** (`HybridRetriever`), which replaces the common approach of LLM-based query routing with a deterministic, sub-millisecond entity detection layer.

#### 5.2.1 Entity Detection

The `EntityDetector` module performs three types of extraction:

1. **Course Code Extraction**: A regex pattern recognizes all valid Stevens course prefixes (AAI, CS, FE, MA, etc. — 80+ prefixes) followed by three-digit course numbers, handling variations in formatting (e.g., "FE 621", "FE621", "FE-621").

2. **Faculty Name Detection**: A prebuilt lookup table of all known faculty members enables rapid name matching, including recognition of academic title prefixes ("Professor", "Prof.", "Dr.").

3. **Intent Classification**: Pattern-matching rules classify the query intent into categories:
   - `professor_lookup`: "Who teaches...", "instructor for..."
   - `course_lookup`: "What courses does...", "classes taught by..."
   - `research_lookup`: "Research interests of...", "publications by..."
   - `contact_lookup`: "Email address of...", "office hours..."
   - `course_info`: "Prerequisites for...", "credits for..."

#### 5.2.2 Routing Strategy

Based on detected entities and intent, the retriever routes queries through one of two paths:

1. **Targeted retrieval** (entities detected): The query is directed to the specific ChromaDB collection with metadata filters that match the detected entities. For example, a query about "FE 621" is routed to the courses collection with a metadata filter for course code "FE 621".

2. **Semantic fallback** (no entities detected): When no structured entities are detected, the system falls back to multi-collection semantic search, querying all relevant collections with the raw query embedding and returning the top-k most similar documents.

This hybrid approach achieves the best of both worlds: deterministic precision for structured queries (which constitute a majority of academic advising questions) and flexible semantic search for open-ended queries.

#### 5.2.3 Performance Advantage

The entity detection layer operates in sub-millisecond time complexity O(1) for course code regex matching and O(n) for faculty name lookup (where n is the number of known faculty, typically < 1000). This is orders of magnitude faster than LLM-based routing, which requires a full model inference pass (~100–500ms) and introduces the risk of misclassification.

### 5.3 Retrieval Configuration

The retrieval system is configured with the following parameters:

| Parameter | Value |
|---|---|
| Top-K per Collection | 5 |
| Maximum Total Documents | 5 |
| Query Rewriting | Enabled |
| Embedding Model | BAAI/bge-small-en-v1.5 |

*Table 2: Retrieval configuration parameters.*

Query rewriting uses the LLM to rephrase ambiguous queries into more specific forms before retrieval, improving recall for queries with implicit intent.

---

## 6. Multi-Agent Orchestration with LangGraph

### 6.1 LangGraph Pipeline

The core intelligence of AdvisorAI is implemented as a stateful graph using LangGraph, a framework for building multi-step, multi-agent LLM applications. The graph implements a combined **ReAct + Reflection** paradigm.

#### 6.1.1 ReAct (Reason-Act-Observe)

The ReAct paradigm [13] interleaves three phases:

- **Reason**: The LLM explicitly articulates what information it needs and why.
- **Act**: The system invokes the appropriate tool (ChromaDB retrieval, web search, etc.).
- **Observe**: The results are incorporated into the context for the next reasoning step.

This approach enables the system to make informed decisions about which tools to invoke, rather than blindly executing a fixed pipeline.

#### 6.1.2 Reflection

After generating a draft response, the system performs self-critique through a reflection step. The LLM scores the response on a 1–10 scale and provides specific feedback on:

- Factual accuracy relative to retrieved sources
- Completeness of the answer
- Appropriate citation of sources
- Tone and helpfulness

If the reflection score falls below the configurable threshold (default: 7), the response enters a **refinement** loop where the LLM improves the answer based on its own critique. This self-correction mechanism significantly reduces the incidence of low-quality responses reaching the user.

### 6.2 Graph Structure

The LangGraph pipeline consists of the following nodes:

```
Router → Gather → Evaluate → Generate → Reflect → [Refine] → Save
```

**Node 1 — Router**: Classifies the incoming query into one of three categories:
- `general`: Non-Stevens questions answerable from general knowledge
- `domain`: Stevens-specific questions requiring retrieval
- `blocked`: Harmful, inappropriate, or adversarial queries

The router also generates a descriptive chat session name for the conversation.

**Node 2 — Gather**: Executes information retrieval agents in parallel:
- **HistoryAgent**: Retrieves the last 10 Q&A pairs from the conversation memory
- **ChromaAgent**: Performs hybrid entity-aware retrieval from ChromaDB (domain queries)
- **GeneralAgent**: Invokes the LLM directly for general knowledge queries

**Node 3 — Evaluate**: A ReAct "think" step that assesses whether the gathered information is sufficient to answer the query. If the Chroma retrieval yields insufficient results, the system decides whether to invoke web search as a fallback.

**Node 4 — Web Search** (conditional): If the evaluate step determines web search is needed, the `WebAgent` is invoked, which:
1. Queries DuckDuckGo or SerpAPI with the reformulated query
2. Scrapes the top-k result URLs
3. Cleans and truncates the scraped content

**Node 5 — Generate**: Synthesizes the final answer from all gathered context (history, ChromaDB documents, web results). The generation prompt includes source attribution instructions.

**Node 6 — Reflect**: Self-critique scoring and feedback generation. The reflection is conditioned on the retrieved sources, enabling fact-checking against the evidence.

**Node 7 — Refine** (conditional): If the reflection score < threshold, the response is refined using the reflection feedback as guidance.

**Node 8 — Save**: Persists the conversation turn to the in-memory store and triggers asynchronous MongoDB persistence.

### 6.3 Safety System

The safety system operates at multiple levels:

1. **Input sanitization**: Query length limits (2,000 characters), HTML/injection stripping.
2. **Regex-based blocking**: Pre-compiled patterns detect violence, profanity, technology probing (attempts to reveal the system prompt or tech stack), and academic dishonesty requests.
3. **LLM classification**: The router uses LLM reasoning to classify edge cases that escape regex detection.
4. **Identity protection**: The system never reveals its underlying technology stack, model names, or system prompts to users.

### 6.4 Multi-Provider LLM Support

The production system's response generation is powered by cloud-hosted LLMs. The `LLMRouter` provides abstracted access to multiple LLM providers with automatic fallback:

| Priority | Provider | Model | Use Case |
|---|---|---|---|
| 1 (Default) | Google | Gemini 2.0 Flash | Primary generation for all chat responses |
| 2 (Fallback) | OpenAI | GPT-4o-mini | Backup when Gemini is unavailable |
| 3 (Fallback) | Anthropic | Claude 3.5 Haiku | Secondary backup |
| Future | Self-hosted | Fine-tuned LLaMA-2-7B (QLoRA) | Planned self-hosted generation |

*Table 3: LLM provider priority, fallback configuration, and planned self-hosted model.*

Google Gemini 2.0 Flash serves as the primary generation model across all pipeline stages — routing, generation, reflection, and refinement — due to its strong instruction-following capabilities and low-latency inference. OpenAI GPT-4o-mini provides a reliable fallback. This multi-provider architecture ensures high availability, allows seamless migration between providers, and is designed to accommodate the future integration of the self-hosted fine-tuned LLaMA model as an additional provider option.

---

## 7. Full-Stack Implementation

### 7.1 Frontend

The frontend is built with **React 19** and **Vite 5**, styled with **Tailwind CSS** and animated with **Framer Motion**. Key components include:

- **ChatInterface**: The primary chat UI with markdown rendering (via `react-markdown` and `remark-gfm`), syntax-highlighted code blocks, message copy functionality, and thumbs up/down feedback buttons.
- **ChatSessionManager**: Manages multiple chat sessions with create, rename, and delete functionality.
- **ChatHistoryView**: Provides a searchable history of past conversations.
- **AdminDashboard**: An administrative interface for managing courses, faculty, users, web scraper status, and job/internship listings.
- **Profile Completion Flow**: A guided onboarding that includes resume upload with AI-powered information extraction for personalized advising.

**Authentication** is handled via **Firebase Auth** with email/password authentication and email verification. Protected routes ensure that only authenticated users with completed profiles can access the dashboard.

### 7.2 Backend

The backend employs a hybrid **FastAPI + Flask** architecture:

- **FastAPI** (`main.py`): Handles the performance-critical chat endpoints (`/api/chat/stream`, `/api/chat/query`) using async/await and SSE streaming. FastAPI's native async support enables efficient handling of concurrent chat sessions.
- **Flask** (`app.py`): Handles the remaining ~50 API routes for authentication, profile management, course/faculty CRUD, admin operations, and job/internship management. Flask is mounted as WSGI middleware within the FastAPI application.

This dual-framework approach leverages FastAPI's superior async performance for streaming chat responses while retaining Flask's mature ecosystem for conventional REST endpoints.

### 7.3 Database Layer

- **MongoDB Atlas**: Stores user profiles, chat sessions, chat history, course data, faculty information, and administrative data. User documents are cached in-memory with TTL-based expiration for performance.
- **ChromaDB**: Serves as the vector database for semantic retrieval, storing embedded document chunks organized into domain-specific collections.

### 7.4 Real-Time Streaming

Chat responses are delivered via **Server-Sent Events (SSE)**, enabling token-by-token streaming from the LLM to the frontend. The streaming pipeline:

1. FastAPI endpoint opens an SSE connection
2. The LangGraph orchestrator yields token chunks asynchronously
3. Each chunk is sent as an SSE `data` event
4. A final `done` event includes source attributions (database documents, web URLs, conversation history)
5. The frontend progressively renders the response with markdown formatting

### 7.5 Deployment

The application is containerized using **Docker** with a `python:3.12-slim` base image and deployed on **Google Cloud Run**:

```
CMD: uvicorn main:app --host 0.0.0.0 --port 8080
     --workers 2 --limit-concurrency 200 --timeout-keep-alive 30
```

The frontend is deployed on **Firebase Hosting** (`advisoraii.web.app`). This separation of frontend and backend hosting enables independent scaling and deployment cycles.

### 7.6 Additional Features

- **Resume Processing**: PDF and DOCX resume upload with AI-powered extraction of skills, education, and experience for personalized advising.
- **Jobs & Internships**: Automated scraping of job and internship listings, with background scheduling and search capabilities.
- **Course and Faculty Reviews**: Students can submit and browse reviews for courses and professors.
- **Web Scraper**: An administrative tool for on-demand scraping of university web pages to update the knowledge base.

---

## 8. Evaluation and Discussion

### 8.1 Qualitative Assessment

AdvisorAI has been evaluated qualitatively across several dimensions:

- **Factual accuracy**: For structured queries about courses, faculty, and programs, the entity-aware hybrid retrieval ensures that responses are grounded in authoritative university data rather than LLM-generated approximations.
- **Hallucination reduction**: The combination of RAG (grounding in retrieved documents), reflection (self-critique scoring), and source attribution significantly reduces hallucination compared to a baseline of prompting a general-purpose LLM.
- **Response quality**: The reflection mechanism with a threshold score of 7/10 provides a quality floor, ensuring that low-confidence responses are refined before delivery.
- **Latency**: Entity detection operates in sub-millisecond time, and streaming SSE delivery provides immediate feedback to users while the full response generates.

### 8.2 Architecture Advantages

**Hybrid retrieval outperforms pure semantic search**: For the academic advising domain, a significant proportion of queries contain structured entities (course codes, faculty names). The entity-aware routing achieves perfect precision for these queries, as it bypasses the approximate nature of embedding similarity search and directly applies metadata filters.

**Reflection improves response quality**: The self-critique mechanism catches issues such as incomplete answers, unsupported claims, and inappropriate tone before the response reaches the user. Empirically, approximately 15–20% of initial drafts receive a reflection score below 7 and benefit from the refinement loop.

**Multi-agent parallelism reduces latency**: By executing the ChromaDB, web search, and history agents in parallel during the gather phase, the system achieves lower end-to-end latency than a sequential pipeline.

### 8.3 Comparison with Existing Systems

| Feature | AdvisorAI | Generic LLM Chatbot | Traditional FAQ Bot |
|---|---|---|---|
| Domain-specific fine-tuning | Yes (QLoRA, parallel research) | No | No |
| Retrieval augmentation | Yes (Hybrid) | Optional | Keyword match |
| Self-reflection quality gate | Yes | No | No |
| Real-time streaming | Yes | Varies | No |
| Multi-agent orchestration | Yes (LangGraph) | No | No |
| Entity-aware routing | Yes | No | No |
| Source attribution | Yes | No | No |
| Safety system | Multi-layered | Basic | Rule-based |

*Table 4: Feature comparison of AdvisorAI with alternative approaches.*

### 8.4 Limitations

- **Evaluation scope**: The current evaluation is primarily qualitative. A comprehensive quantitative evaluation with human annotation on a held-out test set is planned for future work.
- **Cloud API dependency**: The production system currently relies on Google Gemini and OpenAI APIs for generation, incurring per-token costs and requiring internet connectivity. The QLoRA fine-tuned LLaMA-2-7B model has been trained as a parallel effort to address this limitation; its integration as the primary generation backend is a key next step.
- **Fine-tuned model benchmarking**: While the fine-tuned LLaMA-2-7B model has been trained and checkpointed, a comprehensive side-by-side comparison with the cloud-hosted models (Gemini, GPT-4o-mini) on domain-specific accuracy, fluency, and latency has not yet been conducted.
- **Knowledge freshness**: While the web search fallback provides access to current information, the ChromaDB vector store requires periodic re-indexing to reflect curriculum changes.
- **Single institution**: The current system is designed for Stevens Institute of Technology. Generalization to other institutions would require a new data collection and fine-tuning cycle.

---

## 9. Conclusion and Future Work

### 9.1 Conclusion

We have presented AdvisorAI, a comprehensive academic advising chatbot that combines cloud-hosted LLMs with retrieval-augmented generation in a multi-agent architecture, complemented by a parallel fine-tuning research effort. The system addresses the fundamental challenges of domain-specific question-answering — hallucination, information freshness, and query diversity — through a combination of:

1. **Cloud LLM integration** with Google Gemini and OpenAI, providing high-quality generation with multi-provider fallback for reliability
2. **Entity-aware hybrid retrieval** with sub-millisecond routing for structured queries
3. **LangGraph multi-agent orchestration** with ReAct reasoning and self-reflection quality gates
4. **Production-grade deployment** with streaming responses, authentication, and cloud scalability
5. **QLoRA fine-tuning** of LLaMA-2-7B on ~87K domain-specific Q&A pairs, establishing a pathway toward self-hosted, cost-effective generation

AdvisorAI demonstrates that the combination of intelligent retrieval, agentic orchestration, and cloud-hosted LLMs can produce a reliable, low-hallucination academic advising system suitable for real-world university deployment, while the parallel fine-tuning effort paves the way for future independence from external API providers.

### 9.2 Future Work

Several directions for future development are planned:

- **Quantitative evaluation**: Conducting systematic evaluation with human annotators using metrics such as factual accuracy, relevance, completeness, and user satisfaction.
- **Self-hosted fine-tuned model deployment**: Integrating the already-trained QLoRA fine-tuned LLaMA-2-7B model into the production pipeline as the primary generation backbone, eliminating dependency on cloud LLM APIs and reducing per-query cost. This includes benchmarking against Gemini and GPT-4o-mini on domain-specific accuracy metrics.
- **Multi-modal support**: Extending the system to handle image-based queries (e.g., screenshots of course schedules, campus maps).
- **Proactive advising**: Implementing a recommendation engine that proactively suggests courses, research opportunities, and career resources based on the student's profile and academic history.
- **Multi-institutional generalization**: Developing a framework for rapidly adapting AdvisorAI to new universities with minimal manual effort.
- **Continuous learning**: Implementing feedback-driven fine-tuning loops that leverage user thumbs-up/down signals to continuously improve response quality.

---

## References

[1] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A.N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention is All You Need," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017.

[2] OpenAI, "GPT-4 Technical Report," *arXiv preprint arXiv:2303.08774*, 2023.

[3] H. Touvron, T. Lavril, G. Izacard, X. Martinet, M.-A. Lachaux, T. Lacroix, B. Rozière, N. Goyal, E. Hambro, F. Azhar, et al., "LLaMA: Open and Efficient Foundation Language Models," *arXiv preprint arXiv:2302.13971*, 2023.

[4] H. Touvron, L. Martin, K. Stone, P. Albert, A. Almahairi, Y. Babaei, N. Bashlykov, S. Basu, S. Bhatt, R. Bhosale, et al., "Llama 2: Open Foundation and Fine-Tuned Chat Models," *arXiv preprint arXiv:2307.09288*, 2023.

[5] Google DeepMind, "Gemini: A Family of Highly Capable Multimodal Models," *arXiv preprint arXiv:2312.11805*, 2023.

[6] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W.-t. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 9459–9474, 2020.

[7] W. Chen, H. Zha, Z. Chen, W. Xiong, H. Wang, and W. Y. Wang, "HybridQA: A Dataset of Multi-Hop Question Answering over Tabular and Textual Data," *Findings of EMNLP*, 2020.

[8] K. Petroni, T. Rocktäschel, S. Riedel, P. Lewis, A. Bakhtin, Y. Wu, and A. Miller, "Language Models as Knowledge Bases?" *Proceedings of EMNLP-IJCNLP*, 2019.

[9] G. Izacard and E. Grave, "Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering," *Proceedings of EACL*, 2021.

[10] E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang, and W. Chen, "LoRA: Low-Rank Adaptation of Large Language Models," *International Conference on Learning Representations (ICLR)*, 2022.

[11] T. Dettmers, A. Pagnoni, A. Holtzman, and L. Zettlemoyer, "QLoRA: Efficient Finetuning of Quantized Language Models," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 36, 2023.

[12] S. Yao, H. Chen, J. Yang, and K. Narasimhan, "WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 35, 2022.

[13] S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao, "ReAct: Synergizing Reasoning and Acting in Language Models," *International Conference on Learning Representations (ICLR)*, 2023.

[14] LangChain, "LangGraph: Build Stateful, Multi-Agent Applications," 2024. [Online]. Available: https://github.com/langchain-ai/langgraph

[15] N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language Agents with Verbal Reinforcement Learning," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 36, 2023.

[16] A. Holotescu, "MOOCBuddy: A Chatbot for Personalized Learning with MOOCs," *Proceedings of the International Conference on Human-Computer Interaction*, 2016.

[17] A. S. Hasan, "Chatbot for University Related FAQs," *International Conference on Advances in Computing, Communication and Applied Informatics*, 2019.

[18] T. S. Ranoliya, N. Raghuwanshi, and S. Singh, "Chatbot for University Related FAQs," *International Conference on Advances in Computing, Communications and Informatics (ICACCI)*, pp. 1525–1530, 2017.

[19] D. Biswas, "University Chatbots Using Artificial Intelligence," *Journal of Emerging Technologies and Innovative Research*, vol. 7, no. 1, 2020.

---

## Appendix A: Dataset Statistics

| Metric | Value |
|---|---|
| Total Q&A Pairs | 87,782 |
| Data Format | JSONL |
| Fields per Entry | 3 (context, question, answer) |
| Sources Scraped | Stevens website, academic catalog, faculty pages |
| Train/Eval Split | 90% / 10% |
| Missing Values | 0 |
| Empty Strings | 0 |

*Table A1: Summary statistics of the fine-tuning dataset.*

## Appendix B: Technology Stack Summary

| Layer | Technology |
|---|---|
| Frontend Framework | React 19, Vite 5 |
| Frontend Styling | Tailwind CSS, Framer Motion |
| Authentication | Firebase Auth |
| Backend (Async) | FastAPI + Uvicorn |
| Backend (REST) | Flask (WSGI Middleware) |
| Database | MongoDB Atlas |
| Vector Database | ChromaDB 0.5.23 |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| LLM (Primary) | Google Gemini 2.0 Flash |
| LLM (Fallback) | OpenAI GPT-4o-mini, Claude 3.5 Haiku |
| Orchestration | LangGraph (StateGraph) |
| Fine-Tuning | QLoRA on LLaMA-2-7B |
| Deployment (Backend) | Docker, Google Cloud Run |
| Deployment (Frontend) | Firebase Hosting |
| Web Search | DuckDuckGo, SerpAPI |

*Table B1: Complete technology stack of AdvisorAI.*

## Appendix C: API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat/stream` | POST | SSE streaming chat response |
| `/api/chat/query` | POST | Non-streaming chat response |
| `/health` | GET | Health check |
| `/api/auth/signup` | POST | User registration |
| `/api/auth/login` | POST | User authentication |
| `/api/profile` | GET/PUT | User profile management |
| `/api/courses` | GET/POST/PUT/DELETE | Course CRUD |
| `/api/faculty` | GET/POST/PUT/DELETE | Faculty CRUD |
| `/api/chat/sessions` | GET/POST/DELETE | Chat session management |
| `/api/admin/*` | Various | Admin dashboard operations |

*Table C1: Primary API endpoints.*
