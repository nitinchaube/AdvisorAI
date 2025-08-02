#!/usr/bin/env python3
"""
Enhanced example showing LangGraph workflow with Stevens Institute of Technology web search integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.langgraph_graph import LangGraphOrchestrator

async def main():
    """Demonstrate the enhanced LangGraph workflow"""
    
    print("🚀 Enhanced LangGraph Chatbot with Stevens Institute of Technology Web Search")
    print("=" * 70)
    
    try:
        # Initialize the orchestrator
        print("📦 Initializing LangGraph orchestrator...")
        orchestrator = LangGraphOrchestrator()
        print("✅ Orchestrator initialized successfully!")
        
        # Test queries that demonstrate different scenarios
        test_queries = [
            {
                "query": "What computer science courses are available?",
                "description": "Domain-specific query (should use Chroma, no web search needed)"
            },
            {
                "query": "What are the current admission requirements for 2024?",
                "description": "Time-sensitive query (should trigger web search)"
            },
            {
                "query": "How do I contact the admissions office?",
                "description": "Procedural query (should trigger web search)"
            },
            {
                "query": "Tell me about machine learning concepts",
                "description": "General knowledge query (should use general tool)"
            },
            {
                "query": "What is the latest news about Stevens Institute?",
                "description": "Current information query (should trigger web search)"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} different query scenarios...")
        print("-" * 70)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: {description}")
            print(f"Query: '{query}'")
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            
            # Process the query
            start_time = datetime.now()
            result = await orchestrator.process_query(query, user_id="test_user")
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            if result["success"]:
                print(f"✅ Success! (Processing time: {processing_time:.2f}s)")
                print(f"Answer: {result['answer'][:200]}...")
                
                # Show metadata
                metadata = result.get("metadata", {})
                print(f"Tools used: {metadata.get('tools_used', [])}")
                print(f"Collections searched: {metadata.get('collections_searched', [])}")
                print(f"Web search performed: {metadata.get('web_search_performed', False)}")
                print(f"Used general tool: {metadata.get('used_general_tool', False)}")
                
                if metadata.get("reasoning_result"):
                    reasoning = metadata["reasoning_result"]
                    print(f"Reasoning: {reasoning.get('reasoning', 'N/A')}")
                    print(f"Confidence: {reasoning.get('confidence', 'N/A')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            print("-" * 50)
        
        print("\n🎉 Enhanced workflow demonstration completed!")
        print("\nKey Features Demonstrated:")
        print("✅ Automatic query enhancement with 'Stevens Institute of Technology'")
        print("✅ Smart web search decision making based on query type")
        print("✅ Integration with Chroma vector database")
        print("✅ General knowledge handling")
        print("✅ ReACT-style reasoning workflow")
        print("✅ Parallel tool execution")
        print("✅ Comprehensive metadata tracking")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 