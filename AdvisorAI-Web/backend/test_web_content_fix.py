#!/usr/bin/env python3
"""
Test script to verify web content handling and collection prioritization
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_web_content_and_collections():
    """Test that web content is properly handled and collections are prioritized"""
    
    print("🧪 Testing Web Content and Collection Prioritization")
    print("=" * 55)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries that should prioritize collections
        test_queries = [
            "What computer science courses are available?",
            "Tell me about CS 513 course",
            "What are the admission requirements?",
            "Who is Professor Smith?",
            "What is machine learning?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("-" * 55)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: '{query}'")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_web_content",
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
                
                print(f"Collections used: {collections_used}")
                print(f"Web search performed: {web_search_performed}")
                print(f"General tool used: {general_tool_used}")
                
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"Confidence: {reasoning.get('confidence', 'Unknown')}")
        
        print("\n🎉 Web content and collection tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_content_and_collections() 