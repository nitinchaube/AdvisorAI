#!/usr/bin/env python3
"""
Test script to demonstrate enhanced web search functionality
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.web_tool import WebTool
from core.llm_router import LLMRouter

async def test_web_search():
    """Test the enhanced web search functionality"""
    
    print("🧪 Testing Enhanced Web Search Functionality")
    print("=" * 50)
    
    # Initialize tools
    web_tool = WebTool()
    llm_router = LLMRouter()
    
    # Test queries
    test_queries = [
        "computer science courses",
        "admission requirements", 
        "faculty research areas",
        "campus location",
        "tuition fees",
        "graduate programs",
        "Stevens Institute of Technology computer science",  # Already contains Stevens
        "latest news",
        "contact information"
    ]
    
    print("Testing query enhancement:")
    for query in test_queries:
        enhanced = web_tool._enhance_query_with_stevens(query)
        print(f"Original: '{query}'")
        print(f"Enhanced: '{enhanced}'")
        print("-" * 30)
    
    print("\nTesting web search decision logic:")
    
    # Mock Chroma results for testing
    mock_chroma_results = {
        "documents": [
            {"content": "Computer Science program at Stevens Institute of Technology", "score": 0.3},
            {"content": "Stevens CS curriculum information", "score": 0.5}
        ]
    }
    
    empty_chroma_results = {"documents": []}
    
    test_cases = [
        ("computer science courses", mock_chroma_results, "Good Chroma results"),
        ("admission requirements", empty_chroma_results, "No Chroma results"),
        ("latest news 2024", mock_chroma_results, "Time-sensitive query"),
        ("contact email", mock_chroma_results, "Procedural query")
    ]
    
    for query, chroma_results, description in test_cases:
        should_search = web_tool._should_use_web_search(query, chroma_results)
        print(f"Query: '{query}' ({description})")
        print(f"Should web search: {should_search}")
        print("-" * 30)
    
    print("\n🎉 Web search enhancement tests completed!")
    print("\nKey Features:")
    print("✅ Automatically appends 'Stevens Institute of Technology' to queries")
    print("✅ Smart decision making based on query type and Chroma results")
    print("✅ Handles time-sensitive and procedural queries")
    print("✅ Integrates with existing web_scrapper functions")

if __name__ == "__main__":
    asyncio.run(test_web_search()) 