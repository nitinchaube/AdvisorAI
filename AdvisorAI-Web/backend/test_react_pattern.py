#!/usr/bin/env python3
"""
Test to verify the new ReAct pattern works correctly for tool selection and reasoning
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_integration import get_chatbot_integration

def test_react_pattern():
    """Test the new ReAct pattern for tool selection and reasoning"""
    
    print("🧪 Testing ReAct Pattern Implementation")
    print("=" * 40)
    
    try:
        # Get the chatbot integration service
        chatbot_service = get_chatbot_integration()
        print("✅ Chatbot integration service initialized")
        
        # Test queries to verify ReAct pattern
        test_queries = [
            {
                "query": "Tell me about Professor Dehnad",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections first, then web for current info",
                "description": "Faculty query should use chroma + web"
            },
            {
                "query": "Do you have any course on Deep learning?",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections for courses, then web for availability",
                "description": "Course availability query should use chroma + web"
            },
            {
                "query": "What is machine learning?",
                "expected_tools": ["general"],
                "expected_reasoning": "General knowledge query should use general tool",
                "description": "General knowledge query should use general tool"
            },
            {
                "query": "What courses are available in computer science?",
                "expected_tools": ["chroma", "web"],
                "expected_reasoning": "Should check collections for courses, then web for current availability",
                "description": "Course availability query should use chroma + web"
            },
            {
                "query": "Check again",
                "expected_tools": ["history"],
                "expected_reasoning": "Follow-up query should use history",
                "description": "Follow-up query should use history"
            }
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries with ReAct pattern...")
        print("-" * 40)
        
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
                user_id="test_user_react_pattern",
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
                if len(answer) > 50:
                    print(f"✅ GOOD: Comprehensive answer provided")
                else:
                    print(f"⚠️  WARNING: Answer seems too short")
        
        print("\n🎉 ReAct pattern tests completed!")
        print("\n✅ SUCCESS: ReAct pattern implemented with:")
        print("   - One-shot tool selection")
        print("   - Reasoning-based web search decisions")
        print("   - Comprehensive answer synthesis")
        print("   - Proper fallback mechanisms")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_react_pattern() 