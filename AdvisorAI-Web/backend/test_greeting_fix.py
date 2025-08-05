#!/usr/bin/env python3
"""
Test script to verify that simple greetings are handled correctly
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_greeting_handling():
    """Test that simple greetings are handled by general tool without web search"""
    
    print("🧪 Testing Greeting Handling")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test simple greetings
        test_greetings = [
            "Hey",
            "Hello",
            "Hi there",
            "Good morning",
            "What's up"
        ]
        
        print(f"\n🧪 Testing {len(test_greetings)} greetings...")
        print("-" * 40)
        
        for i, greeting in enumerate(test_greetings, 1):
            print(f"\n📝 Test {i}: '{greeting}'")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=greeting,
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
                
                if web_search_performed:
                    print("⚠️  WARNING: Web search was performed for a simple greeting!")
                else:
                    print("✅ GOOD: No web search for simple greeting")
                
                if general_tool_used:
                    print("✅ GOOD: General tool was used")
                else:
                    print("⚠️  WARNING: General tool was not used")
        
        print("\n🎉 Greeting handling tests completed!")
        
        if web_search_performed:
            print("\n❌ ISSUE: Some greetings triggered web search when they shouldn't have")
        else:
            print("\n✅ SUCCESS: All greetings handled correctly without unnecessary web search")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_greeting_handling() 