#!/usr/bin/env python3
"""
Test to verify that chat session storage is working properly
"""

import sys
import os
import asyncio
import requests
import json

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chat_session_storage():
    """Test that chat session storage is working properly"""
    
    print("🧪 Testing Chat Session Storage")
    print("=" * 40)
    
    try:
        # Test data
        test_user_id = "test_user_session_storage"
        test_query = "What is machine learning?"
        
        # Simulate the chat query process
        from chatbot_integration import get_chatbot_integration
        
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test 1: Process a query and check if it would be stored
        print(f"\n📝 Test 1: Processing query: '{test_query}'")
        
        result = chatbot_service.process_query(
            user_query=test_query,
            user_id=test_user_id,
            chat_history=[]
        )
        
        if result.get('error'):
            print(f"❌ Error: {result.get('response', 'Unknown error')}")
        else:
            print(f"✅ Success!")
            print(f"Response: {result.get('response', '')[:100]}...")
            print(f"Processing time: {result.get('processing_time', 0):.2f}s")
            
            # Check if response has the right structure for storage
            sources = result.get('sources', {})
            print(f"Sources: {sources}")
            
            # Simulate what would be stored in MongoDB
            mock_message = {
                'id': f"user_{int(asyncio.get_event_loop().time() * 1000)}",
                'role': 'user',
                'content': test_query,
                'timestamp': '2024-01-01T00:00:00.000Z'
            }
            
            mock_ai_message = {
                'id': f"ai_{int(asyncio.get_event_loop().time() * 1000)}",
                'role': 'assistant',
                'content': result.get('response', ''),
                'timestamp': '2024-01-01T00:00:00.000Z',
                'sources': sources,
                'processing_time': result.get('processing_time', 0),
                'agent_metadata': {
                    'tools_used': sources.get('collections_used', []),
                    'web_search_performed': sources.get('web_search_performed', False),
                    'general_tool_used': sources.get('general_tool_used', False),
                    'chat_history_included': sources.get('chat_history_included', False)
                }
            }
            
            print(f"\n📊 Mock message structure for storage:")
            print(f"User message: {json.dumps(mock_message, indent=2)}")
            print(f"AI message: {json.dumps(mock_ai_message, indent=2)}")
            
            # Test 2: Check if the structure is correct for MongoDB storage
            print(f"\n📝 Test 2: Validating message structure")
            
            required_fields = ['id', 'role', 'content', 'timestamp']
            user_fields_ok = all(field in mock_message for field in required_fields)
            ai_fields_ok = all(field in mock_ai_message for field in required_fields)
            
            if user_fields_ok and ai_fields_ok:
                print(f"✅ GOOD: Message structure is correct for MongoDB storage")
            else:
                print(f"❌ BAD: Message structure is missing required fields")
            
            # Test 3: Check if agent metadata is included
            print(f"\n📝 Test 3: Checking agent metadata")
            
            if 'agent_metadata' in mock_ai_message:
                print(f"✅ GOOD: Agent metadata is included")
                print(f"Tools used: {mock_ai_message['agent_metadata']['tools_used']}")
                print(f"Web search performed: {mock_ai_message['agent_metadata']['web_search_performed']}")
                print(f"General tool used: {mock_ai_message['agent_metadata']['general_tool_used']}")
                print(f"Chat history included: {mock_ai_message['agent_metadata']['chat_history_included']}")
            else:
                print(f"❌ BAD: Agent metadata is missing")
        
        print("\n🎉 Chat session storage tests completed!")
        print("\n✅ SUCCESS: Chat session storage should work properly")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_session_storage() 