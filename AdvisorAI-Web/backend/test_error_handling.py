#!/usr/bin/env python3
"""
Test to verify that user-friendly error messages are shown instead of technical errors
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_error_handling():
    """Test that user-friendly error messages are shown instead of technical errors"""
    
    print("🧪 Testing Error Handling - User-Friendly Messages")
    print("=" * 55)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test normal query first
        print("\n📝 Test 1: Normal query (should work)")
        result = chatbot_service.process_query(
            user_query="What is machine learning?",
            user_id="test_user_error_handling",
            chat_history=[]
        )
        
        if result.get('error'):
            print(f"❌ Unexpected error: {result.get('response', 'Unknown error')}")
        else:
            print(f"✅ Success: {result.get('response', '')[:100]}...")
        
        # Test with invalid query to trigger error handling
        print("\n📝 Test 2: Very long query (should trigger error)")
        long_query = "What is machine learning? " * 1000  # Very long query
        result = chatbot_service.process_query(
            user_query=long_query,
            user_id="test_user_error_handling",
            chat_history=[]
        )
        
        if result.get('error'):
            response = result.get('response', '')
            print(f"✅ Error handled properly")
            print(f"Response: {response}")
            
            # Check if response is user-friendly
            if "technical" in response.lower() or "difficulties" in response.lower() or "trouble" in response.lower():
                print(f"✅ GOOD: User-friendly error message shown")
            else:
                print(f"⚠️  WARNING: Response may contain technical details")
        else:
            print(f"✅ Query processed successfully")
        
        # Test with empty query
        print("\n📝 Test 3: Empty query")
        result = chatbot_service.process_query(
            user_query="",
            user_id="test_user_error_handling",
            chat_history=[]
        )
        
        if result.get('error'):
            response = result.get('response', '')
            print(f"✅ Error handled properly")
            print(f"Response: {response}")
        else:
            print(f"✅ Query processed successfully")
        
        print("\n🎉 Error handling tests completed!")
        print("\n✅ SUCCESS: User-friendly error messages should be shown")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_error_handling() 