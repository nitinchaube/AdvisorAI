import asyncio
from core.langgraph_graph import LangGraphOrchestrator

async def main():
    orchestrator = LangGraphOrchestrator()
    
    # Test different types of queries to demonstrate ReACT reasoning
    test_queries = [
        "What courses are available in Computer Science?",  # Domain-specific, likely sufficient from DB
        "What is machine learning?",  # General knowledge, no web search needed
        "What are the latest developments in AI at Stevens?",  # Current info, needs web search
        "Who is Professor Smith?",  # Domain-specific, likely sufficient from DB
        "What are the current admission requirements for Stevens?",  # Current info, needs web search
        "Explain the concept of artificial intelligence",  # General knowledge, no web search needed
        "What are the latest research projects at Stevens?",  # Current info, needs web search
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = await orchestrator.process_query(
            query=query,
            user_id="user123"
        )
        
        print(f"Answer: {result['answer']}")
        print(f"Tools used: {result['metadata']['tools_used']}")
        print(f"Used general tool: {result['metadata'].get('used_general_tool', False)}")
        print(f"Web search performed: {result['metadata'].get('web_search_performed', False)}")
        
        # Show reasoning if available
        reasoning = result['metadata'].get('reasoning_result', {})
        if reasoning:
            print(f"Reasoning: {reasoning.get('reasoning', 'N/A')}")
            print(f"Confidence: {reasoning.get('confidence', 'N/A')}")
            print(f"What missing: {reasoning.get('what_missing', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main()) 