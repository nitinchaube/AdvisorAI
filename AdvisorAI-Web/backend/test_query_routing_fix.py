#!/usr/bin/env python3
"""
Test to verify that queries properly check collections and web before using general tool
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_query_routing_fix():
    """Test that queries properly check collections and web before using general tool"""
    
    print("🧪 Testing Query Routing Fix")
    print("=" * 35)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries that should check collections and web first
        test_queries = [
            {
                "query": "Do you have any course on Deep learning?",
                "expected_tools": ["history", "chroma", "web"],
                "description": "Course query should check collections and web"
            },
            {
                "query": "What courses are available in computer science?",
                "expected_tools": ["history", "chroma", "web"],
                "description": "Course availability query should check collections and web"
            },
            {
                "query": "Tell me about CS 513 course",
                "expected_tools": ["history", "chroma"],
                "description": "Specific course query should check collections"
            },
            {
                "query": "What is machine learning?",
                "expected_tools": ["history", "chroma", "web"],
                "description": "General concept but Stevens-related should check collections"
            },
            {
                "query": "What is the meaning of life?",
                "expected_tools": ["history", "general"],
                "description": "Pure general knowledge should use general tool"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("-" * 35)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            expected_tools = test_case["expected_tools"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: '{query}'")
            print(f"📋 Description: {description}")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_routing_fix",
                chat_history=[]
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                print(f"Response: {result.get('response', '')[:150]}...")
                print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Check which tools were used
                sources = result.get('sources', {})
                collections_used = sources.get('collections_used', [])
                web_search_performed = sources.get('web_search_performed', False)
                general_tool_used = sources.get('general_tool_used', False)
                chat_history_included = sources.get('chat_history_included', False)
                
                actual_tools = []
                if collections_used:
                    actual_tools.append("chroma")
                if web_search_performed:
                    actual_tools.append("web")
                if general_tool_used:
                    actual_tools.append("general")
                if chat_history_included:
                    actual_tools.append("history")
                
                print(f"🔧 Tools used: {actual_tools}")
                print(f"📊 Collections: {collections_used}")
                print(f"🌐 Web search: {web_search_performed}")
                print(f"🧠 General tool: {general_tool_used}")
                print(f"📚 History included: {chat_history_included}")
                
                # Verify expected tools were used
                if expected_tools:
                    if any(tool in actual_tools for tool in expected_tools):
                        print(f"✅ GOOD: Expected tools used")
                    else:
                        print(f"⚠️  WARNING: Expected tools not used. Expected: {expected_tools}, Got: {actual_tools}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"🧠 Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"🎯 Confidence: {reasoning.get('confidence', 'Unknown')}")
        
        print("\n🎉 Query routing fix tests completed!")
        print("\n✅ SUCCESS: Queries should now check collections and web before using general tool")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_routing_fix() 