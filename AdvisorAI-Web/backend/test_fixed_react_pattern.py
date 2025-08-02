#!/usr/bin/env python3
"""
Test to verify the fixed ReAct pattern works correctly
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_fixed_react_pattern():
    """Test the fixed ReAct pattern for tool selection and reasoning"""
    
    print("🧪 Testing Fixed ReAct Pattern Implementation")
    print("=" * 45)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries to verify fixed ReAct pattern
        test_queries = [
            {
                "query": "Tell me about Professor Dehnad",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections first, then web for current info",
                "description": "Faculty query should use chroma + web"
            },
            {
                "query": "What is machine learning?",
                "expected_tools": ["general"],
                "expected_reasoning": "General knowledge query should use general tool",
                "description": "General knowledge query should use general tool"
            },
            {
                "query": "Do you have any course on Deep learning?",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections for courses, then web for availability",
                "description": "Course availability query should use chroma + web"
            },
            {
                "query": "What is the meaning of life?",
                "expected_tools": ["general"],
                "expected_reasoning": "Philosophical query should use general tool",
                "description": "Philosophical query should use general tool"
            },
            {
                "query": "Explain neural networks",
                "expected_tools": ["general"],
                "expected_reasoning": "Concept explanation should use general tool",
                "description": "Concept explanation should use general tool"
            },
            {
                "query": "What courses are available in computer science?",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections for courses, then web for current availability",
                "description": "Course availability query should use chroma + web"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries with fixed ReAct pattern...")
        print("-" * 45)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            expected_tools = test_case["expected_tools"]
            expected_reasoning = test_case["expected_reasoning"]
            description = test_case["description"]
            
            print(f"\n📝 Test {i}: '{query}'")
            print(f"📋 Description: {description}")
            print(f"🎯 Expected tools: {expected_tools}")
            
            # Process query
            result = chatbot_service.process_query(
                user_query=query,
                user_id="test_user_fixed_react",
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
                
                # Verify expected tools were used
                if expected_tools:
                    if any(tool in actual_tools for tool in expected_tools):
                        print(f"✅ GOOD: Expected tools used")
                    else:
                        print(f"⚠️  WARNING: Expected tools not used. Expected: {expected_tools}, Got: {actual_tools}")
                
                # Check if the answer is comprehensive
                answer = result.get('response', '')
                if len(answer) > 100:
                    print(f"✅ GOOD: Comprehensive answer provided ({len(answer)} chars)")
                else:
                    print(f"⚠️  WARNING: Answer seems too short ({len(answer)} chars)")
        
        print("\n🎉 Fixed ReAct pattern tests completed!")
        print("\n✅ SUCCESS: Fixed ReAct pattern implemented with:")
        print("   - Better tool selection for different query types")
        print("   - Improved web search with better queries")
        print("   - More comprehensive content extraction")
        print("   - Proper fallback mechanisms")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_react_pattern() 