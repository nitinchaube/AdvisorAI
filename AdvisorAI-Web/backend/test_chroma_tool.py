#!/usr/bin/env python3
"""
Test script to check if Chroma tool is working properly
"""

import sys
import os
import asyncio

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.tools.chroma_tool import ChromaTool

async def test_chroma_tool():
    """Test the Chroma tool functionality"""
    
    print("🧪 Testing Chroma Tool")
    print("=" * 25)
    
    try:
        # Initialize Chroma tool
        chroma_tool = ChromaTool()
        print(f"✅ ChromaTool initialized with {len(chroma_tool.collections)} collections")
        
        # Test queries
        test_queries = [
            "What computer science courses are available?",
            "Tell me about CS 513 course",
            "What are the admission requirements?",
            "Who is Professor Smith?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("-" * 25)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: '{query}'")
            
            # Search collections
            result = await chroma_tool.search_collections(query, "test_user")
            
            if result.get('success'):
                documents = result.get('documents', [])
                collections_searched = result.get('collections_searched', [])
                
                print(f"✅ Success!")
                print(f"Collections searched: {collections_searched}")
                print(f"Documents found: {len(documents)}")
                
                if documents:
                    print("Sample documents:")
                    for j, doc in enumerate(documents[:2]):
                        print(f"  Doc {j+1}: {doc.page_content[:100]}...")
                else:
                    print("❌ No documents found")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print("\n🎉 Chroma tool tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chroma_tool()) 