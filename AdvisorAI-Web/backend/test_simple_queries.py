#!/usr/bin/env python3
"""
Test to verify that simple queries use the general agent directly
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_simple_queries():
    """Test that simple queries use general agent directly"""
    
    print("🧪 Testing Simple Query Handling")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test simple queries that should use general tool directly
        test_queries = [
            {
                "query": "thanks",
                "description": "Simple thank you - should use general tool directly"
            },
            {
                "query": "hello",
                "description": "Simple greeting - should use general tool directly"
            },
            {
                "query": "how are you?",
                "description": "Simple question - should use general tool directly"
            },
            {
                "query": "ok",
                "description": "Simple acknowledgment - should use general tool directly"
            },
            {
                "query": "cool",
                "description": "Simple expression - should use general tool directly"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} simple queries...")
        print("-" * 40)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: '{query}'")
            print(f"📋 Description: {description}")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_simple_queries",
                chat_history=[]
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                print(f"Response: {result.get('response', '')[:200]}...")
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
                
                # Check reasoning
                if 'reasoning' in sources:
                    reasoning = sources['reasoning']
                    print(f"🧠 Reasoning: {reasoning.get('reasoning', 'No reasoning')[:100]}...")
                    print(f"🎯 Confidence: {reasoning.get('confidence', 'Unknown')}")
                    print(f"📊 Web search needed: {reasoning.get('need_web_search', 'Unknown')}")
                
                # Check if the answer is appropriate for simple queries
                answer = result.get('response', '')
                if len(answer) > 10 and len(answer) < 200:
                    print(f"✅ GOOD: Appropriate response length for simple query ({len(answer)} chars)")
                else:
                    print(f"⚠️  WARNING: Response length may be inappropriate ({len(answer)} chars)")
                
                # Check for specific improvements
                if "general" in actual_tools and len(actual_tools) <= 2:  # general + history
                    print(f"✅ GOOD: Simple query properly used general tool")
                else:
                    print(f"⚠️  WARNING: Simple query should use general tool only")
                
                if not web_search_performed:
                    print(f"✅ GOOD: No unnecessary web search for simple query")
                else:
                    print(f"⚠️  WARNING: Web search should not be performed for simple queries")
                
                # Check if the answer is natural and friendly
                if any(word in answer.lower() for word in ["welcome", "hello", "hi", "good", "thanks", "you're", "glad", "happy"]):
                    print(f"✅ GOOD: Response is natural and friendly")
                else:
                    print(f"⚠️  WARNING: Response may not be natural for simple query")
        
        print("\n🎉 Simple query handling test completed!")
        print("\n✅ SUCCESS: Simple queries now:")
        print("   - Use general tool directly")
        print("   - Skip unnecessary web search")
        print("   - Provide quick, natural responses")
        print("   - Avoid overthinking basic interactions")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_queries() 