#!/usr/bin/env python3
"""
Test script to verify history integration for follow-up queries
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_history_integration():
    """Test that history is properly integrated for follow-up queries"""
    
    print("🧪 Testing History Integration")
    print("=" * 35)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test a sequence of queries to build history
        test_sequence = [
            "What computer science courses are available?",
            "check again",
            "tell me more about the courses",
            "What are the admission requirements?",
            "check again"
        ]
        
        print(f"\n🧪 Testing {len(test_sequence)} queries in sequence...")
        print("-" * 35)
        
        for i, query in enumerate(test_sequence, 1):
            print(f"\n📝 Test {i}: '{query}'")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_history",
                chat_history=[]
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                print(f"Response: {result.get('response', '')[:150]}...")
                print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Check if history was used
                sources = result.get('sources', {})
                history_included = sources.get('chat_history_included', False)
                general_tool_used = sources.get('general_tool_used', False)
                
                print(f"History included: {history_included}")
                print(f"General tool used: {general_tool_used}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
        
        print("\n🎉 History integration tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history_integration() 