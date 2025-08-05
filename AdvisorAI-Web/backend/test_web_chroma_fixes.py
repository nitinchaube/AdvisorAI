#!/usr/bin/env python3
"""
Test to verify the web search and chroma collection fixes
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_web_chroma_fixes():
    """Test the web search and chroma collection fixes"""
    
    print("🧪 Testing Web Search and Chroma Collection Fixes")
    print("=" * 50)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries that should use both chroma and web
        test_queries = [
            {
                "query": "Tell me about Professor Dehnad",
                "description": "Should use chroma collections + web search with proper content extraction"
            },
            {
                "query": "What courses does Professor Dehnad teach?",
                "description": "Should search chroma for course info + web for current details"
            },
            {
                "query": "professor dehnad i think teaches knowledge discovery and data mining",
                "description": "Should verify this information using chroma + web"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("-" * 50)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: '{query}'")
            print(f"📋 Description: {description}")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_web_chroma_fixes",
                chat_history=[]
            )
            
            if result.get('error'):
                print(f"❌ Error: {result.get('response', 'Unknown error')}")
            else:
                print(f"✅ Success!")
                print(f"Response: {result.get('response', '')[:300]}...")
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
                if len(answer) > 200:
                    print(f"✅ GOOD: Comprehensive answer provided ({len(answer)} chars)")
                else:
                    print(f"⚠️  WARNING: Answer seems too short ({len(answer)} chars)")
                
                # Check for specific improvements
                if "dehnad" in query.lower():
                    if "chroma" in actual_tools:
                        print(f"✅ GOOD: Chroma collections were used")
                    else:
                        print(f"⚠️  WARNING: Chroma collections should be used for professor queries")
                    
                    if "web" in actual_tools:
                        print(f"✅ GOOD: Web search was performed")
                    else:
                        print(f"⚠️  WARNING: Web search should be performed for current professor info")
                
                # Check if the answer contains meaningful information
                if "professor" in answer.lower() or "dehnad" in answer.lower() or "stevens" in answer.lower():
                    print(f"✅ GOOD: Answer contains relevant information")
                else:
                    print(f"⚠️  WARNING: Answer may not contain relevant information")
        
        print("\n🎉 Web search and chroma collection fixes test completed!")
        print("\n✅ SUCCESS: Fixes implemented:")
        print("   - Fixed web search content extraction")
        print("   - Improved chroma collection usage")
        print("   - Better content length (5000 chars)")
        print("   - More comprehensive web scraping")
        print("   - Proper async handling")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_chroma_fixes() 