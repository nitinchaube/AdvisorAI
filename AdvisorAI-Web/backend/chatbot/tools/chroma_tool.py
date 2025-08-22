from typing import List, Dict, Any
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import hashlib
import json
import chromadb
from config.settings import settings
from core.llm_router import LLMRouter

class ChromaTool:
    """Tool for interacting with Chroma vector database collections using RAG service logic"""

    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.collections = self._load_collections()
        self.llm_router = LLMRouter()
        print(f"ChromaTool initialized with {len(self.collections)} collections: {list(self.collections.keys())}")

    def _load_collections(self) -> Dict[str, Chroma]:
        """Load all available Chroma collections using RAG service logic"""
        collections = {}
        if os.path.exists(settings.VECTORDB_DIR):
            print(f"Loading collections from: {settings.VECTORDB_DIR}")
            for folder in os.listdir(settings.VECTORDB_DIR):
                full_path = os.path.join(settings.VECTORDB_DIR, folder)
                if os.path.isdir(full_path):
                    try:
                        # Try direct ChromaDB client approach (RAG service logic)
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
                        # Fallback to simple Chroma approach
                        try:
                            chroma_wrapper = Chroma(
                                collection_name=folder,
                                persist_directory=full_path,
                                embedding_function=self.embedding_model
                            )
                            collections[folder] = chroma_wrapper
                            print(f"Successfully loaded collection using fallback: {folder}")
                        except Exception as fallback_error:
                            print(f"Fallback also failed for {folder}: {fallback_error}")
        else:
            print(f"VectorDB directory does not exist: {settings.VECTORDB_DIR}")
        
        return collections

    async def _ask_router_llm(self, user_query: str) -> List[str]:
        """Ask LLM which collections to search based on user query (RAG service logic)"""
        collections = list(self.collections.keys()) # Ensure this is up-to-date
        
        # If no collections are loaded, return empty list
        if not collections:
            print("No collections available, will use web search only")
            return []
        
        router_prompt = """
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
        """
        
        prompt = router_prompt.format(collections=collections, user_query=user_query)
        
        try:
            llm = self.llm_router.get_llm()
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
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

    async def _retrieve_from_collections(self, user_query: str, collection_names: List[str]) -> List[Document]:
        """Retrieve documents from specified collections and return top-k sorted results (RAG service logic)"""
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
                        k=settings.TOP_K_PER_COLLECTION
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
            
        top_docs = unique_docs[:settings.MAX_TOTAL_DOCS]
        print(f"Returning top {len(top_docs)} documents from {len(unique_docs)} unique documents")
        return top_docs

    async def search_collections(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Search across all available collections"""
        try:
            print(f"🔍 CHROMA: Searching collections for query: '{query}'")
            
            if not self.collections:
                print(f"⚠️  CHROMA: No collections available")
                return {
                    "documents": [],
                    "collections_searched": [],
                    "success": False,
                    "error": "No collections available"
                }
            
            # Use LLM to decide which collections to search
            selected_collections = await self._ask_router_llm(query)
            print(f"🎯 CHROMA: LLM selected collections: {selected_collections}")
            
            # Retrieve documents from selected collections
            all_documents = await self._retrieve_from_collections(query, selected_collections)
            
            print(f"✅ CHROMA: Found {len(all_documents)} documents from {len(selected_collections)} collections")
            
            # Convert documents to a format that can be serialized
            documents_data = []
            for doc in all_documents:
                documents_data.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "collection": doc.metadata.get("collection", "unknown")
                })
            
            return {
                "documents": documents_data,
                "collections_searched": selected_collections,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ CHROMA: Error searching collections: {str(e)}")
            return {
                "documents": [],
                "collections_searched": [],
                "success": False,
                "error": str(e)
            }

    def get_collection(self, collection_name: str):
        """Get a specific collection by name"""
        return self.collections.get(collection_name)

    def get_collection_names(self) -> List[str]:
        """Get list of available collection names"""
        return list(self.collections.keys())

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        stats = {}
        for name, collection in self.collections.items():
            try:
                count = collection._collection.count()
                stats[name] = {"document_count": count}
            except Exception as e:
                stats[name] = {"error": str(e)}
        return stats 