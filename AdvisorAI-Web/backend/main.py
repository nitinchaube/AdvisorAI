"""
AdvisorAI Backend – FastAPI + uvicorn entry point.

Architecture
============
• Performance-critical chat endpoints (streaming SSE, query) run as
  **native async** FastAPI routes — no sync-to-async bridge, thousands
  of concurrent connections on a single process.

• All other endpoints (auth, profile, admin, jobs, …) are served by
  the existing Flask app mounted via ``WSGIMiddleware``.  Zero rewrites
  needed for the ~50 existing routes.

Usage (development)
-------------------
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload

Usage (production via Dockerfile)
---------------------------------
    uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2 --limit-concurrency 200 --timeout-keep-alive 30
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.wsgi import WSGIMiddleware

import firebase_admin
from firebase_admin import auth as firebase_auth
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger("advisorai.fastapi")

# ═══════════════════════════════════════════════════════════════════════════
# MongoDB (reuse the same connection settings as Flask app)
# ═══════════════════════════════════════════════════════════════════════════

MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "AdvisorAI")
mongo_client = MongoClient(
    MONGO_URI,
    maxPoolSize=50,
    minPoolSize=5,
    maxIdleTimeMS=30000,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
    retryWrites=True,
)
mongo_db = mongo_client[MONGO_DB_NAME]

# ═══════════════════════════════════════════════════════════════════════════
# Firebase (initialise only if not already done by the Flask app import)
# ═══════════════════════════════════════════════════════════════════════════

if not firebase_admin._apps:
    firebase_admin.initialize_app()
    logger.info("Firebase Admin SDK initialized (from FastAPI main)")

# ═══════════════════════════════════════════════════════════════════════════
# Chatbot integration singleton
# ═══════════════════════════════════════════════════════════════════════════

from chatbot_integration import get_chatbot_integration

# ═══════════════════════════════════════════════════════════════════════════
# FastAPI app
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="AdvisorAI",
    description="AI Academic Advisor for Stevens Institute of Technology",
    version="2.0.0",
)

# ── CORS (mirrors Flask CORS config) ─────────────────────────────────────

_cors_origins_str = os.environ.get("CORS_ORIGINS", "")
if _cors_origins_str:
    CORS_ORIGINS = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5003",
        "http://127.0.0.1:5003",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Content-Range"],
)

# ═══════════════════════════════════════════════════════════════════════════
# Auth dependency (replaces Flask's @verify_token decorator)
# ═══════════════════════════════════════════════════════════════════════════

# In-memory token cache (shared with Flask's cache via import)
from app import _get_cached_user, _set_cached_user


async def verify_firebase_token(request: Request) -> dict:
    """FastAPI dependency: verify Firebase ID token and return user doc.

    Mirrors the Flask ``verify_token`` decorator logic, including the
    in-memory TTL cache to avoid repeated Firebase + MongoDB round-trips.
    """
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token is missing")

    id_token = authorization.split("Bearer ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")

    user_id = decoded_token["uid"]

    # Fast path: serve from cache
    cached = _get_cached_user(user_id)
    if cached and cached.get("emailVerified"):
        return cached

    # Slow path: MongoDB lookup
    user_doc = mongo_db.users.find_one({"uid": user_id})

    if not user_doc:
        # Auto-create minimal profile from Firebase
        try:
            fb_user = firebase_auth.get_user(user_id)
            user_doc = {
                "uid": user_id,
                "email": fb_user.email,
                "fullName": fb_user.display_name or "",
                "createdAt": datetime.now(),
                "profileCompleted": False,
                "resumeData": {},
                "role": "user",
                "emailVerified": fb_user.email_verified,
            }
            mongo_db.users.insert_one(user_doc)
        except Exception:
            raise HTTPException(status_code=500, detail="User profile creation failed")

    # Check email verification
    if not user_doc.get("emailVerified", False):
        try:
            fb_user = firebase_auth.get_user(user_id)
            if fb_user.email_verified:
                mongo_db.users.update_one(
                    {"uid": user_id},
                    {"$set": {"emailVerified": True, "emailVerifiedAt": datetime.now()}},
                )
                user_doc["emailVerified"] = True
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Email not verified. Please verify your email first.",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Email not verified")

    _set_cached_user(user_id, user_doc)
    return user_doc


# ═══════════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Lightweight health check for Cloud Run / load balancer."""
    chatbot = get_chatbot_integration()
    return {
        "status": "ok",
        "orchestrator_available": chatbot.orchestrator is not None,
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Native async chat endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/chat/stream")
async def chat_stream(request: Request, user: dict = Depends(verify_firebase_token)):
    """Stream chat response via Server-Sent Events (native async).

    This replaces the Flask SSE endpoint with a truly async implementation
    that does NOT block a thread while waiting for LLM tokens.
    """
    data = await request.json()
    query = data.get("query", "").strip()
    chat_history = data.get("chat_history", [])
    session_id = data.get("session_id")
    user_id = user["uid"]

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    logger.info("Async streaming for user %s session %s: %s", user_id, session_id, query[:80])

    collected_answer = ""
    collected_meta: dict = {}

    async def event_generator():
        nonlocal collected_answer, collected_meta
        chatbot = get_chatbot_integration()

        async for event in chatbot.async_stream_query(
            user_query=query,
            user_id=user_id,
            chat_history=chat_history,
        ):
            etype = event.get("type")
            if etype == "token":
                collected_answer += event.get("content", "")
            elif etype == "done":
                collected_meta = event

            yield f"data: {json.dumps(event)}\n\n"

    async def stream_and_persist():
        async for chunk in event_generator():
            yield chunk

        # Persist after stream completes
        full_answer = collected_answer.strip()
        if full_answer and session_id:
            chat_name = collected_meta.get("chat_name", "New Chat")
            _persist_session(user_id, session_id, query, full_answer, collected_meta, chat_name)

    return StreamingResponse(
        stream_and_persist(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat/query")
async def chat_query(request: Request, user: dict = Depends(verify_firebase_token)):
    """Process chat query natively async (no thread-blocking)."""
    data = await request.json()
    query = data.get("query", "").strip()
    chat_history = data.get("chat_history", [])
    session_id = data.get("session_id")
    user_id = user["uid"]

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    logger.info("Async chat query for user %s session %s: %s", user_id, session_id, query[:80])

    chatbot = get_chatbot_integration()
    result = await chatbot.async_process_query(
        user_query=query,
        user_id=user_id,
        chat_history=chat_history,
    )

    chat_name = result.get("chat_name", "New Chat")

    # Persist to MongoDB
    if result.get("response") and session_id:
        _persist_session(user_id, session_id, query, result["response"], result, chat_name)

    # Legacy chat_history
    if result.get("response"):
        try:
            mongo_db.chat_history.insert_one({
                "user_id": user_id,
                "query": query,
                "response": result["response"],
                "timestamp": datetime.now(),
                "sources": result.get("sources", {}),
                "processing_time": result.get("processing_time", 0),
                "session_id": session_id,
            })
        except Exception as e:
            logger.error("Legacy chat_history save error: %s", e)

    return JSONResponse(content={
        "success": True,
        "response": result["response"],
        "sources": result.get("sources", {}),
        "processing_time": result.get("processing_time", 0),
        "error": result.get("error", False),
        "chat_name": chat_name,
    })


def _persist_session(
    user_id: str,
    session_id: str,
    query: str,
    answer: str,
    meta: dict,
    chat_name: str,
):
    """Persist chat messages to MongoDB using atomic $push."""
    try:
        user_msg = {
            "id": f"user_{int(time.time() * 1000)}",
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat(),
        }
        ai_msg = {
            "id": f"ai_{int(time.time() * 1000)}",
            "role": "assistant",
            "content": answer,
            "timestamp": datetime.now().isoformat(),
            "sources": meta.get("sources", {}),
        }

        update_ops = {
            "$push": {"messages": {"$each": [user_msg, ai_msg]}},
            "$set": {"last_updated": datetime.now()},
            "$inc": {"message_count": 2},
        }

        if chat_name and chat_name != "New Chat":
            # Update title only if still "New Chat"
            mongo_db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id, "title": "New Chat"},
                {**update_ops, "$set": {**update_ops["$set"], "title": chat_name}},
            )
            # Push messages even if title was already set
            mongo_db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id, "title": {"$ne": "New Chat"}},
                update_ops,
            )
        else:
            mongo_db.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                update_ops,
            )
    except Exception as e:
        logger.error("Session persist error: %s", e)

    # Legacy chat_history
    try:
        mongo_db.chat_history.insert_one({
            "user_id": user_id,
            "query": query,
            "response": answer,
            "timestamp": datetime.now(),
            "sources": meta.get("sources", {}),
            "session_id": session_id,
        })
    except Exception as e:
        logger.error("Legacy chat_history save error: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
# Mount Flask app for ALL other endpoints
# ═══════════════════════════════════════════════════════════════════════════
# FastAPI routes take precedence (chat endpoints above), everything else
# falls through to the existing Flask app.

from app import app as flask_app  # noqa: E402

app.mount("/", WSGIMiddleware(flask_app))
