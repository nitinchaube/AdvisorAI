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
        """Router node - LLM decides which tools to use using ReAct pattern"""
        query = state.get("query", "")
        print(f"\n🎯 ROUTER: Analyzing query for tool selection: '{query}'")
        
        llm = self.llm_router.get_llm()
        
        # First, check if this is a simple query using LLM
        simple_check_prompt = f"""
        You are analyzing a user query to determine if it's a simple interaction that doesn't need complex reasoning.

        User Query: "{query}"

        Determine if this is a simple query that should get a direct, friendly response without complex analysis.

        Simple queries include:
        - Greetings (hello, hi, hey, good morning)
        - Thanks/acknowledgments (thanks, thank you, ok, sure)
        - Basic expressions (cool, nice, great, wow)
        - Simple questions (how are you, what's up)
        - Short responses (yes, no, maybe)

        Return ONLY a JSON object:
        {{
            "is_simple": true/false,
            "reasoning": "brief explanation of why it's simple or complex"
        }}

        Examples:
        - "thanks" → {{"is_simple": true, "reasoning": "Simple thank you expression"}}
        - "hello" → {{"is_simple": true, "reasoning": "Basic greeting"}}
        - "Tell me about Professor Dehnad" → {{"is_simple": false, "reasoning": "Complex information request"}}
        - "What is machine learning?" → {{"is_simple": false, "reasoning": "Knowledge question requiring explanation"}}
        """

        try:
            print(f"🤖 ROUTER: Checking if query is simple...")
            response = await llm.ainvoke([{"role": "user", "content": simple_check_prompt}])
            
            # Parse JSON response
            try:
                import json
                import re
                
                # Try to parse JSON
                try:
                    simple_check = json.loads(response.content.strip())
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        simple_check = json.loads(json_match.group())
                    else:
                        raise json.JSONDecodeError("No valid JSON found")
                
                is_simple = simple_check.get("is_simple", False)
                reasoning = simple_check.get("reasoning", "No reasoning provided")
                
                print(f"📝 ROUTER: Simple check - {is_simple}: {reasoning}")
                
                # If it's a simple query, use general tool directly
                if is_simple:
                    print(f"✅ ROUTER: Simple query detected - using general tool directly")
                    state["tool_decision"] = {
                        "tools": ["general", "history"],
                        "primary_tool": "general",
                        "reasoning": f"Simple query detected: {reasoning}",
                        "confidence": "high",
                        "simple_query": True
                    }
                    return state
                
            except Exception as parse_error:
                print(f"❌ ROUTER: Error parsing simple check response: {parse_error}")
                # Continue with normal ReAct flow if parsing fails
        
        except Exception as e:
            print(f"❌ ROUTER: Error in simple query check: {str(e)}")
            # Continue with normal ReAct flow if simple check fails
        
        # Generate chat name for complex queries
        try:
            chat_name_prompt = f"""
            Generate a short, descriptive name for this chat session based on the user's query.
            
            User Query: "{query}"
            
            Create a concise name (3-8 words) that captures the main topic or intent of this conversation.
            
            Examples:
            - "Tell me about Professor Dehnad" → "Professor Dehnad Information"
            - "What courses are available in computer science?" → "CS Course Recommendations"
            - "How do I apply for admission?" → "Admission Application Guide"
            - "What is machine learning?" → "Machine Learning Explanation"
            - "Can you help me with course selection?" → "Course Selection Help"
            
            Return ONLY the chat name, no quotes or extra text.
            """
            
            print(f"🤖 ROUTER: Generating chat name...")
            name_response = await llm.ainvoke([{"role": "user", "content": chat_name_prompt}])
            chat_name = name_response.content.strip().replace('"', '').replace("'", "")
            print(f"📝 ROUTER: Generated chat name: {chat_name}")
            state["chat_name"] = chat_name
            
        except Exception as e:
            print(f"❌ ROUTER: Error generating chat name: {str(e)}")
            state["chat_name"] = "New Chat"
        
        # ReAct-style prompt for one-shot tool selection
        router_prompt = f"""
        You are an AI assistant for Stevens Institute of Technology. Analyze the user query and decide which tools to use.

        Available tools:
        1. "general" - For general knowledge questions, definitions, concepts, explanations (NON-Stevens specific)
        2. "chroma" - For Stevens-specific data (courses, faculty, programs, policies, requirements)
        3. "web" - For current/recent information, contact details, availability, updates
        4. "history" - For conversation context and follow-up questions

        User Query: "{query}"

        Decision Guidelines:
        - Use "general" for: what is, explain, define, how does, why, concept, theory (NON-Stevens specific)
        - Use "chroma" for: courses, faculty, professors, programs, Stevens-specific information
        - Use "web" for: current info, contact details, availability, recent updates
        - Use "history" for: conversation context, follow-up questions

        Think step by step:
        1. What type of information is being requested?
        2. Is it Stevens-specific or general knowledge?
        3. Does it need current/recent information?
        4. Is it a follow-up or context-dependent question?

        Return ONLY a valid JSON object with your reasoning and tool selection:
        {{
            "reasoning": "step-by-step analysis of the query",
            "tools": ["tool1", "tool2", "tool3"],
            "confidence": "high/medium/low",
            "primary_tool": "main_tool_to_use_first"
        }}

        Examples:
        - "What is machine learning?" → {{"tools": ["general"], "primary_tool": "general"}}
        - "Tell me about Professor Dehnad" → {{"tools": ["chroma", "web"], "primary_tool": "chroma"}}
        - "Do you have courses on deep learning?" → {{"tools": ["chroma", "web"], "primary_tool": "chroma"}}
        - "What courses are available?" → {{"tools": ["chroma", "web"], "primary_tool": "chroma"}}
        - "Check again" → {{"tools": ["history"], "primary_tool": "history"}}
        - "What is the meaning of life?" → {{"tools": ["general"], "primary_tool": "general"}}
        - "Explain neural networks" → {{"tools": ["general"], "primary_tool": "general"}}
        """

        try:
            print(f"🤖 ROUTER: Using LLM for tool selection...")
            response = await llm.ainvoke([{"role": "user", "content": router_prompt}])
            
            print(f"📝 ROUTER: LLM response: {response.content[:200]}...")
            
            # Parse JSON response
            try:
                import json
                import re
                
                # Try to parse JSON
                try:
                    tool_decision = json.loads(response.content.strip())
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        tool_decision = json.loads(json_match.group())
                    else:
                        raise json.JSONDecodeError("No valid JSON found")
                
                # Validate and set defaults
                tools = tool_decision.get("tools", ["chroma"])
                primary_tool = tool_decision.get("primary_tool", tools[0] if tools else "chroma")
                reasoning = tool_decision.get("reasoning", "No reasoning provided")
                confidence = tool_decision.get("confidence", "medium")
                
                # Always include history for context
                if "history" not in tools:
                    tools.append("history")
                
                print(f"✅ ROUTER: Selected tools: {tools}")
                print(f"🎯 ROUTER: Primary tool: {primary_tool}")
                print(f"🧠 ROUTER: Reasoning: {reasoning[:100]}...")
                print(f"📊 ROUTER: Confidence: {confidence}")
                
                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": primary_tool,
                    "reasoning": reasoning,
                    "confidence": confidence
                }
                
            except Exception as parse_error:
                print(f"❌ ROUTER: Error parsing LLM response: {parse_error}")
                # Fallback to rule-based selection
                tools = self._fallback_tool_selection(query)
                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": tools[0] if tools else "chroma",
                    "reasoning": "Fallback rule-based selection",
                    "confidence": "low"
                }
                
        except Exception as e:
            print(f"❌ ROUTER: Error in LLM tool selection: {str(e)}")
            # Fallback to rule-based selection
            tools = self._fallback_tool_selection(query)
            state["tool_decision"] = {
                "tools": tools,
                "primary_tool": tools[0] if tools else "chroma",
                "reasoning": f"Fallback due to error: {str(e)}",
                "confidence": "low"
            }
        
        return state
    
    def _fallback_tool_selection(self, query: str) -> List[str]:
        """Fallback rule-based tool selection"""
        query_lower = query.lower().strip()
        tools = ["history"]  # Always include history
        
        # Check for general knowledge queries (NON-Stevens specific)
        general_indicators = ["what is", "explain", "define", "how does", "why", "concept", "theory", "meaning of life", "philosophy"]
        stevens_indicators = ["course", "cs", "class", "subject", "faculty", "professor", "admission", "requirement", "stevens", "institute", "university", "deep learning", "machine learning", "ai", "artificial intelligence", "data science", "computer science", "engineering", "program", "degree", "major", "minor", "dehnad", "professor"]
        
        # If it's a general knowledge query without Stevens context
        if any(indicator in query_lower for indicator in general_indicators) and not any(indicator in query_lower for indicator in stevens_indicators):
            tools.append("general")
            print(f"🔄 FALLBACK: Using general tool for general knowledge query")
        else:
            # Stevens-specific or mixed queries
            tools.append("chroma")
            print(f"🔄 FALLBACK: Using chroma tool for Stevens-specific query")
            
            # Add web for current/recent information
            current_indicators = ["current", "latest", "2024", "2025", "now", "recent", "contact", "phone", "email", "apply", "register", "available", "offer", "have", "provide", "teach", "include"]
            if any(indicator in query_lower for indicator in current_indicators):
                tools.append("web")
                print(f"🔄 FALLBACK: Adding web tool for current information")
        
        return tools
    
    async def _tools_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tools node - executes selected tools using ReAct pattern"""
        tool_decision = state.get("tool_decision", {})
        tools_to_use = tool_decision.get("tools", ["chroma"])
        primary_tool = tool_decision.get("primary_tool", "chroma")
        
        print(f"\n🔧 TOOLS: Executing tools using ReAct pattern")
        print(f"📋 TOOLS: Selected tools: {tools_to_use}")
        print(f"🎯 TOOLS: Primary tool: {primary_tool}")
        
        # Execute tools in parallel based on selection
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
        """Reasoning node - LLM decides if web search is needed using ReAct pattern"""
        query = state.get("query", "")
        tool_decision = state.get("tool_decision", {})
        
        print(f"\n🧠 REASON: Analyzing if web search is needed for: '{query}'")
        
        # Check if this is a simple query that doesn't need web search
        if tool_decision.get("simple_query", False):
            print(f"✅ REASON: Simple query detected - no web search needed")
            state["reasoning_result"] = {
                "need_web_search": False,
                "reasoning": "Simple query detected - no web search needed",
                "confidence": "high",
                "what_missing": "Nothing missing - simple query handled by general tool"
            }
            return state
        
        llm = self.llm_router.get_llm()
        
        # Gather available information from previous tools
        chroma_results = state.get("chroma_results", {})
        general_answer = state.get("general_answer")
        history_results = state.get("history_results", {})
        
        # Build context for reasoning
        available_info = []
        
        if chroma_results.get("documents"):
            available_info.append(f"Vector Database Results: Found {len(chroma_results['documents'])} documents")
            print(f"📊 REASON: Found {len(chroma_results.get('documents', []))} Chroma documents")
        
        if general_answer:
            available_info.append("General Knowledge Available")
            print(f"🧠 REASON: General knowledge available")
        
        if history_results.get("relevant_history"):
            available_info.append("Relevant History Available")
            print(f"📚 REASON: Relevant history available")
        
        context = "\n".join(available_info) if available_info else "No specific information available."
        
        # ReAct-style reasoning prompt
        reasoning_prompt = f"""
        You are an AI assistant that needs to decide whether to search the web for additional information about Stevens Institute of Technology.

        User Question: "{query}"

        Available Information:
        {context}

        Think step by step:
        1. What specific information is the user asking for?
        2. Do we have sufficient information from our database and general knowledge?
        3. What might be missing that would require web search?
        4. Is this a current/recent information request?

        Decision Guidelines:
        - Set need_web_search to true if:
          * The question asks for current/recent information (2024, 2025, upcoming, latest, etc.)
          * The question contains technical/procedural terms (apply, register, contact, email, phone, etc.)
          * The question asks for "what is", "tell me about", "information about" with likely current info needs
          * Available information is insufficient or unclear
          * The question requires external context not in the database
          * The user asks for specific details not covered
          * We have no or very few documents from the database
        - Set need_web_search to false if:
          * Available information is comprehensive and sufficient
          * The question is about general knowledge that's well covered
          * The answer can be provided from existing information
          * We have very good similarity scores (< 0.6) from vector database
          * It's a simple greeting or casual conversation
          * The general tool has provided a satisfactory answer
          * The question is basic and doesn't require current information

        Return ONLY a valid JSON object:
        {{
            "need_web_search": true/false,
            "reasoning": "step-by-step explanation of why web search is needed or not needed",
            "confidence": "high/medium/low",
            "what_missing": "what specific information might be missing",
            "available_sufficient": true/false
        }}
        """

        try:
            print(f"🤖 REASON: Using LLM to decide on web search...")
            response = await llm.ainvoke([{"role": "user", "content": reasoning_prompt}])
            
            print(f"📝 REASON: LLM response: {response.content[:200]}...")
            
            # Parse JSON response
            try:
                import json
                import re
                
                # Try to parse JSON
                try:
                    reasoning_result = json.loads(response.content.strip())
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        reasoning_result = json.loads(json_match.group())
                    else:
                        raise json.JSONDecodeError("No valid JSON found")
                
                state["reasoning_result"] = reasoning_result
                print(f"✅ REASON: LLM decided - Web search needed: {reasoning_result.get('need_web_search', False)}")
                print(f"📝 REASON: Reasoning: {reasoning_result.get('reasoning', 'No reasoning provided')}")
                print(f"📊 REASON: Confidence: {reasoning_result.get('confidence', 'Unknown')}")
                
            except Exception as parse_error:
                print(f"❌ REASON: Error parsing LLM response: {parse_error}")
                # Fallback reasoning - be more conservative about web search
                state["reasoning_result"] = {
                    "need_web_search": False,
                    "reasoning": f"Fallback due to parsing error: {parse_error}",
                    "confidence": "low",
                    "what_missing": "Unable to determine",
                    "available_sufficient": True
                }
                print(f"🔄 REASON: Fallback - no web search")
                
        except Exception as e:
            print(f"❌ REASON: Error in LLM reasoning: {str(e)}")
            # Fallback reasoning - be more conservative about web search
            state["reasoning_result"] = {
                "need_web_search": False,
                "reasoning": f"Fallback due to error: {str(e)}",
                "confidence": "low",
                "what_missing": "Unable to determine",
                "available_sufficient": True
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
        """Web search node - performs web search based on reasoning decision"""
        query = state.get("query", "")
        reasoning_result = state.get("reasoning_result", {})
        
        print(f"\n🌐 WEB: Starting web search based on reasoning decision")
        print(f"📝 WEB: Reasoning: {reasoning_result.get('reasoning', 'No reasoning')}")
        
        try:
            # Perform web search using the web agent
            web_results = await self.web_agent.process(state)
            
            if web_results.get("web_results", {}).get("success"):
                print(f"✅ WEB: Web search completed successfully")
                print(f"📊 WEB: Found web content: {len(web_results.get('web_results', {}).get('web_content', ''))} characters")
            else:
                print(f"⚠️  WEB: Web search completed but no results found")
            
            return web_results
            
        except Exception as e:
            print(f"❌ WEB: Error in web search: {str(e)}")
            return {
                "web_results": {
                    "success": False,
                    "error": str(e),
                    "web_content": "",
                    "urls": []
                }
            }
    
    async def _final_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Final node - synthesizes answer using ReAct pattern with all available information"""
        query = state.get("query", "")
        tool_decision = state.get("tool_decision", {})
        
        print(f"\n🎯 FINAL: Synthesizing answer using ReAct pattern")
        
        # Check if this is a simple query that needs direct response
        if tool_decision.get("simple_query", False):
            print(f"✅ FINAL: Simple query detected - using direct response")
            llm = self.llm_router.get_llm()
            
            # Simple response prompt for basic interactions
            simple_prompt = f"""
            You are a helpful AI assistant for Stevens Institute of Technology. 
            The user said: "{query}"
            
            Provide a brief, friendly, and appropriate response. Keep it short and natural.
            """
            
            try:
                response = await llm.ainvoke([{"role": "user", "content": simple_prompt}])
                answer = response.content.strip()
                print(f"✅ FINAL: Simple response generated: {answer[:100]}...")
                state["answer"] = answer
                return state
            except Exception as e:
                print(f"❌ FINAL: Error generating simple response: {str(e)}")
                # Fallback simple response
                state["answer"] = "You're welcome! How can I help you today?"
                return state
        
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
            for i, doc in enumerate(chroma_results["documents"][:5]):
                context_parts.append(f"Document {i+1}: {doc['content'][:200]}...")
            print(f"📊 FINAL: Using {len(chroma_results.get('documents', []))} Chroma documents")
        
        # Add web results
        if web_results.get("scraped_content") or web_results.get("web_content"):
            context_parts.append("Web Search Results:")
            web_content_to_show = web_results.get("scraped_content") or web_results.get("web_content")
            context_parts.append(web_content_to_show[:1000] + "...")
            print(f"🌐 FINAL: Using web search content")
        
        # Add general knowledge
        if general_answer:
            context_parts.append("General Knowledge:")
            context_parts.append(general_answer[:500] + "...")
            print(f"🧠 FINAL: Using general knowledge")
        
        # Add history
        if history_results.get("relevant_history"):
            context_parts.append("Previous Conversation Context (for reference only):")
            for i, entry in enumerate(history_results["relevant_history"][:5]):
                context_parts.append(f"Previous Q: {entry.get('query', 'Unknown')}")
                context_parts.append(f"Previous A: {entry.get('response', 'Unknown')[:100]}...")
            print(f"📚 FINAL: Using conversation history")
        
        # Add reasoning context
        if reasoning_result.get("reasoning"):
            context_parts.append("Reasoning Context:")
            context_parts.append(f"Web search needed: {reasoning_result.get('need_web_search', False)}")
            context_parts.append(f"Reasoning: {reasoning_result.get('reasoning', 'No reasoning')}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific information available."
        
        # ReAct-style final synthesis prompt
        final_prompt = f"""
        You are an AI assistant for Stevens Institute of Technology. Synthesize a comprehensive answer using all available information.

        User Question: "{query}"

        Available Information:
        {context}

        Instructions:
        1. **Answer the user's question directly and comprehensively**
        2. **Use information from the vector database (Stevens-specific data) as your primary source**
        3. **Supplement with web search results for current/recent information**
        4. **Use general knowledge for concepts and explanations**
        5. **Reference conversation history for context, but focus on the current question**
        6. **Be specific about Stevens Institute of Technology when relevant**
        7. **If information is not available, clearly state what you don't know**
        8. **Provide actionable information when possible**
        9. **Be concise but thorough**
        10. **Avoid speculation or making up information**

        Important Guidelines:
        - If the question is about Stevens courses, faculty, or programs, prioritize vector database results
        - If current information is needed (contact details, availability, recent updates), use web search results
        - If general concepts are asked, use general knowledge appropriately
        - If information is missing, be honest about limitations
        - Always prioritize accuracy over completeness

        Synthesize your answer:
        """

        try:
            print(f"🤖 FINAL: Using LLM to synthesize answer...")
            response = await llm.ainvoke([{"role": "user", "content": final_prompt}])
            
            answer = response.content.strip()
            print(f"✅ FINAL: Answer synthesized successfully")
            print(f"📝 FINAL: Answer length: {len(answer)} characters")
            
            state["answer"] = answer
            return state
            
        except Exception as e:
            print(f"❌ FINAL: Error synthesizing answer: {str(e)}")
            # Fallback answer
            state["answer"] = "I apologize, but I encountered an error while processing your request. Please try again."
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