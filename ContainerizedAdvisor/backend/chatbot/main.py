from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from core.langgraph_graph import LangGraphOrchestrator
from config.settings import settings

app = FastAPI(title="LangGraph Chatbot API", version="1.0.0")

# Initialize the orchestrator
orchestrator = LangGraphOrchestrator()

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    success: bool
    answer: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        result = await orchestrator.process_query(
            query=request.query,
            user_id=request.user_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LangGraph Chatbot"}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        from tools.chroma_tool import ChromaTool
        chroma_tool = ChromaTool()
        stats = chroma_tool.get_collection_stats()
        return {"collections": stats}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
