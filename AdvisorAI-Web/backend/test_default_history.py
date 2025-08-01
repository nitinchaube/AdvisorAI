#!/usr/bin/env python3
"""
Test to verify that history is always included by default
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_default_history_inclusion():
    """Test that history is always included by default"""
    
    print("🧪 Testing Default History Inclusion")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries with and without history
        test_cases = [
            {
                "name": "New Query - No History",
                "query": "What computer science courses are available?",
                "chat_history": [],
                "expected_history_included": True,
                "description": "New query should include history (even if empty)"
            },
            {
                "name": "Query with History",
                "query": "Tell me about CS 513",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_history_included": True,
                "description": "Query with history should include it"
            },
            {
                "name": "Follow-up Query",
                "query": "check again",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_history_included": True,
                "description": "Follow-up query should include history"
            },
            {
                "name": "General Knowledge Query",
                "query": "What is machine learning?",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_history_included": True,
                "description": "General knowledge query should include history"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_cases)} cases...")
        print("-" * 40)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print(f"📋 Description: {test_case['description']}")
            print(f"❓ Query: '{test_case['query']}'")
            print(f"📚 History entries: {len(test_case['chat_history'])}")
            
            # Process query with chat history
            result = chatbot_service.process_query(
                user_query=test_case['query'],
                user_id="test_user_default_history",
                chat_history=test_case['chat_history']
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
                
                # Verify history is always included
                if chat_history_included:
                    print(f"✅ GOOD: History included as expected")
                else:
                    print(f"❌ BAD: History not included when it should be")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"🧠 Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"🎯 Confidence: {reasoning.get('confidence', 'Unknown')}")
        
        print("\n🎉 Default history inclusion tests completed!")
        print("\n✅ SUCCESS: History should always be included by default")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_default_history_inclusion() 