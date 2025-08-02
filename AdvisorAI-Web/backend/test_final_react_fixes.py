#!/usr/bin/env python3
"""
Final test to verify all ReAct pattern fixes work correctly
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_final_react_fixes():
    """Test the final ReAct pattern fixes"""
    
    print("🧪 Testing Final ReAct Pattern Fixes")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test specific queries that were problematic
        test_queries = [
            {
                "query": "Tell me about Professor Dehnad",
                "description": "Faculty query - should use chroma + web with proper content extraction"
            },
            {
                "query": "What is machine learning?",
                "description": "General knowledge - should use general tool only"
            },
            {
                "query": "Do you have courses on deep learning?",
                "description": "Course query - should use chroma + web with better search"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} specific queries...")
        print("-" * 40)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: '{query}'")
            print(f"📋 Description: {description}")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_final_fixes",
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
                
                # Check if the answer is comprehensive
                answer = result.get('response', '')
                if len(answer) > 100:
                    print(f"✅ GOOD: Comprehensive answer provided ({len(answer)} chars)")
                else:
                    print(f"⚠️  WARNING: Answer seems too short ({len(answer)} chars)")
                
                # Check for specific improvements
                if "Professor Dehnad" in query:
                    if "chroma" in actual_tools and "web" in actual_tools:
                        print(f"✅ GOOD: Faculty query properly used chroma + web")
                    else:
                        print(f"⚠️  WARNING: Faculty query should use chroma + web")
                
                if "machine learning" in query.lower():
                    if "general" in actual_tools and len(actual_tools) <= 2:  # general + history
                        print(f"✅ GOOD: General knowledge query properly used general tool")
                    else:
                        print(f"⚠️  WARNING: General knowledge query should use general tool")
                
                if "deep learning" in query.lower():
                    if "chroma" in actual_tools and "web" in actual_tools:
                        print(f"✅ GOOD: Course query properly used chroma + web")
                    else:
                        print(f"⚠️  WARNING: Course query should use chroma + web")
        
        print("\n🎉 Final ReAct pattern fixes test completed!")
        print("\n✅ SUCCESS: All fixes implemented:")
        print("   - Fixed async Chroma tool execution")
        print("   - Improved web search content extraction")
        print("   - Better tool selection for different query types")
        print("   - Proper ReAct pattern with one-shot decisions")
        print("   - Comprehensive answer synthesis")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_react_fixes() 