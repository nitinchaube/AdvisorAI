from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
import asyncio
from agents.chroma_agent import ChromaAgent
from agents.web_agent import WebAgent
from agents.history_agent import HistoryAgent
from agents.general_agent import GeneralAgent
from core.llm_router import LLMRouter
from core.memory_store import get_memory_store
import json

class LangGraphOrchestrator:
    """Main orchestrator for the LangGraph-powered chatbot with ReACT reasoning"""
    
    def __init__(self):
        self.llm_router = LLMRouter()
        self.memory_store = get_memory_store()
        
        # Initialize agents
        self.chroma_agent = ChromaAgent()
        self.web_agent = WebAgent()
        self.history_agent = HistoryAgent()
        self.general_agent = GeneralAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with ReACT reasoning"""
        
        # Define the state schema
        workflow = StateGraph(Dict)
        
        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("final", self._final_node)
        workflow.add_node("save", self._save_node)
        
        # Define edges with conditional routing
        workflow.set_entry_point("router")
        workflow.add_edge("router", "tools")
        workflow.add_edge("tools", "reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_web_search,
            {
                "web_search": "web_search",
                "final": "final"
            }
        )
        workflow.add_edge("web_search", "final")
        workflow.add_edge("final", "save")
        workflow.add_edge("save", END)
        
        return workflow.compile()
    
    async def _router_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Router node - decides which tools to use"""
        query = state.get("query", "")
        print(f"\n🎯 ROUTER: Analyzing query: '{query}'")
        
        llm = self.llm_router.get_llm()
        
        # Check for simple greetings and casual queries
        simple_greetings = ["hey", "hello", "hi", "good morning", "good afternoon", "good evening", "how are you", "what's up", "sup"]
        query_lower = query.lower().strip()
        
        # Check for follow-up queries
        follow_up_indicators = [
            "check again", "check", "again", "more", "what else", "tell me more", 
            "additional", "further", "expand", "elaborate", "details", "specifically",
            "continue", "go on", "and?", "what about", "how about", "can you tell me more",
            "give me more", "show me more", "explain more", "describe more"
        ]
        
        is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)
        
        # Also check for short queries that might be follow-ups
        if not is_follow_up and len(query_lower) <= 20:
            follow_up_pronouns = ["it", "this", "that", "these", "those", "them", "they"]
            words = query_lower.split()
            if any(word in follow_up_pronouns for word in words):
                is_follow_up = True
        
        # If it's a simple greeting, use only general tool
        if any(greeting in query_lower for greeting in simple_greetings):
            print(f"✅ ROUTER: Simple greeting detected - using general tool only")
            state["tool_decision"] = {
                "tools": ["general"],
                "reasoning": "Simple greeting detected - using general tool only"
            }
            return state
        
        # For all other queries, include history by default for better context
        # Determine additional tools based on query type
        additional_tools = []
        
        # Add chroma for Stevens-specific queries
        if any(word in query_lower for word in ["course", "cs", "class", "subject", "faculty", "professor", "admission", "requirement", "stevens", "institute", "university"]):
            additional_tools.append("chroma")
        
        # Add web for current/recent information
        if any(word in query_lower for word in ["current", "latest", "2024", "2025", "now", "recent", "contact", "phone", "email", "apply", "register"]):
            additional_tools.append("web")
        
        # Add general for general knowledge queries
        if any(word in query_lower for word in ["what is", "explain", "define", "how does", "why", "concept", "theory"]) and not additional_tools:
            additional_tools.append("general")
        
        # If no specific tools identified, use chroma as default for Stevens context
        if not additional_tools:
            additional_tools.append("chroma")
        
        # Always include history for context
        tools = ["history"] + additional_tools
        
        print(f"📚 ROUTER: Including history by default for better context")
        state["tool_decision"] = {
            "tools": tools,
            "reasoning": f"Including history by default + {', '.join(additional_tools)} for query type"
        }
        return state
    
    async def _tools_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tools node - executes selected tools in parallel"""
        tool_decision = state.get("tool_decision", {})
        tools_to_use = tool_decision.get("tools", ["chroma"])
        
        print(f"\n🔧 TOOLS: Executing tools: {tools_to_use}")
        
        # Execute tools in parallel
        tasks = []
        
        if "chroma" in tools_to_use:
            print(f"🔍 TOOLS: Starting Chroma search...")
            tasks.append(self.chroma_agent.process(state))
        
        if "history" in tools_to_use:
            print(f"📚 TOOLS: Starting History search...")
            tasks.append(self.history_agent.process(state))
        
        if "general" in tools_to_use:
            print(f"🧠 TOOLS: Starting General knowledge...")
            tasks.append(self.general_agent.process(state))
        
        # Note: Web search is handled separately in the reasoning phase
        
        # Wait for all tools to complete
        if tasks:
            print(f"⏳ TOOLS: Waiting for {len(tasks)} tools to complete...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results back into state
            for i, result in enumerate(results):
                if isinstance(result, dict):
                    state.update(result)
                    print(f"✅ TOOLS: Tool {i+1} completed successfully")
                else:
                    # Handle exceptions
                    state[f"tool_error"] = str(result)
                    print(f"❌ TOOLS: Tool {i+1} failed: {str(result)}")
        
        print(f"✅ TOOLS: All tools completed")
        return state
    
    async def _reason_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reasoning node - LLM decides if web search is needed"""
        query = state.get("query", "")
        print(f"\n🧠 REASON: Analyzing if web search is needed for: '{query}'")
        
        llm = self.llm_router.get_llm()
        
        # Gather available information
        chroma_results = state.get("chroma_results", {})
        general_answer = state.get("general_answer")
        history_results = state.get("history_results", {})
        
        # Check if this is a simple greeting or general query that doesn't need web search
        simple_greetings = ["hey", "hello", "hi", "good morning", "good afternoon", "good evening", "how are you", "what's up"]
        query_lower = query.lower().strip()
        
        # If it's a simple greeting, no web search needed
        if any(greeting in query_lower for greeting in simple_greetings):
            print(f"✅ REASON: Simple greeting detected - no web search needed")
            state["reasoning_result"] = {
                "need_web_search": False,
                "reasoning": "Simple greeting detected - no web search needed",
                "confidence": "high",
                "what_missing": "Nothing missing - greeting handled by general tool"
            }
            return state
        
        # Build context for reasoning
        available_info = []
        
        if chroma_results.get("documents"):
            available_info.append("Vector Database Results:")
            for doc in chroma_results["documents"][:2]:
                available_info.append(f"- {doc['content'][:150]}...")
            print(f"📊 REASON: Found {len(chroma_results.get('documents', []))} Chroma documents")
        
        if general_answer:
            available_info.append(f"General Knowledge: {general_answer[:200]}...")
            print(f"🧠 REASON: General knowledge available")
        
        if history_results.get("relevant_history"):
            available_info.append("Relevant History Available")
            print(f"📚 REASON: Relevant history available")
        
        context = "\n".join(available_info) if available_info else "No specific information available."
        
        # Enhanced reasoning prompt based on RAG service patterns
        reasoning_prompt = f"""
        You are an AI assistant that needs to decide whether to search the web for additional information about Stevens Institute of Technology.
        
        User Question: "{query}"
        
        Available Information:
        {context}
        
        Instructions:
        1. FIRST check if vector database (collections) has sufficient information
        2. Only use web search if vector database information is clearly insufficient
        3. Be conservative about web search - prefer using existing data
        
        Decision Guidelines:
        - Set need_web_search to true ONLY if:
          * Vector database has NO relevant documents at all
          * Vector database documents are completely unrelated to the query
          * Question specifically asks for CURRENT information (2024, 2025, latest updates, this year)
          * Question asks for specific contact information (phone, email, office hours, contact details)
          * Question asks for procedural information (how to apply, register, deadlines, application process)
          * Question asks for recent events or news about Stevens
          * Vector database information is clearly outdated or insufficient
        - Set need_web_search to false if:
          * Vector database has relevant documents (even if not perfect)
          * Question can be answered from existing information
          * It's a general knowledge question
          * It's a simple greeting or casual conversation
          * Vector database has good similarity scores
          * Question is about courses, faculty, or academic information that should be in the database
          * Question asks for basic information about Stevens (not current/recent)
        
        Examples:
        - "What computer science courses are available?" → need_web_search: false (use collections)
        - "Tell me about CS 513" → need_web_search: false (use collections)
        - "What are the latest admission requirements for 2024?" → need_web_search: true (current info needed)
        - "How do I contact the admissions office?" → need_web_search: true (contact info needed)
        - "What is machine learning?" → need_web_search: false (general knowledge)
        
        IMPORTANT: You must respond with ONLY a valid JSON object. No additional text, no explanations outside the JSON.
        
        Return this exact JSON format:
        {{
            "need_web_search": true/false,
            "reasoning": "explanation of why web search is needed or not needed",
            "confidence": "high/medium/low",
            "what_missing": "what specific information might be missing"
        }}
        """
        
        try:
            print(f"🤖 REASON: Using LLM to decide on web search...")
            response = await llm.ainvoke([{"role": "user", "content": reasoning_prompt}])
            
            print(f"📝 REASON: LLM response: {response.content[:200]}...")
            
            # Try to parse JSON
            try:
                reasoning_result = json.loads(response.content)
                state["reasoning_result"] = reasoning_result
                print(f"✅ REASON: LLM decided - Web search needed: {reasoning_result.get('need_web_search', False)}")
                print(f"📝 REASON: Reasoning: {reasoning_result.get('reasoning', 'No reasoning provided')}")
            except json.JSONDecodeError as json_error:
                print(f"❌ REASON: JSON parsing failed: {json_error}")
                print(f"📝 REASON: Raw response: {response.content}")
                
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    try:
                        reasoning_result = json.loads(json_match.group())
                        state["reasoning_result"] = reasoning_result
                        print(f"✅ REASON: Extracted JSON successfully")
                    except:
                        print(f"❌ REASON: Failed to extract valid JSON")
                        raise json_error
                else:
                    raise json_error
                    
        except Exception as e:
            print(f"❌ REASON: Error in LLM reasoning: {str(e)}")
            # Fallback reasoning - be more conservative about web search
            state["reasoning_result"] = {
                "need_web_search": False,  # Changed from True to False for fallback
                "reasoning": f"Fallback due to error: {str(e)}",
                "confidence": "low",
                "what_missing": "Unable to determine"
            }
            print(f"🔄 REASON: Fallback - no web search")
        
        return state
    
    def _should_web_search(self, state: Dict[str, Any]) -> str:
        """Determine if web search should be performed"""
        reasoning_result = state.get("reasoning_result", {})
        need_web_search = reasoning_result.get("need_web_search", False)
        
        if need_web_search:
            print(f"🌐 WEB: Web search will be performed")
            return "web_search"
        else:
            print(f"✅ WEB: No web search needed, proceeding to final answer")
            return "final"
    
    async def _web_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Web search node - performs web search when needed"""
        query = state.get("query", "")
        chroma_results = state.get("chroma_results", {})
        
        print(f"\n🌐 WEB: Performing web search for: '{query}'")
        
        # Perform web search with Chroma results for smart decision making
        web_results = await self.web_agent.process({
            "query": query,
            "chroma_results": chroma_results
        })
        
        state.update(web_results)
        print(f"✅ WEB: Web search completed")
        return state
    
    async def _final_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Final node - synthesizes the final answer"""
        query = state.get("query", "")
        print(f"\n🎯 FINAL: Synthesizing final answer for: '{query}'")
        
        llm = self.llm_router.get_llm()
        
        # Gather all available information
        chroma_results = state.get("chroma_results", {})
        web_results = state.get("web_results", {})
        general_answer = state.get("general_answer")
        history_results = state.get("history_results", {})
        reasoning_result = state.get("reasoning_result", {})
        
        # Build comprehensive context
        context_parts = []
        
        # Add Chroma results
        if chroma_results.get("documents"):
            context_parts.append("Vector Database Results:")
            for i, doc in enumerate(chroma_results["documents"][:3]):
                context_parts.append(f"Document {i+1}: {doc['content'][:200]}...")
        
        # Add web results
        if web_results.get("scraped_content"):
            context_parts.append("Web Search Results:")
            # Show more web content and format it better
            web_content = web_results["scraped_content"]
            if len(web_content) > 1000:
                context_parts.append(web_content[:1000] + "...")
            else:
                context_parts.append(web_content)
            
            # Also add web URLs if available
            if web_results.get("search_results"):
                context_parts.append("Web Sources:")
                for i, url in enumerate(web_results["search_results"][:3]):
                    context_parts.append(f"Source {i+1}: {url}")
        elif web_results.get("web_content"):
            context_parts.append("Web Search Results:")
            # Show more web content and format it better
            web_content = web_results["web_content"]
            if len(web_content) > 1000:
                context_parts.append(web_content[:1000] + "...")
            else:
                context_parts.append(web_content)
            
            # Also add web URLs if available
            if web_results.get("urls"):
                context_parts.append("Web Sources:")
                for i, url in enumerate(web_results["urls"][:3]):
                    context_parts.append(f"Source {i+1}: {url}")
        
        # Add general knowledge
        if general_answer:
            context_parts.append(f"General Knowledge: {general_answer}")
        
        # Add history
        if history_results.get("relevant_history"):
            context_parts.append("Previous Conversation Context (for reference only):")
            for i, entry in enumerate(history_results["relevant_history"][:3]):
                context_parts.append(f"Previous Q: {entry.get('query', 'Unknown')}")
                context_parts.append(f"Previous A: {entry.get('response', 'Unknown')[:200]}...")
                context_parts.append("---")
        elif state.get("chat_history"):
            # If no history results but chat_history is provided, use it directly
            context_parts.append("Previous Conversation Context (for reference only):")
            context_parts.append(state["chat_history"])
            context_parts.append("---")
        
        # Add reasoning
        if reasoning_result.get("reasoning"):
            context_parts.append(f"Reasoning: {reasoning_result['reasoning']}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific information available."
        
        # Enhanced final answer prompt with better history handling
        final_prompt = f"""
        You are a helpful AI assistant for Stevens Institute of Technology. Synthesize a comprehensive answer based on all available information.
        
        User Question: "{query}"
        
        Available Information:
        {context}
        
        Instructions:
        1. **PRIORITY: Answer the CURRENT user question first and foremost**
        2. Use information from all available sources (vector database, web search, general knowledge)
        3. If the question is about Stevens Institute of Technology, use specific information
        4. For general questions, provide informative responses
        5. Be concise but thorough
        6. If you don't know something, say so clearly
        7. Avoid speculation or making up information
        8. Prioritize the most relevant information for the CURRENT question
        9. If general knowledge is available and sufficient, use it
        10. If web search was performed, incorporate that information appropriately
        11. **Use conversation history ONLY for context and reference, NOT to answer the current question**
        12. If this is a follow-up question (like "check again", "tell me more", "what else"), refer to the previous conversation history for context
        13. For follow-up queries, build upon the previous answers and provide additional or updated information
        14. If the user asks to "check again", provide the same information but perhaps with more detail or updated sources
        15. If web search results are available, use them to provide specific, up-to-date information
        16. If vector database results are available, combine them with web search results for comprehensive answers
        17. **IMPORTANT: Do NOT answer questions from the history - only use history for context**
        18. If the user asks for "more details" or "tell me more", provide additional information not mentioned before
        19. If the user asks "what else", provide different aspects or related information
        20. Maintain conversation flow and context throughout the interaction
        21. Reference previous conversation when relevant to show continuity
        22. **CRITICAL: The current user question is the ONLY question you should answer**
        23. History is for understanding context, not for answering historical questions
        24. Focus on providing fresh, relevant information for the current query
        
        Answer:
        """
        
        try:
            print(f"🤖 FINAL: Using LLM to synthesize final answer...")
            response = await llm.ainvoke([{"role": "user", "content": final_prompt}])
            final_answer = response.content
            
            print(f"📝 FINAL: Generated answer: {final_answer[:100]}...")
            
            # Determine which tools were used
            tools_used = []
            if chroma_results.get("documents"):
                tools_used.append("chroma")
            if web_results.get("scraped_content") or web_results.get("web_content"):
                tools_used.append("web")
            if general_answer:
                tools_used.append("general")
            if history_results.get("relevant_history"):
                tools_used.append("history")
            
            print(f"✅ FINAL: Answer synthesized using tools: {tools_used}")
            print(f"💾 FINAL: Setting answer in state: {final_answer[:50]}...")
            
            state["answer"] = final_answer
            state["success"] = True
            state["metadata"] = {
                "tools_used": tools_used,
                "collections_searched": chroma_results.get("collections_searched", []),
                "web_search_performed": bool(web_results.get("scraped_content")),
                "used_general_tool": bool(general_answer),
                "reasoning_result": reasoning_result
            }
            
        except Exception as e:
            print(f"❌ FINAL: Error synthesizing answer: {str(e)}")
            state["answer"] = "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."
            state["success"] = False
        
        return state
    
    async def _save_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save node - stores the conversation"""
        user_id = state.get("user_id", "default")
        query = state.get("query", "")
        answer = state.get("answer", "")  # Changed from final_answer to answer
        
        # Save to memory
        await self.memory_store.save_conversation(
            user_id=user_id,
            query=query,
            response=answer,
            metadata={
                "tools_used": state.get("tool_decision", {}).get("tools", []),
                "collections_searched": state.get("collections_searched", []),
                "web_search_performed": "web_results" in state,
                "used_general_tool": state.get("used_general_tool", False),
                "reasoning_result": state.get("reasoning_result", {})
            }
        )
        
        return state
    
    async def process_query(self, query: str, user_id: str = "default", chat_history: str = "") -> Dict[str, Any]:
        """Process a user query through the entire workflow"""
        initial_state = {
            "query": query,
            "user_id": user_id,
            "chat_history": chat_history  # Add chat history to initial state
        }
        
        try:
            print(f"🚀 PROCESS: Starting query processing for: '{query}'")
            print(f"📚 PROCESS: Chat history provided: {bool(chat_history)}")
            final_state = await self.graph.ainvoke(initial_state)
            
            answer = final_state.get("answer", "")
            print(f"📤 PROCESS: Final answer retrieved: {answer[:100]}...")
            print(f"📊 PROCESS: Final state keys: {list(final_state.keys())}")
            
            result = {
                "success": True,
                "answer": answer,  # Changed from final_answer to answer
                "metadata": {
                    "tools_used": final_state.get("tool_decision", {}).get("tools", []),
                    "collections_searched": final_state.get("collections_searched", []),
                    "web_search_performed": "web_results" in final_state,
                    "used_general_tool": final_state.get("used_general_tool", False),
                    "reasoning_result": final_state.get("reasoning_result", {})
                }
            }
            
            print(f"✅ PROCESS: Returning result with answer length: {len(answer)}")
            return result
            
        except Exception as e:
            print(f"❌ PROCESS: Error in query processing: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment."
            } 