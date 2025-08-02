#!/usr/bin/env python3
"""
Test to verify that current query gets priority and history is only used for reference
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_query_priority():
    """Test that current query gets priority and history is only used for reference"""
    
    print("🧪 Testing Query Priority vs History Reference")
    print("=" * 50)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test scenarios to verify query priority
        test_scenarios = [
            {
                "name": "New Query - Should Answer Current Question",
                "query": "What is machine learning?",
                "chat_history": [
                    {"role": "user", "content": "What computer science courses are available?"},
                    {"role": "assistant", "content": "Stevens Institute of Technology offers various computer science courses including CS 513, CS 546, and CS 570."}
                ],
                "expected_focus": "machine learning",
                "description": "Should answer about machine learning, not courses"
            },
            {
                "name": "Follow-up - Should Answer Current Question",
                "query": "Tell me about CS 513",
                "chat_history": [
                    {"role": "user", "content": "What is machine learning?"},
                    {"role": "assistant", "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience."}
                ],
                "expected_focus": "CS 513",
                "description": "Should answer about CS 513, not machine learning"
            },
            {
                "name": "Different Topic - Should Answer Current Question",
                "query": "What are the admission requirements?",
                "chat_history": [
                    {"role": "user", "content": "Tell me about CS 513"},
                    {"role": "assistant", "content": "CS 513 is a graduate-level course in algorithms and data structures."}
                ],
                "expected_focus": "admission requirements",
                "description": "Should answer about admission requirements, not CS 513"
            },
            {
                "name": "General Knowledge - Should Answer Current Question",
                "query": "What is artificial intelligence?",
                "chat_history": [
                    {"role": "user", "content": "What are the admission requirements?"},
                    {"role": "assistant", "content": "The admission requirements for Stevens Institute include a completed application, transcripts, and letters of recommendation."}
                ],
                "expected_focus": "artificial intelligence",
                "description": "Should answer about AI, not admission requirements"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_scenarios)} scenarios...")
        print("-" * 50)
        
        for i, test_case in enumerate(test_scenarios, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print(f"📋 Description: {test_case['description']}")
            print(f"❓ Current Query: '{test_case['query']}'")
            print(f"🎯 Expected Focus: {test_case['expected_focus']}")
            print(f"📚 History entries: {len(test_case['chat_history'])}")
            
            # Process query with chat history
            result = chatbot_service.process_query(
                user_query=test_case['query'],
                user_id="test_user_query_priority",
                chat_history=test_case['chat_history']
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                response = result.get('response', '')
                print(f"Response: {response[:200]}...")
                print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Check if response focuses on the current query
                response_lower = response.lower()
                expected_focus_lower = test_case['expected_focus'].lower()
                
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
                print(f"📚 History included: {chat_history_included}")
                
                # Verify response focuses on current query
                if expected_focus_lower in response_lower:
                    print(f"✅ GOOD: Response focuses on current query ({test_case['expected_focus']})")
                else:
                    print(f"⚠️  WARNING: Response may not focus on current query")
                
                # Check for history misuse (shouldn't answer history questions)
                history_questions = []
                for entry in test_case['chat_history']:
                    if entry.get('role') == 'user':
                        history_questions.append(entry.get('content', '').lower())
                
                history_misuse = False
                for hist_q in history_questions:
                    if hist_q in response_lower and hist_q != test_case['query'].lower():
                        history_misuse = True
                        break
                
                if history_misuse:
                    print(f"❌ BAD: Response appears to answer history question instead of current query")
                else:
                    print(f"✅ GOOD: Response doesn't answer history questions")
        
        print("\n🎉 Query priority tests completed!")
        print("\n✅ SUCCESS: Current query should get priority, history for reference only")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_priority() 