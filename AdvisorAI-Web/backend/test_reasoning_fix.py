#!/usr/bin/env python3
"""
Test script to debug the reasoning issue
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_reasoning_fix():
    """Test that the reasoning issue is fixed"""
    
    print("🧪 Testing Reasoning Fix")
    print("=" * 30)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries that should trigger reasoning
        test_queries = [
            "give some info on tian han?",
            "What computer science courses are available?",
            "Tell me about machine learning",
            "What are the admission requirements for 2024?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("-" * 30)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: '{query}'")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user",
                chat_history=[]
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                print(f"Response: {result.get('response', '')[:100]}...")
                print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Check if web search was performed
                sources = result.get('sources', {})
                web_search_performed = sources.get('web_search_performed', False)
                general_tool_used = sources.get('general_tool_used', False)
                
                print(f"Web search performed: {web_search_performed}")
                print(f"General tool used: {general_tool_used}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"Reasoning: {reasoning.get('reasoning', 'No reasoning')}")
                    print(f"Confidence: {reasoning.get('confidence', 'Unknown')}")
        
        print("\n🎉 Reasoning fix tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reasoning_fix() 