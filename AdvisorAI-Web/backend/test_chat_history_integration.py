#!/usr/bin/env python3
"""
Test script to verify chat history integration for follow-up queries
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_chat_history_integration():
    """Test that chat history is properly integrated for follow-up queries"""
    
    print("🧪 Testing Chat History Integration")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test a sequence of queries to build history
        test_sequence = [
            {
                "query": "What computer science courses are available?",
                "expected_tools": ["chroma"]
            },
            {
                "query": "check again",
                "expected_tools": ["history", "chroma"],
                "is_follow_up": True
            },
            {
                "query": "tell me more about CS 513",
                "expected_tools": ["history", "chroma"],
                "is_follow_up": True
            },
            {
                "query": "What are the admission requirements?",
                "expected_tools": ["chroma"]
            },
            {
                "query": "check again",
                "expected_tools": ["history", "chroma"],
                "is_follow_up": True
            }
        ]
        
        print(f"\n🧪 Testing {len(test_sequence)} queries in sequence...")
        print("-" * 40)
        
        chat_history = []
        
        for i, test_case in enumerate(test_sequence, 1):
            query = test_case["query"]
            expected_tools = test_case.get("expected_tools", [])
            is_follow_up = test_case.get("is_follow_up", False)
            
            print(f"\n📝 Test {i}: '{query}'")
            if is_follow_up:
                print(f"🔄 This is a follow-up query")
            
            # Process query with chat history
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_history_integration",
                chat_history=chat_history
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
                
                print(f"Collections used: {collections_used}")
                print(f"Web search performed: {web_search_performed}")
                print(f"General tool used: {general_tool_used}")
                print(f"Chat history included: {chat_history_included}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"Confidence: {reasoning.get('confidence', 'Unknown')}")
                
                # Add to chat history for next iteration
                chat_history.append({
                    "query": query,
                    "response": result.get('response', ''),
                    "timestamp": i
                })
                
                # Verify expected tools were used
                actual_tools = []
                if collections_used:
                    actual_tools.append("chroma")
                if web_search_performed:
                    actual_tools.append("web")
                if general_tool_used:
                    actual_tools.append("general")
                if chat_history_included:
                    actual_tools.append("history")
                
                if expected_tools and actual_tools:
                    if any(tool in actual_tools for tool in expected_tools):
                        print(f"✅ GOOD: Expected tools used")
                    else:
                        print(f"⚠️  WARNING: Expected tools not used. Expected: {expected_tools}, Got: {actual_tools}")
        
        print("\n🎉 Chat history integration tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_history_integration() 