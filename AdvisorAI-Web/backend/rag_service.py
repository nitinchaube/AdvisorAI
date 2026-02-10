import os
import json
import time
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import random

# Import web scraper
from web_scrapper import scrape_web_content

load_dotenv()

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb_dir = os.getenv("VECTORDB_DIR", "./chroma")

def load_vector_store(collection_name):
    collection_path = os.path.join(vectordb_dir, collection_name)
    return Chroma(
        collection_name=collection_name,
        persist_directory=collection_path,
        embedding_function=embedding_model
    )

class RAGService:
    def __init__(self):
        # Embeddings
        embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
        
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        self.google_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Vector DB Configuration
        self.vectordb_dir = os.getenv("VECTORDB_DIR", "./VectorDB")
        
        # Retrieval Configuration
        self.top_k_per_collection = int(os.getenv("TOP_K_PER_COLLECTION", "5"))
        self.max_total_docs = int(os.getenv("MAX_TOTAL_DOCS", "5"))
        
        # Web Search Configuration
        self.web_search_enabled = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
        self.web_search_results = int(os.getenv("WEB_SEARCH_RESULTS", "3"))
        
        # API Configuration
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:5003")
        
        # Load all collections
        self.collections = self._load_all_collections()
        
        print(f"RAG Service initialized with {len(self.collections)} collections: {list(self.collections.keys())}")
        print(f"Configuration: top_k={self.top_k_per_collection}, max_docs={self.max_total_docs}, web_search={self.web_search_enabled}")
    
    def _load_all_collections(self) -> Dict[str, Chroma]:
        """Load all vectorized collections from directory"""
        collections = {}
        if os.path.exists(self.vectordb_dir):
            for folder in os.listdir(self.vectordb_dir):
                full_path = os.path.join(self.vectordb_dir, folder)
                if os.path.isdir(full_path):
                    try:
                        # Try direct ChromaDB client approach
                        print(f"Trying to load collection {folder} with direct client...")
                        client = chromadb.PersistentClient(path=full_path)
                        
                        # Get collection info
                        collection_info = client.list_collections()
                        print(f"Available collections in {folder}: {[c.name for c in collection_info]}")
                        
                        # Try to get the collection
                        try:
                            collection = client.get_collection(name=folder)
                            count = collection.count()
                            print(f"Collection {folder} has {count} documents")
                            
                            if count > 0:
                                # Create a Chroma wrapper with the client
                                chroma_wrapper = Chroma(
                                    client=client,
                                    collection_name=folder,
                                    embedding_function=self.embedding_model
                                )
                                collections[folder] = chroma_wrapper
                                print(f"Successfully loaded collection: {folder}")
                            else:
                                print(f"Collection {folder} has no documents, skipping")
                                
                        except Exception as get_error:
                            print(f"Error getting collection {folder}: {get_error}")
                            # Try with default collection name
                            try:
                                collection = client.get_collection()
                                count = collection.count()
                                print(f"Default collection has {count} documents")
                                
                                if count > 0:
                                    chroma_wrapper = Chroma(
                                        client=client,
                                        embedding_function=self.embedding_model
                                    )
                                    collections[folder] = chroma_wrapper
                                    print(f"Successfully loaded default collection for {folder}")
                                else:
                                    print(f"Default collection has no documents, skipping")
                                    
                            except Exception as default_error:
                                print(f"Error getting default collection for {folder}: {default_error}")
                                
                    except Exception as e:
                        print(f"Error loading collection {folder}: {e}")
                        
        return collections
    
    def _get_llm(self, streaming: bool = False, callbacks: List = None):
        """Get LLM instance based on provider"""
        if self.llm_provider == "gemini":
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.google_api_key,
                streaming=streaming,
                callbacks=callbacks or []
            )
        elif self.llm_provider == "openai":
            model_name = os.getenv("OPENAI_MODEL", "gpt-4")
            return ChatOpenAI(
                model=model_name,
                openai_api_key=self.openai_api_key,
                streaming=streaming,
                callbacks=callbacks or []
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def _ask_router_llm(self, user_query: str) -> List[str]:
        """Ask LLM which collections to search based on user query"""
        collections = list(self.collections.keys())
        
        # If no collections are loaded, return empty list
        if not collections:
            print("No collections available, will use web search only")
            return []
        
        router_prompt = os.getenv("ROUTER_PROMPT", """
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
        - If no collections are relevant, return: []
        """)
        
        prompt = router_prompt.format(collections=collections, user_query=user_query)
        
        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            if response.content is None:
                print("LLM returned None content, falling back")
                return collections  # or []
            selected_collections = json.loads(response.content.strip() or '[]')
            
            # Validate that selected collections exist
            valid_collections = [col for col in selected_collections if col in collections]
            if not valid_collections:
                print("No valid collections selected, using all available collections")
                return collections
            
            print(f"Router selected collections: {valid_collections}")
            return valid_collections
            
        except Exception as e:
            print(f"Error in router LLM: {e}")
            print("Falling back to all available collections")
            return collections
    
    def _retrieve_from_collections(self, user_query: str, collection_names: List[str]) -> List[Document]:
        """Retrieve documents from specified collections and return top-k sorted results"""
        all_docs = []
        
        # If no collections specified, return empty list
        if not collection_names:
            print("No collections specified for retrieval")
            return []
        
        for collection_name in collection_names:
            if collection_name in self.collections:
                try:
                    vector_store = self.collections[collection_name]
                    # Get more docs than needed for better sorting
                    docs_with_scores = vector_store.similarity_search_with_score(
                        user_query, 
                        k=self.top_k_per_collection
                    )
                    
                    for doc, score in docs_with_scores:
                        doc.metadata["collection"] = collection_name
                        doc.metadata["source"] = "vector_db"
                        doc.metadata["similarity_score"] = score
                    
                    all_docs.extend([doc for doc, _ in docs_with_scores])
                    print(f"Retrieved {len(docs_with_scores)} docs from {collection_name}")
                    
                except Exception as e:
                    print(f"Error retrieving from {collection_name}: {e}")
            else:
                print(f"Collection {collection_name} not found in loaded collections")
        
        # Sort by similarity score (lower is better for cosine similarity)
        all_docs.sort(key=lambda x: x.metadata.get("similarity_score", 1e6))
        
        # Remove duplicates based on content hash
        seen_contents = set()
        unique_docs = []
        for doc in all_docs:
            content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            if content_hash not in seen_contents:
                unique_docs.append(doc)
                seen_contents.add(content_hash)
            
        top_3_docs = unique_docs[:3]
        print(f"Returning top {len(top_3_docs)} documents from {len(unique_docs)} unique documents")
        return top_3_docs
    
    def _format_chat_history(self, chat_history: List[Dict]) -> str:
        """Format chat history for context"""
        if not chat_history:
            return ""
        
        formatted_history = []
        for msg in chat_history[-5:]:  # Last 5 messages to avoid context overflow
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                formatted_history.append(f"User: {content}")
            elif role == "assistant":
                formatted_history.append(f"Assistant: {content}")
        
        return "\n".join(formatted_history)
    
    def _clean_markdown_response(self, response: str) -> str:
        """Clean and format markdown response for better display"""
        if not response:
            return ""
        
        # Remove excessive markdown formatting
        response = re.sub(r'\*\*(.*?)\*\*', r'**\1**', response)  # Keep bold
        response = re.sub(r'\*(.*?)\*', r'*\1*', response)  # Keep italic
        
        # Clean up excessive newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Ensure proper spacing around lists
        response = re.sub(r'(\n)(\d+\.)', r'\n\n\2', response)
        response = re.sub(r'(\n)(\* )', r'\n\n\2', response)
        
        return response.strip()
    
    def _should_use_web_search(self, user_query: str, docs: List[Document]) -> bool:
        """Smart decision on whether to use web search"""
        
        query_lower = user_query.lower()
        
        # Always use web search for current/recent information queries
        current_time_indicators = [
            "current", "recent", "latest", "now", "today", "this year", "2024", "2025",
            "upcoming", "next", "future", "new", "announcement", "update", "when", "deadline",
            "application", "admission", "enrollment", "registration", "semester", "term"
        ]
        
        if any(indicator in query_lower for indicator in current_time_indicators):
            print(f"Web search triggered: Query contains time indicator")
            return True
        
        # Always use web search for specific technical or procedural questions
        technical_indicators = [
            "api", "endpoint", "database", "server", "deployment", "configuration",
            "setup", "installation", "tutorial", "guide", "how to", "process", "procedure",
            "apply", "register", "enroll", "submit", "contact", "email", "phone", "address"
        ]
        
        if any(indicator in query_lower for indicator in technical_indicators):
            print(f"Web search triggered: Query contains technical/procedural indicator")
            return True
        
        # Use web search for questions that likely need current information
        current_info_indicators = [
            "what is", "tell me about", "information about", "details about", "latest",
            "current status", "available", "offered", "schedule", "timing", "location",
            "requirements", "prerequisites", "cost", "tuition", "fees", "scholarship"
        ]
        
        if any(indicator in query_lower for indicator in current_info_indicators):
            print(f"Web search triggered: Query likely needs current information")
            return True
        
        # If we have good documents, don't web search (but be less strict)
        if docs and len(docs) > 0:
            # Check if any document has very good similarity score (more strict threshold)
            very_good_docs = [doc for doc in docs if doc.metadata.get("similarity_score", 1.0) < 0.6]
            if very_good_docs:
                print(f"No web search: Found very good documents (score < 0.6)")
                return False
            else:
                # If we have documents but they're not very good, still consider web search
                print(f"Web search considered: Documents found but similarity scores not very good")
                return True
        
        # If no documents found, definitely use web search
        if not docs or len(docs) == 0:
            print(f"Web search triggered: No documents found")
            return True
        
        # Default to web search for better coverage
        print(f"Web search triggered: Default case for better coverage")
        return True
    
    def _build_context_prompt(self, docs: List[Document], user_query: str, 
                             user_info: str = None, web_content: str = None,
                             chat_history: str = None) -> str:
        """Build context-aware prompt for LLM"""
        
        # Build context from available information
        context_parts = []
        if docs and len(docs) > 0:
            context_parts.append("Available Information:")
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[{i}]: {doc.page_content}")
        else:
            context_parts.append("Available Information: No relevant information found.")
        
        # Add web content if available
        if web_content:
            context_parts.append(f"\nAdditional Web Information:\n{web_content}")
        
        context = "\n\n".join(context_parts)
        
        # Build user context
        user_context = ""
        if user_info:
            user_context = f"\nUser Profile Information:\n{user_info}"
        
        # Build chat history context
        chat_context = ""
        if chat_history:
            chat_context = f"\nRecent Conversation:\n{chat_history}"
        
        # Get prompt template from environment or use default
        prompt_template = os.getenv("RAG_PROMPT_TEMPLATE", """
You are a helpful academic advisor for Stevens Institute of Technology. Your goal is to provide comprehensive, accurate, and useful information to help students with their questions.

{user_context}{chat_context}

Available Information:
{context}

User Query: {user_query}

Instructions:
1. Provide a complete and helpful answer to the user's question using the available information above.
2. If the information is available in the context, provide it directly and comprehensively.
3. If you have partial information, provide what you know and mention what additional details might be helpful.
4. If the answer is not present in the context, provide a helpful response and suggest where they might find more information (e.g., "For the most current information, you can check the Stevens website at [specific URL]").
5. Be conversational and helpful - don't just say "I don't know" without offering alternatives.
6. If the user asks about their personal information, use their profile data if available.
7. Include relevant links or specific resources when appropriate.
8. If you're providing information from web sources, include the source URL for credibility.

Response:
""")
        
        return prompt_template.format(
            user_context=user_context,
            chat_context=chat_context,
            context=context,
            user_query=user_query
        )
    
    def _check_needs_web_search(self, llm_response: str) -> bool:
        """Check if LLM response indicates need for web search"""
        web_search_indicators = os.getenv("WEB_SEARCH_INDICATORS", 
            "i need to search the web,i need to do a web search,i don't have information,i don't have access to,i cannot provide,i'm unable to,i don't have recent,my training data,i don't have current,i'm not aware of,i don't have specific,i cannot answer,i don't have details,i'm not familiar with,i don't have up-to-date,web search,search the web,i don't have enough information,i apologize,i'm sorry,i don't know,i cannot find,i don't have access,i don't have the specific,i don't have current information,i don't have recent information,i don't have the latest,i don't have the most recent,i don't have the most current,i don't have the most up-to-date,i don't have the most recent information,i don't have the most current information,i don't have the most up-to-date information"
        ).split(",")
        
        response_lower = llm_response.lower()
        
        # Check for explicit indicators
        if any(indicator in response_lower for indicator in web_search_indicators):
            print(f"Web search triggered by LLM response: Contains explicit indicator")
            return True
        
        # Check for short/unsatisfactory responses
        if len(llm_response.strip()) < 100:
            print(f"Web search triggered by LLM response: Response too short ({len(llm_response)} chars)")
            return True
        
        # Check for responses that seem uncertain
        uncertainty_indicators = [
            "i think", "i believe", "probably", "maybe", "possibly", "likely",
            "as far as i know", "to the best of my knowledge", "i'm not entirely sure",
            "i'm not completely sure", "i'm not certain", "i'm not positive"
        ]
        
        if any(indicator in response_lower for indicator in uncertainty_indicators):
            print(f"Web search triggered by LLM response: Contains uncertainty indicator")
            return True
        
        return False
    
    def _get_user_info_from_api(self, user_id: str) -> str:
        """Get user information from database API"""
        try:
            api_url = f"{self.api_base_url}/api/user/profile"
            headers = {"Authorization": f"Bearer {user_id}"}  # This should be a proper JWT token
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get("success") and user_data.get("profile"):
                    profile = user_data["profile"]
                    
                    # Format user data for context
                    user_info_parts = []
                    for key, value in profile.items():
                        if key not in ['resume-data', 'resume-text', 'uid', 'createdAt', 'updatedAt'] and value:
                            if isinstance(value, (list, dict)):
                                user_info_parts.append(f"{key}: {json.dumps(value, indent=2)}")
                            else:
                                user_info_parts.append(f"{key}: {value}")
                    
                    return "\n".join(user_info_parts)
                else:
                    print(f"No profile data found for user {user_id}")
                    return ""
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
            
            # Step 2: Format chat history
            formatted_chat_history = self._format_chat_history(chat_history or [])
            
            # Step 3: Check if we have any collections available
            if not self.collections:
                print("No collections available, using web search only")
                return self._handle_web_search_only(user_query, user_info, formatted_chat_history, start_time)
            
            # Step 4: Ask LLM which collections to search
            selected_collections = self._ask_router_llm(user_query)
            
            # Step 5: Retrieve documents from selected collections (top-k sorted)
            docs = self._retrieve_from_collections(user_query, selected_collections)
            print(f"Retrieved {len(docs)} documents from collections")
            
            # Step 6: Smart web search decision
            web_search_performed = False
            web_search_error = None
            
            # Check if we should use web search based on query and available docs
            should_web_search = self._should_use_web_search(user_query, docs)
            
            if self.web_search_enabled and should_web_search:
                print("Smart decision: Using web search for current/recent information...")
                web_search_performed = True
                
                try:
                    # Perform web search
                    search_query = user_query + " Stevens Institute of Technology"
                    web_content = scrape_web_content(search_query, num_results=self.web_search_results)
                    
                    # Build enhanced prompt with web content
                    enhanced_prompt = os.getenv("WEB_ENHANCED_PROMPT_TEMPLATE", """You are a helpful academic advisor for Stevens Institute of Technology. Your goal is to provide comprehensive, accurate, and useful information to help students with their questions.

{user_context}{chat_context}

Available Information:
{context}

Additional Web Information for the query "{user_query}":
{web_content}

Instructions:
1. Provide a complete and helpful answer using both the available information and web information above.
2. Synthesize information from both sources to give the most comprehensive answer possible.
3. If there are conflicting information sources, mention this and provide both perspectives.
4. Include specific details, dates, requirements, or other concrete information when available.
5. Include relevant links or sources for credibility and further reference.
6. Be conversational and helpful - provide actionable information rather than just directing users to websites.
7. If you're providing information from web sources, include the source URL for credibility.

Response:
""").format(
                        user_context=f"\nUser Profile Information:\n{user_info}" if user_info else "",
                        chat_context=f"\nRecent Conversation:\n{formatted_chat_history}" if formatted_chat_history else "",
                        context="\n\n".join([f"[{i+1}]: {doc.page_content}" for i, doc in enumerate(docs)]) if docs else "No relevant information found.",
                        user_query=user_query,
                        web_content=web_content
                    )
                    
                    # Get final response with web content
                    llm = self._get_llm()
                    final_response = llm.invoke(enhanced_prompt).content
                    final_response = self._clean_markdown_response(final_response)
                    
                    return {
                        "response": final_response,
                        "processing_time": time.time() - start_time,
                        "sources": {
                            "collections_used": selected_collections,
                            "documents_retrieved": len(docs),
                            "web_search_performed": web_search_performed,
                            "user_info_included": bool(user_info),
                            "chat_history_included": bool(formatted_chat_history),
                            "top_documents": [
                                {
                                    "collection": doc.metadata.get("collection"),
                                    "score": doc.metadata.get("similarity_score"),
                                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                                }
                                for doc in docs[:3]  # Top 3 documents
                            ] if docs else []
                        }
                    }
                    
                except Exception as e:
                    print(f"Web search failed: {e}")
                    web_search_error = str(e)
                    # Fall through to normal processing
            
            # Step 7: Build initial prompt and get LLM response
            initial_prompt = self._build_context_prompt(docs, user_query, user_info, None, formatted_chat_history)
            llm = self._get_llm()
            initial_response = llm.invoke(initial_prompt).content
            initial_response = self._clean_markdown_response(initial_response)
            
            # Step 8: Check if web search is needed based on response
            if self.web_search_enabled and not web_search_performed and self._check_needs_web_search(initial_response):
                print("LLM response indicates need for web search. Getting additional information...")
                web_search_performed = True
                
                try:
                    # Perform web search
                    search_query = user_query + " Stevens Institute of Technology"
                    web_content = scrape_web_content(search_query, num_results=self.web_search_results)
                    
                    # Build enhanced prompt with web content
                    enhanced_prompt = os.getenv("WEB_ENHANCED_PROMPT_TEMPLATE", """You are a helpful academic advisor for Stevens Institute of Technology. Your goal is to provide comprehensive, accurate, and useful information to help students with their questions.

Your initial response was: {initial_response}

Additional web information for the query "{user_query}":
{web_content}

{user_context}{chat_context}

Instructions:
1. Review your initial response and the additional web information.
2. Provide a comprehensive answer that incorporates both your initial knowledge and the web information.
3. If the web information adds valuable details, integrate them into your response.
4. If the web information doesn't add value, stick with your original response but make it more helpful and detailed.
5. Include specific details, dates, requirements, or other concrete information when available.
6. Include relevant links or sources for credibility and further reference.
7. Be conversational and helpful - provide actionable information rather than just directing users to websites.

Response:
""").format(
                        initial_response=initial_response,
                        user_query=user_query,
                        web_content=web_content,
                        user_context=f"\nUser Profile Information:\n{user_info}" if user_info else "",
                        chat_context=f"\nRecent Conversation:\n{formatted_chat_history}" if formatted_chat_history else ""
                    )
                    
                    # Get final response with web content
                    final_response = llm.invoke(enhanced_prompt).content
                    final_response = self._clean_markdown_response(final_response)
                    
                    return {
                        "response": final_response,
                        "processing_time": time.time() - start_time,
                        "sources": {
                            "collections_used": selected_collections,
                            "documents_retrieved": len(docs),
                            "web_search_performed": web_search_performed,
                            "user_info_included": bool(user_info),
                            "chat_history_included": bool(formatted_chat_history),
                            "top_documents": [
                                {
                                    "collection": doc.metadata.get("collection"),
                                    "score": doc.metadata.get("similarity_score"),
                                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                                }
                                for doc in docs[:3]  # Top 3 documents
                            ] if docs else []
                        }
                    }
                    
                except Exception as e:
                    print(f"Web search failed: {e}")
                    web_search_error = str(e)
                    return {
                        "response": initial_response,
                        "processing_time": time.time() - start_time,
                        "sources": {
                            "collections_used": selected_collections,
                            "documents_retrieved": len(docs),
                            "web_search_performed": web_search_performed,
                            "web_search_error": web_search_error,
                            "user_info_included": bool(user_info),
                            "chat_history_included": bool(formatted_chat_history),
                            "top_documents": [
                                {
                                    "collection": doc.metadata.get("collection"),
                                    "score": doc.metadata.get("similarity_score"),
                                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                                }
                                for doc in docs[:3]  # Top 3 documents
                            ] if docs else []
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
                        "web_search_performed": web_search_performed,
                        "user_info_included": bool(user_info),
                        "chat_history_included": bool(formatted_chat_history),
                        "top_documents": [
                            {
                                "collection": doc.metadata.get("collection"),
                                "score": doc.metadata.get("similarity_score"),
                                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                            }
                            for doc in docs[:3]  # Top 3 documents
                        ] if docs else []
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
    
    def _handle_web_search_only(self, user_query: str, user_info: str, formatted_chat_history: str, start_time: float) -> Dict:
        """Handle queries when no collections are available - use web search only"""
        try:
            print("Using web search only since no collections are available")
            
            # Perform web search
            search_query = user_query + " Stevens Institute of Technology"
            web_content = scrape_web_content(search_query, num_results=self.web_search_results)
            
            # Build prompt for web search only
            web_only_prompt = os.getenv("WEB_ONLY_PROMPT_TEMPLATE", """
You are a helpful academic advisor for Stevens Institute of Technology. Your goal is to provide comprehensive, accurate, and useful information to help students with their questions.

{user_context}
Chat History: 
{chat_context}

Web Information for the query "{user_query}":
{web_content}

User Query: {user_query}

Instructions:
1. Provide a complete and helpful answer to the user's question using the web information above.
2. If the information is available in the web content, provide it directly and comprehensively.
3. If you have partial information, provide what you know and mention what additional details might be helpful.
4. Include specific details, dates, requirements, or other concrete information when available.
5. Include relevant links or sources for credibility and further reference.
6. Be conversational and helpful - provide actionable information rather than just directing users to websites.
7. If the user asks about their personal information, use their profile data if available.
8. If the answer is not present in the web content, provide a helpful response and suggest where they might find more information.

Response:
""")
            
            # Get response
            llm = self._get_llm()
            response = llm.invoke(web_only_prompt).content
            response = self._clean_markdown_response(response)
            
            return {
                "response": response,
                "processing_time": time.time() - start_time,
                "sources": {
                    "collections_used": [],
                    "documents_retrieved": 0,
                    "web_search_performed": True,
                    "user_info_included": bool(user_info),
                    "chat_history_included": bool(formatted_chat_history),
                    "top_documents": [],
                    "note": "No collections available, using web search only"
                }
            }
            
        except Exception as e:
            print(f"Web search only failed: {e}")
            return {
                "response": f"I apologize, but I'm currently unable to access my knowledge base or search the web. Please try again later or contact support if the issue persists.",
                "error": True,
                "processing_time": time.time() - start_time,
                "sources": {
                    "collections_used": [],
                    "documents_retrieved": 0,
                    "web_search_performed": False,
                    "user_info_included": bool(user_info),
                    "chat_history_included": bool(formatted_chat_history),
                    "top_documents": [],
                    "error": str(e)
                }
            }
    
    def stream_query(self, user_query: str, user_id: str = None,
                    chat_history: List[Dict] = None):
        """Stream query response"""
        
        # Get user info
        user_info = ""
        if user_id:
            user_info = self._get_user_info_from_api(user_id)
        
        # Format chat history
        formatted_chat_history = self._format_chat_history(chat_history or [])
        
        # Get collections and documents
        selected_collections = self._ask_router_llm(user_query)
        docs = self._retrieve_from_collections(user_query, selected_collections)
        
        # Build prompt
        prompt = self._build_context_prompt(docs, user_query, user_info, None, formatted_chat_history)
        
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
                "vectordb_directory": self.vectordb_dir,
                "top_k_per_collection": self.top_k_per_collection,
                "max_total_docs": self.max_total_docs,
                "web_search_enabled": self.web_search_enabled
            }
            
            # Get document counts for each collection
            collection_stats = {}
            for name, collection in self.collections.items():
                try:
                    if collection._collection is not None:
                        count = collection._collection.count()
                    else:
                        count = 0
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