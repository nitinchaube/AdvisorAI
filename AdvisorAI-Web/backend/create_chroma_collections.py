#!/usr/bin/env python3
"""
Script to create Chroma vector collections from JSON data files.
"""

import os
import json
import shutil
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ChromaCollectionBuilder:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./Data")
        self.vectordb_dir = os.getenv("VECTORDB_DIR", "./VectorDB")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        
        print(f"Chroma Collection Builder initialized")
        print(f"Data directory: {self.data_dir}")
        print(f"VectorDB directory: {self.vectordb_dir}")
    
    def create_collection_from_json(self, json_file_path: str, collection_name: str) -> bool:
        """Create a Chroma collection from a JSON file."""
        try:
            print(f"\n📁 Processing {json_file_path}...")
            
            # Read JSON file
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"❌ Error: {json_file_path} does not contain a list of objects")
                return False
            
            print(f"📊 Found {len(data)} items in {json_file_path}")
            
            # Create documents
            documents = []
            for idx, item in enumerate(data):
                # Convert item to text representation
                if isinstance(item, dict):
                    text_parts = []
                    for key, value in item.items():
                        if value is not None and value != "":
                            if isinstance(value, (list, dict)):
                                text_parts.append(f"{key}: {json.dumps(value, indent=2)}")
                            else:
                                text_parts.append(f"{key}: {value}")
                    text = "\n".join(text_parts)
                else:
                    text = str(item)
                
                # Create metadata
                metadata = {
                    "source_file": os.path.basename(json_file_path),
                    "index": idx,
                    "collection": collection_name,
                    "keys": ",".join(item.keys()) if isinstance(item, dict) else "simple_data"
                }
                
                # Create document
                doc = Document(page_content=text, metadata=metadata)
                documents.append(doc)
            
            print(f"📝 Created {len(documents)} documents")
            
            # Create collection directory
            collection_path = os.path.join(self.vectordb_dir, collection_name)
            
            # Remove existing collection if it exists
            if os.path.exists(collection_path):
                print(f"🗑️  Removing existing collection: {collection_name}")
                shutil.rmtree(collection_path)
            
            # Create new collection
            print(f"🏗️  Creating collection: {collection_name}")
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                collection_name=collection_name,
                persist_directory=collection_path
            )
            
            # Persist the collection
            vector_store.persist()
            
            print(f"✅ Successfully created collection '{collection_name}' with {len(documents)} documents")
            return True
            
        except Exception as e:
            print(f"❌ Error creating collection '{collection_name}': {str(e)}")
            return False
    
    def build_all_collections(self) -> Dict[str, bool]:
        """Build all collections from JSON files in the data directory."""
        results = {}
        
        if not os.path.exists(self.data_dir):
            print(f"❌ Data directory not found: {self.data_dir}")
            return results
        
        # Get all JSON files
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        
        if not json_files:
            print(f"❌ No JSON files found in {self.data_dir}")
            return results
        
        print(f"🔍 Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            collection_name = os.path.splitext(json_file)[0]
            json_file_path = os.path.join(self.data_dir, json_file)
            success = self.create_collection_from_json(json_file_path, collection_name)
            results[collection_name] = success
        
        return results

def main():
    """Main function to run the collection builder."""
    print("🚀 Starting Chroma Collection Builder")
    print("=" * 50)
    
    builder = ChromaCollectionBuilder()
    
    # Check existing collections
    existing_collections = []
    if os.path.exists(builder.vectordb_dir):
        existing_collections = [d for d in os.listdir(builder.vectordb_dir) 
                              if os.path.isdir(os.path.join(builder.vectordb_dir, d))]
    
    if existing_collections:
        print(f"\n📋 Existing collections found: {existing_collections}")
        print("\nOptions:")
        print("1. Rebuild all collections (will delete existing ones)")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == "1":
            print("\n🔄 Rebuilding all collections...")
            results = builder.build_all_collections()
            
            print("\n📋 Results:")
            for collection_name, success in results.items():
                status = "✅ Success" if success else "❌ Failed"
                print(f"  • {collection_name}: {status}")
        else:
            print("👋 Exiting...")
    else:
        print("\n🔄 No existing collections found. Creating new ones...")
        results = builder.build_all_collections()
        
        print("\n�� Results:")
        for collection_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  • {collection_name}: {status}")

if __name__ == "__main__":
    main()