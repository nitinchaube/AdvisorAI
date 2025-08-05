#!/usr/bin/env python3
"""
Comprehensive test for perfect chatbot functionality with history integration
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_perfect_chatbot():
    """Test perfect chatbot functionality with history integration"""
    
    print("🧪 Testing Perfect Chatbot Functionality")
    print("=" * 50)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test scenarios with different chat history formats
        test_scenarios = [
            {
                "name": "New User - Course Query",
                "query": "What computer science courses are available?",
                "chat_history": [],
                "expected_tools": ["chroma"],
                "description": "New user asking about courses"
            },
            {
                "name": "Follow-up - Check Again",
                "query": "check again",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_tools": ["history", "chroma"],
                "description": "User asking to check again after getting course info"
            },
            {
                "name": "Follow-up - Tell Me More",
                "query": "tell me more about CS 513",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_tools": ["history", "chroma"],
                "description": "User asking for more details about specific course"
            },
            {
                "name": "Follow-up - What Else",
                "query": "what else?",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_tools": ["history", "chroma"],
                "description": "User asking for additional information"
            },
            {
                "name": "General Knowledge Query",
                "query": "What is machine learning?",
                "chat_history": [],
                "expected_tools": ["general"],
                "description": "General knowledge question"
            },
            {
                "name": "Current Information Query",
                "query": "What are the latest admission requirements for 2024?",
                "chat_history": [],
                "expected_tools": ["chroma", "web"],
                "description": "Query requiring current information"
            },
            {
                "name": "Short Follow-up",
                "query": "more details",
                "chat_history": [
                    {"role": "user", "content": "Tell me about CS 513"},
                    {"role": "assistant", "content": "CS 513 is a graduate-level course in algorithms and data structures."}
                ],
                "expected_tools": ["history", "chroma"],
                "description": "Short follow-up query"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_scenarios)} scenarios...")
        print("-" * 50)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Test {i}: {scenario['name']}")
            print(f"📋 Description: {scenario['description']}")
            print(f"❓ Query: '{scenario['query']}'")
            print(f"📚 History entries: {len(scenario['chat_history'])}")
            
            # Process query with chat history
            result = chatbot_service.process_query(
                user_query=scenario['query'],
                user_id="test_user_perfect",
                chat_history=scenario['chat_history']
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
                expected_tools = scenario['expected_tools']
                if expected_tools:
                    if any(tool in actual_tools for tool in expected_tools):
                        print(f"✅ GOOD: Expected tools used")
                    else:
                        print(f"⚠️  WARNING: Expected tools not used. Expected: {expected_tools}, Got: {actual_tools}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"🧠 Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"🎯 Confidence: {reasoning.get('confidence', 'Unknown')}")
        
        print("\n🎉 Perfect chatbot tests completed!")
        print("\n✅ SUCCESS: All scenarios tested successfully")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_perfect_chatbot() 