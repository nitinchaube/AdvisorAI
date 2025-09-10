# LangGraph Chatbot

A modular, production-ready, LangGraph-powered agentic AI chatbot with real-time dynamic tool selection and high concurrency handling.

## Features

- **LangGraph Orchestration**: ReAct-based flow with parallel tool execution
- **ReACT Reasoning**: LLM-driven decision making for web search based on available information
- **Dynamic Tool Selection**: LLM-driven tool routing based on query content
- **Multiple Vector DB Collections**: ChromaDB integration with multiple collections
- **Web Search Integration**: Intelligent fallback to web search using existing web_scrapper functions
- **Conversation Memory**: Pluggable memory storage (in-memory, Redis, Postgres)
- **LLM Switching**: Support for OpenAI, Gemini, and Claude with fallback logic
- **High Concurrency**: Async/await throughout for optimal performance
- **Production Ready**: FastAPI with health checks, error handling, and monitoring

## Architecture

```
chatbot/
├── config/
│   ├── __init__.py
│   └── settings.py          # Environment-based configuration
├── core/
│   ├── __init__.py
│   ├── llm_router.py        # LLM provider management
│   ├── memory_store.py      # Abstract memory storage
│   └── langgraph_graph.py   # Main orchestrator with ReACT reasoning
├── tools/
│   ├── __init__.py
│   ├── chroma_tool.py       # Vector database operations
│   ├── web_tool.py          # Web search and scraping
│   ├── history_tool.py      # Conversation history
│   └── general_tool.py      # General knowledge questions
├── agents/
│   ├── __init__.py
│   ├── base_agent.py        # Abstract agent base
│   ├── chroma_agent.py      # Vector DB agent
│   ├── web_agent.py         # Web search agent
│   ├── history_agent.py     # History agent
│   └── general_agent.py     # General knowledge agent
├── prompts/
│   ├── __init__.py
│   ├── tool_router.prompt   # Tool selection prompt
│   └── final_answer.prompt  # Answer synthesis prompt
├── main.py                  # FastAPI entry point
├── requirements.txt         # Dependencies
├── example_usage.py         # Usage example
└── README.md               # This file
```

## ReACT Workflow

The chatbot implements a sophisticated ReACT (Reasoning and Acting) workflow:

1. **Router Node**: LLM decides which tools to use based on query
2. **Tools Node**: Executes selected tools in parallel (Chroma, History, General)
3. **Reason Node**: LLM analyzes available information and decides if web search is needed
4. **Web Search Node**: Performs web search only when LLM determines it's necessary
5. **Final Node**: Synthesizes all results into final answer
6. **Save Node**: Stores conversation in memory

### ReACT Reasoning Examples

**No Web Search Needed:**
- "What courses are available in Computer Science?" → Sufficient info in database
- "What is machine learning?" → General knowledge, no current info needed

**Web Search Triggered:**
- "What are the latest developments in AI at Stevens?" → Needs current information
- "What are the current admission requirements?" → Policy may have changed
- "What are the latest research projects?" → Requires recent updates

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file (see `.env.example`)

3. Ensure VectorDB directory exists with collections:
   - AllCourseRelatedData
   - AllFacultyGeneralInformation
   - AllFacultyResearchInformation

## Usage

### Running the API Server

```bash
cd chatbot
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

- `POST /chat` - Process chat queries
- `GET /health` - Health check
- `GET /stats` - System statistics

### Example Usage

```python
import asyncio
from core.langgraph_graph import LangGraphOrchestrator

async def main():
    orchestrator = LangGraphOrchestrator()
    
    result = await orchestrator.process_query(
        query="What are the latest developments in AI at Stevens?",
        user_id="user123"
    )
    
    print(f"Answer: {result['answer']}")
    print(f"Tools used: {result['metadata']['tools_used']}")
    print(f"Web search performed: {result['metadata']['web_search_performed']}")
    print(f"Reasoning: {result['metadata']['reasoning_result']['reasoning']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Environment Variables

- `LLM_PROVIDER`: LLM provider (openai, gemini, claude)
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google API key for Gemini
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude
- `VECTORDB_DIR`: Path to vector database directory
- `WEB_SEARCH_ENABLED`: Enable/disable web search
- `MEMORY_TYPE`: Memory storage type (in_memory, redis, postgres)

### LLM Models

- OpenAI: `gpt-4`, `gpt-3.5-turbo`
- Gemini: `gemini-2.0-flash`, `gemini-1.5-pro`
- Claude: `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

## ReACT Reasoning Logic

The system uses intelligent reasoning to determine when web search is needed:

### Web Search Triggers:
- Questions requiring current/recent information
- Insufficient information in available sources
- Questions needing external context
- Specific details not covered in database

### No Web Search When:
- Available information is comprehensive
- General knowledge questions are well covered
- Answer can be provided from existing information

## Integration

The chatbot integrates with your existing project:

- Uses `web_scrapper.py` functions for web search
- Compatible with existing ChromaDB collections
- Maintains same environment variables as main project
- Can be integrated into existing Flask backend

## Development

### Adding New Tools

1. Create tool class in `tools/`
2. Create agent in `agents/`
3. Update router prompt in `prompts/tool_router.prompt`
4. Add tool to orchestrator in `core/langgraph_graph.py`

### Adding New Memory Stores

1. Implement `MemoryStore` interface in `core/memory_store.py`
2. Update `get_memory_store()` factory function
3. Add configuration option in `config/settings.py`

## Performance

- **Parallel Tool Execution**: Tools run concurrently for faster responses
- **Selective Tool Use**: Only necessary tools are executed
- **Intelligent Web Search**: Web search only when LLM determines it's needed
- **Caching**: Memory stores provide conversation caching
- **ReACT Efficiency**: Avoids unnecessary web searches

## Monitoring

- Health check endpoint for service monitoring
- Statistics endpoint for system metrics
- Error handling with detailed error messages
- Logging throughout the workflow
- Reasoning transparency in metadata

## Production Deployment

1. Set up environment variables
2. Configure memory store (Redis recommended for production)
3. Set up monitoring and logging
4. Deploy with uvicorn or gunicorn
5. Configure reverse proxy (nginx)

## License

This project is part of the AdvisorAI system. 