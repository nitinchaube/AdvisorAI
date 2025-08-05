# Enhanced LangGraph Chatbot with Stevens Institute of Technology Web Search

## 🚀 Overview

This enhanced chatbot implements a sophisticated LangGraph-powered agentic AI system with intelligent web search integration specifically optimized for Stevens Institute of Technology queries.

## ✨ Key Features

### 🔍 Enhanced Web Search
- **Automatic Query Enhancement**: Every web query automatically appends "Stevens Institute of Technology" for better search results
- **Smart Decision Making**: Uses RAG service patterns to determine when web search is needed
- **Context-Aware**: Considers Chroma database results before deciding on web search
- **Time-Sensitive Detection**: Automatically triggers web search for current/recent information queries

### 🧠 Intelligent Reasoning
- **ReACT-Style Workflow**: LLM-driven reasoning about when to use web search
- **Multi-Tool Orchestration**: Parallel execution of Chroma, History, General, and Web tools
- **Fallback Logic**: Comprehensive error handling and fallback mechanisms

### 🎯 Stevens Institute of Technology Optimization
- **Domain-Specific**: Optimized for academic queries about Stevens Institute
- **Current Information**: Prioritizes up-to-date information from web sources
- **Procedural Queries**: Handles contact, application, and administrative questions

## 🏗️ Architecture

```
User Query → Router → Tools (Parallel) → Reason → Web Search (Conditional) → Final Answer
```

### Components

1. **Router Node**: Decides which tools to use
2. **Tools Node**: Executes Chroma, History, and General tools in parallel
3. **Reason Node**: LLM decides if web search is needed
4. **Web Search Node**: Performs enhanced web search with Stevens context
5. **Final Node**: Synthesizes all results into final answer
6. **Save Node**: Stores conversation in memory

## 🔧 Enhanced Web Search Logic

### Query Enhancement
```python
# Original query
"computer science courses"

# Enhanced query (automatically generated)
"computer science courses Stevens Institute of Technology"
```

### Smart Decision Making
The system uses sophisticated logic to determine when web search is needed:

#### Always Trigger Web Search For:
- **Time-sensitive queries**: "current", "recent", "latest", "2024", "2025", "upcoming"
- **Procedural queries**: "apply", "register", "contact", "email", "phone", "address"
- **Information queries**: "what is", "tell me about", "information about"
- **Technical queries**: "api", "endpoint", "setup", "installation", "guide"

#### Skip Web Search When:
- **Good Chroma results**: Similarity scores < 0.6
- **Comprehensive information**: Available from vector database
- **General knowledge**: Well-covered topics

## 📊 Usage Examples

### Domain-Specific Query
```python
query = "What computer science courses are available?"
# Uses: Chroma tool
# Skips: Web search (good vector database results)
```

### Time-Sensitive Query
```python
query = "What are the current admission requirements for 2024?"
# Uses: Chroma tool + Web search
# Enhanced: "What are the current admission requirements for 2024? Stevens Institute of Technology"
```

### Procedural Query
```python
query = "How do I contact the admissions office?"
# Uses: Chroma tool + Web search
# Enhanced: "How do I contact the admissions office? Stevens Institute of Technology"
```

### General Knowledge Query
```python
query = "Tell me about machine learning concepts"
# Uses: General tool
# Skips: Web search (general knowledge handled directly)
```

## 🛠️ Setup and Configuration

### Environment Variables
```bash
# LLM Configuration
LLM_PROVIDER=openai  # or gemini, claude
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key

# Vector Database
VECTORDB_DIR=./VectorDB
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_RESULTS=3

# Retrieval
TOP_K_PER_COLLECTION=5
MAX_TOTAL_DOCS=5
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Test setup
python test_setup.py

# Run enhanced example
python example_enhanced_usage.py
```

## 🧪 Testing

### Test Web Search Features
```bash
python test_web_search.py
```

### Test Full Workflow
```bash
python example_enhanced_usage.py
```

### Test Basic Setup
```bash
python test_setup.py
```

## 📈 Performance Features

### Parallel Execution
- Tools execute in parallel for faster response times
- Chroma, History, and General tools run simultaneously

### Smart Caching
- Chroma results influence web search decisions
- Avoids unnecessary web searches when good data is available

### Fallback Mechanisms
- Multiple LLM providers for reliability
- Graceful degradation when tools fail

## 🔍 Web Search Integration

### Enhanced Query Processing
1. **Input**: User query
2. **Enhancement**: Append "Stevens Institute of Technology" if not present
3. **Decision**: Smart logic determines if web search is needed
4. **Execution**: Use existing `web_scrapper` functions
5. **Integration**: Combine with Chroma results for comprehensive answers

### Decision Logic
```python
def _should_use_web_search(self, query: str, chroma_results: Dict = None) -> bool:
    # Time-sensitive indicators
    current_time_indicators = ["current", "recent", "latest", "2024", "2025"]
    
    # Technical/procedural indicators  
    technical_indicators = ["apply", "register", "contact", "email", "phone"]
    
    # Information-seeking indicators
    info_indicators = ["what is", "tell me about", "information about"]
    
    # Check Chroma results quality
    if chroma_results and chroma_results.get("documents"):
        very_good_docs = [doc for doc in docs if doc.get("score", 1.0) < 0.6]
        if very_good_docs:
            return False  # Skip web search
```

## 🎯 Benefits

### For Users
- **More Relevant Results**: Stevens-specific web searches
- **Faster Responses**: Smart decision making reduces unnecessary searches
- **Comprehensive Answers**: Combines vector database and web information
- **Current Information**: Always gets the latest data when needed

### For Developers
- **Modular Design**: Easy to extend and modify
- **Comprehensive Logging**: Detailed metadata for debugging
- **Error Handling**: Robust fallback mechanisms
- **Performance Optimized**: Parallel execution and smart caching

## 🔮 Future Enhancements

- **Multi-University Support**: Extend to other institutions
- **Advanced Caching**: Redis-based conversation memory
- **Real-time Updates**: WebSocket integration for live updates
- **Analytics Dashboard**: Usage statistics and performance metrics

## 📝 License

This project is part of the AdvisorAI system for Stevens Institute of Technology. 