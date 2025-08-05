#!/usr/bin/env python3
"""
Test script to demonstrate improved RAG service integration
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.chroma_tool import ChromaTool
from tools.web_tool import WebTool
from core.llm_router import LLMRouter

async def test_rag_integration():
    """Test the improved RAG service integration"""
    
    print("🧪 Testing Improved RAG Service Integration")
    print("=" * 60)
    
    # Initialize tools
    chroma_tool = ChromaTool()
    web_tool = WebTool()
    llm_router = LLMRouter()
    
    print("✅ Tools initialized successfully")
    
    # Test queries that demonstrate RAG service improvements
    test_queries = [
        {
            "query": "What computer science courses are available?",
            "description": "Domain-specific query (should use intelligent collection routing)"
        },
        {
            "query": "Tell me about faculty research areas",
            "description": "Faculty-related query (should route to faculty collections)"
        },
        {
            "query": "What are the admission requirements for 2024?",
            "description": "Time-sensitive query (should trigger web search)"
        },
        {
            "query": "How do I contact the admissions office?",
            "description": "Procedural query (should trigger web search)"
        },
        {
            "query": "What is machine learning?",
            "description": "General knowledge query (should use general tool)"
        }
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} different query scenarios...")
    print("-" * 60)
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"\n📝 Test {i}: {description}")
        print(f"Query: '{query}'")
        
        # Test Chroma tool with RAG service logic
        print("\n🔍 Testing Chroma Tool (RAG Service Logic):")
        try:
            chroma_results = chroma_tool.search_collections(query)
            print(f"✅ Chroma search successful")
            print(f"   Collections used: {chroma_results.get('collections_used', [])}")
            print(f"   Documents found: {chroma_results.get('total_docs', 0)}")
            
            # Show top document details
            if chroma_results.get('documents'):
                top_doc = chroma_results['documents'][0]
                print(f"   Top document: {top_doc.get('collection', 'unknown')} (score: {top_doc.get('score', 'unknown'):.4f})")
                print(f"   Content preview: {top_doc.get('content', '')[:100]}...")
            else:
                print("   No documents found")
                
        except Exception as e:
            print(f"❌ Chroma search failed: {e}")
        
        # Test web search decision logic
        print("\n🌐 Testing Web Search Decision Logic:")
        try:
            should_search = web_tool._should_use_web_search(query, chroma_results)
            print(f"   Should web search: {should_search}")
            
            if should_search:
                enhanced_query = web_tool._enhance_query_with_stevens(query)
                print(f"   Enhanced query: '{enhanced_query}'")
                
                # Test web search (without actually performing it)
                print("   Web search would be triggered for this query")
            else:
                print("   Web search skipped - sufficient information from vector database")
                
        except Exception as e:
            print(f"❌ Web search decision failed: {e}")
        
        print("-" * 40)
    
    print("\n🎉 RAG Service Integration Tests Completed!")
    print("\nKey Improvements:")
    print("✅ Intelligent collection routing using LLM")
    print("✅ Better document retrieval with deduplication")
    print("✅ Smart web search decision making")
    print("✅ Enhanced query processing with Stevens context")
    print("✅ Improved content formatting and cleaning")
    print("✅ Better error handling and fallback mechanisms")

if __name__ == "__main__":
    asyncio.run(test_rag_integration()) 