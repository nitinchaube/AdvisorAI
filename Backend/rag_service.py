import os
import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import random

# Import web scraper
from WebScrapper.web_scrapper import scrape_web_content

load_dotenv()

class RAGService:
    def __init__(self):
        # Embeddings
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Vector DB Configuration
        self.vectordb_dir = os.getenv("VECTORDB_DIR", "./VectorDB")
        
        # Load all collections
        self.collections = self._load_all_collections()
        
        print(f"RAG Service initialized with {len(self.collections)} collections: {list(self.collections.keys())}")
    
    def _load_all_collections(self) -> Dict[str, Chroma]:
        """Load all vectorized collections from directory"""
        collections = {}
        if os.path.exists(self.vectordb_dir):
            for folder in os.listdir(self.vectordb_dir):
                full_path = os.path.join(self.vectordb_dir, folder)
                if os.path.isdir(full_path):
                    try:
                        collections[folder] = Chroma(
                            collection_name=folder,
                            persist_directory=full_path,
                            embedding_function=self.embedding_model
                        )
                        print(f"Loaded collection: {folder}")
                    except Exception as e:
                        print(f"Error loading collection {folder}: {e}")
        return collections
    
    def _get_llm(self, streaming: bool = False, callbacks: List = None):
        """Get LLM instance based on provider"""
        if self.llm_provider == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.google_api_key,
                streaming=streaming,
                callbacks=callbacks or []
            )
        elif self.llm_provider == "openai":
            return ChatOpenAI(
                model="gpt-4",
                openai_api_key=self.openai_api_key,
                streaming=streaming,
                callbacks=callbacks or []
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _ask_router_llm(self, user_query: str) -> List[str]:
        """Ask LLM which collections to search based on user query"""
        collections = list(self.collections.keys())
        
        prompt = f"""
        You are a smart router in a RAG system for Stevens Institute of Technology.

        Available collections:
        {collections}

        User question: "{user_query}"

        Your task is to determine which collections are most relevant to answer this question.
        Return ONLY a valid JSON array of collection names. No explanation.

        Examples:
        - For course questions: ["AllCourseRelatedData"]
        - For faculty questions: ["AllFacultyGeneralInformation", "AllFacultyResearchInformation"]
        - For general questions: ["AllFacultyGeneralInformation", "AllCourseRelatedData"]
        """
        
        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            selected_collections = json.loads(response.content.strip())
            
            # Validate that selected collections exist
            valid_collections = [col for col in selected_collections if col in collections]
            if not valid_collections:
                print("No valid collections selected, using all collections")
                return collections
            
            print(f"Router selected collections: {valid_collections}")
            return valid_collections
            
        except Exception as e:
            print(f"Error in router LLM: {e}")
            print("Falling back to all collections")
            return collections
    
    def _retrieve_from_collections(self, user_query: str, collection_names: List[str], top_k: int = 2) -> List[Document]:
        """Retrieve documents from specified collections"""
        all_docs = []
        
        for collection_name in collection_names:
            if collection_name in self.collections:
                try:
                    vector_store = self.collections[collection_name]
                    docs = vector_store.similarity_search(user_query, k=top_k)
                    
                    for doc in docs:
                        doc.metadata["collection"] = collection_name
                        doc.metadata["source"] = "vector_db"
                    
                    all_docs.extend(docs)
                    print(f"Retrieved {len(docs)} docs from {collection_name}")
                    
                except Exception as e:
                    print(f"Error retrieving from {collection_name}: {e}")
        
        return all_docs
    
    def _build_context_prompt(self, docs: List[Document], user_query: str, 
                             user_info: str = None, web_content: str = None) -> str:
        """Build context-aware prompt for LLM"""
        
        # Build context from vector database documents
        context_parts = []
        if docs:
            context_parts.append("Vector Database Information:")
            for doc in docs:
                collection = doc.metadata.get("collection", "unknown")
                context_parts.append(f"[{collection}]: {doc.page_content}")
        
        # Add web content if available
        if web_content:
            context_parts.append(f"\nWeb Search Information:\n{web_content}")
        
        context = "\n\n".join(context_parts)
        
        # Build user context
        user_context = ""
        if user_info:
            user_context = f"\nUser Profile Information:\n{user_info}"
        
        return f"""You are an intelligent academic advisor for Stevens Institute of Technology.

{user_context}

Available Information:
{context}

User Query: {user_query}

Instructions:
1. Use the provided information to give accurate, helpful responses
2. If the information is insufficient to answer the question, respond with: "I need to search the web for more information."
3. Be conversational and helpful
4. If you have enough information, provide a comprehensive answer
5. If the user asks about their personal information, use their profile data if available

Response:"""
    
    def _check_needs_web_search(self, llm_response: str) -> bool:
        """Check if LLM response indicates need for web search"""
        web_search_indicators = [
            "i need to search the web",
            "i need to do a web search",
            "i don't have information",
            "i don't have access to",
            "i cannot provide",
            "i'm unable to",
            "i don't have recent",
            "my training data",
            "i don't have current",
            "i'm not aware of",
            "i don't have specific",
            "i cannot answer",
            "i don't have details",
            "i'm not familiar with",
            "i don't have up-to-date",
            "web search",
            "search the web"
        ]
        
        response_lower = llm_response.lower()
        return any(indicator in response_lower for indicator in web_search_indicators)
    
    def _get_user_info_from_api(self, user_id: str) -> str:
        """Get user information from database API"""
        try:
            # This would be your actual API call to get user data
            # For now, returning empty string - implement based on your database structure
            api_url = f"http://localhost:5000/api/user/{user_id}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                # Format user data for context
                user_info_parts = []
                for key, value in user_data.items():
                    if key not in ['resume-data', 'resume-text'] and value:
                        if isinstance(value, (list, dict)):
                            user_info_parts.append(f"{key}: {json.dumps(value, indent=2)}")
                        else:
                            user_info_parts.append(f"{key}: {value}")
                
                return "\n".join(user_info_parts)
            else:
                print(f"Failed to get user info: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Error getting user info: {e}")
            return ""
    
    def process_query(self, user_query: str, user_id: str = None, 
                     chat_history: List[Dict] = None) -> Dict:
        """Main query processing function following the specified architecture"""
        
        start_time = time.time()
        
        try:
            # Step 1: Get user info from API if user_id provided
            user_info = ""
            if user_id:
                user_info = self._get_user_info_from_api(user_id)
                print(f"Retrieved user info for {user_id}")
            
            # Step 2: Ask LLM which collections to search
            selected_collections = self._ask_router_llm(user_query)
            
            # Step 3: Retrieve documents from selected collections
            docs = self._retrieve_from_collections(user_query, selected_collections, top_k=2)
            print(f"Retrieved {len(docs)} documents from collections")
            
            # Step 4: Build initial prompt and get LLM response
            initial_prompt = self._build_context_prompt(docs, user_query, user_info)
            llm = self._get_llm()
            initial_response = llm.invoke(initial_prompt).content
            
            # Step 5: Check if web search is needed
            if self._check_needs_web_search(initial_response):
                print("LLM needs web search. Getting additional information...")
                
                try:
                    # Perform web search
                    web_content = scrape_web_content(user_query, num_results=3)
                    
                    # Build enhanced prompt with web content
                    enhanced_prompt = f"""You are an intelligent academic advisor for Stevens Institute of Technology.

Your initial response was: {initial_response}

Additional web information for the query "{user_query}":
{web_content}

{user_info}

Please provide a comprehensive answer using both your initial knowledge and the web information above.
If the web information doesn't add value, stick with your original response.
"""
                    
                    # Get final response with web content
                    final_response = llm.invoke(enhanced_prompt).content
                    
                    return {
                        "response": final_response,
                        "processing_time": time.time() - start_time,
                        "sources": {
                            "collections_used": selected_collections,
                            "documents_retrieved": len(docs),
                            "web_search_performed": True,
                            "user_info_included": bool(user_info)
                        }
                    }
                    
                except Exception as e:
                    print(f"Web search failed: {e}")
                    return {
                        "response": initial_response,
                        "processing_time": time.time() - start_time,
                        "sources": {
                            "collections_used": selected_collections,
                            "documents_retrieved": len(docs),
                            "web_search_performed": False,
                            "web_search_error": str(e),
                            "user_info_included": bool(user_info)
                        }
                    }
            else:
                # No web search needed
                return {
                    "response": initial_response,
                    "processing_time": time.time() - start_time,
                    "sources": {
                        "collections_used": selected_collections,
                        "documents_retrieved": len(docs),
                        "web_search_performed": False,
                        "user_info_included": bool(user_info)
                    }
                }
                
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your query: {str(e)}",
                "error": True,
                "processing_time": time.time() - start_time,
                "sources": {}
            }
    
    def stream_query(self, user_query: str, user_id: str = None,
                    chat_history: List[Dict] = None):
        """Stream query response"""
        
        # Get user info
        user_info = ""
        if user_id:
            user_info = self._get_user_info_from_api(user_id)
        
        # Get collections and documents
        selected_collections = self._ask_router_llm(user_query)
        docs = self._retrieve_from_collections(user_query, selected_collections, top_k=2)
        
        # Build prompt
        prompt = self._build_context_prompt(docs, user_query, user_info)
        
        # Create streaming handler
        class StreamHandler(StreamingStdOutCallbackHandler):
            def __init__(self):
                super().__init__()
                self.tokens = []
            
            def on_llm_new_token(self, token: str, **kwargs):
                self.tokens.append(token)
                yield token
        
        # Get streaming LLM
        handler = StreamHandler()
        llm = self._get_llm(streaming=True, callbacks=[handler])
        
        # Stream response
        for token in llm.stream(prompt):
            yield token
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        try:
            stats = {
                "total_collections": len(self.collections),
                "collection_names": list(self.collections.keys()),
                "llm_provider": self.llm_provider,
                "vectordb_directory": self.vectordb_dir
            }
            
            # Get document counts for each collection
            collection_stats = {}
            for name, collection in self.collections.items():
                try:
                    # This might need adjustment based on your Chroma version
                    count = collection._collection.count()
                    collection_stats[name] = count
                except Exception as e:
                    collection_stats[name] = f"Error: {e}"
            
            stats["collection_document_counts"] = collection_stats
            return stats
            
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {"error": str(e)}

# Global instance
rag_service = RAGService() 