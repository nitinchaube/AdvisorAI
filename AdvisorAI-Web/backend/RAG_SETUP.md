# RAG Service Setup Guide

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
PORT=5002

# Firebase Configuration
# Make sure firebase_key.json is in the backend directory

# LLM Configuration
LLM_PROVIDER=gemini  # or "openai"
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
GEMINI_MODEL=gemini-2.0-flash
OPENAI_MODEL=gpt-4

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector Database Configuration
VECTORDB_DIR=./VectorDB

# Retrieval Configuration
TOP_K_PER_COLLECTION=5
MAX_TOTAL_DOCS=5

# Web Search Configuration
WEB_SEARCH_ENABLED=true
WEB_SEARCH_RESULTS=3

# API Configuration
API_BASE_URL=http://localhost:5002

# Prompt Templates (optional - will use defaults if not set)
ROUTER_PROMPT=You are a smart router in a RAG system for Stevens Institute of Technology...

RAG_PROMPT_TEMPLATE=You are an intelligent academic advisor for Stevens Institute of Technology...

WEB_ENHANCED_PROMPT_TEMPLATE=You are an intelligent academic advisor for Stevens Institute of Technology...

WEB_SEARCH_INDICATORS=i need to search the web,i need to do a web search,i don't have information,i don't have access to,i cannot provide,i'm unable to,i don't have recent,my training data,i don't have current,i'm not aware of,i don't have specific,i cannot answer,i don't have details,i'm not familiar with,i don't have up-to-date,web search,search the web
```

## Installation Notes

**Important**: The requirements.txt has been updated to resolve dependency conflicts:

1. **OpenAI**: Changed from `openai==0.28.0` to `openai>=1.10.0,<2.0.0` to be compatible with `langchain-openai`
2. **Google Generative AI**: Changed from `google-generativeai==0.3.0` to `google-generativeai>=0.3.1,<0.4.0` to be compatible with `langchain-google-genai`

These changes ensure all langchain packages work together without conflicts.

## Architecture Overview

The RAG service implements the following architecture:

1. **Query Processing**: User query is received
2. **Collection Routing**: LLM determines which collections to search
3. **Document Retrieval**: Top-k documents retrieved from each collection and sorted
4. **Context Building**: Documents combined with user profile info
5. **LLM Response**: Initial response generated
6. **Web Search**: If needed, web search is performed and response enhanced
7. **Final Response**: Comprehensive answer returned with sources

## Key Features

- **Environment Variables**: All configuration through environment variables
- **Top-K Retrieval**: Retrieves top-k documents from each collection, then sorts and returns top-5
- **User Context**: Fetches user profile from database API for personalized responses
- **Web Search Integration**: Automatic web search when information is insufficient
- **Source Tracking**: Tracks which collections were used and document scores
- **Streaming Support**: Real-time token streaming for better UX

## API Endpoints

- `POST /api/chat/query` - Process chat query with RAG
- `POST /api/chat/stream` - Stream chat response
- `GET /api/chat/history` - Get user's chat history
- `GET /api/rag/stats` - Get RAG system statistics

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Ensure VectorDB directory exists with collections:
   - AllCourseRelatedData
   - AllFacultyGeneralInformation
   - AllFacultyResearchInformation

4. Start the backend:
```bash
python app.py
```

## Usage

The RAG service is automatically integrated into the chat interface. Users can:

1. Ask questions about courses, professors, or academic planning
2. View sources used for each response
3. Get personalized responses based on their profile
4. Receive enhanced responses with web search when needed

## Configuration Options

- `TOP_K_PER_COLLECTION`: Number of documents to retrieve from each collection (default: 5)
- `MAX_TOTAL_DOCS`: Maximum total documents to return after sorting (default: 5)
- `WEB_SEARCH_ENABLED`: Enable/disable web search (default: true)
- `WEB_SEARCH_RESULTS`: Number of web search results to include (default: 3) 