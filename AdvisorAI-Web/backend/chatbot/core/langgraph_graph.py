from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
import asyncio
import re
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
        
        # Initialize agentsG
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
        
        # Add nod"
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
        print(f"\nROUTER: Analyzing query for tool selection: '{query}'")
        
        llm = self.llm_router.get_llm()
        
        # Generate chat name for ALL queries (before simple query check)
        try:
            chat_name_prompt = f"""
            Generate a short, descriptive name for this chat session based on the user's query.
            
            User Query: "{query}"
            
            Create a concise name (3-8 words) that captures the main topic or intent of this conversation.
            
            Examples:
            - "How are you?" → "General Greeting & Introduction"
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
            print(f"ROUTER: Generated chat name: '{chat_name}'")
            state["chat_name"] = chat_name
            print(f"ROUTER: Set chat_name in state: '{state['chat_name']}'")
            
        except Exception as e:
            print(f"ROUTER: Error generating chat name: {str(e)}")
            state["chat_name"] = "New Chat"
            print(f"ROUTER: Set fallback chat_name in state: '{state['chat_name']}'")
        
        # Check if this is a simple query that can be answered directly
        try:
            simple_check_prompt = f"""
            Determine if this query is simple and can be answered directly without complex reasoning or tool usage.
            
            User Query: "{query}"
            
            A simple query is:
            - A basic greeting or introduction
            - A straightforward question about general concepts
            - Something that doesn't require Stevens-specific information
            - A question that can be answered with general knowledge
            
            Examples of simple queries:
            - "How are you?" → Simple greeting
            - "What is machine learning?" → Simple concept explanation
            - "Hello" → Simple greeting
            - "Thank you" → Simple acknowledgment
            
            Examples of complex queries:
            - "Tell me about Professor Dehnad" → Requires Stevens-specific data
            - "What courses are available in computer science?" → Requires course database
            - "How do I apply for admission?" → Requires Stevens-specific information
            
            Return ONLY a valid JSON object:
            {{
                "is_simple": true/false,
                "reasoning": "brief explanation of why this is simple or complex"
            }}
            """
            
            print(f"ROUTER: Checking if query is simple...")
            response = await llm.ainvoke([{"role": "user", "content": simple_check_prompt}])
            
            print(f"ROUTER: Simple check response: {response.content[:200]}...")
            
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
                
                print(f"ROUTER: Simple check - {is_simple}: {reasoning}")
                
                # If it's a simple query, use general tool directly
                if is_simple:
                    print(f"ROUTER: Simple query detected - using general tool directly")
                    state["tool_decision"] = {
                        "tools": ["general", "history"],
                        "primary_tool": "general",
                        "reasoning": f"Simple query detected: {reasoning}",
                        "confidence": "high",
                        "simple_query": True
                    }
                    return state
                
            except Exception as parse_error:
                print(f"ROUTER: Error parsing simple check response: {parse_error}")
                # Continue with normal ReAct flow if parsing fails
        
        except Exception as e:
            print(f"ROUTER: Error in simple query check: {str(e)}")
            # Continue with normal ReAct flow if simple check fails
        
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
        - "try again with my previous question" → {{"tools": ["history"], "primary_tool": "history"}}
        - "what about my last question" → {{"tools": ["history"], "primary_tool": "history"}}
        - "repeat that" → {{"tools": ["history"], "primary_tool": "history"}}
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
                
                print(f"ROUTER: Selected tools: {tools}")
                print(f"ROUTER: Primary tool: {primary_tool}")
                print(f"ROUTER: Reasoning: {reasoning[:100]}...")
                print(f"ROUTER: Confidence: {confidence}")
                
                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": primary_tool,
                    "reasoning": reasoning,
                    "confidence": confidence
                }
                
            except Exception as parse_error:
                print(f"ROUTER: Error parsing LLM response: {parse_error}")
                # Fallback to rule-based selection
                tools = self._fallback_tool_selection(query)
                state["tool_decision"] = {
                    "tools": tools,
                    "primary_tool": tools[0] if tools else "chroma",
                    "reasoning": "Fallback rule-based selection",
                    "confidence": "low"
                }
                
        except Exception as e:
            print(f"ROUTER: Error in LLM tool selection: {str(e)}")
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
        
        tools.append("general")

        return tools
    
    async def _tools_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tools node - executes selected tools using ReAct pattern"""
        tool_decision = state.get("tool_decision", {})
        tools_to_use = tool_decision.get("tools", ["chroma"])
        primary_tool = tool_decision.get("primary_tool", "chroma")
        
        print(f"\TOOLS: Executing tools using ReAct pattern")
        print(f" TOOLS: Selected tools: {tools_to_use}")
        print(f" TOOLS: Primary tool: {primary_tool}")
        
        # Execute tools in parallel based on selection
        tasks = []
        
        if "chroma" in tools_to_use:
            print(f"TOOLS: Starting Chroma search...")
            tasks.append(self.chroma_agent.process(state))
        
        if "history" in tools_to_use:
            print(f"TOOLS: Starting History search...")
            tasks.append(self.history_agent.process(state))
        
        if "general" in tools_to_use:
            print(f"TOOLS: Starting General knowledge...")
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
            available_info.append(f"Found {len(chroma_results['documents'])} relevant information sources")
            print(f"📊 REASON: Found {len(chroma_results.get('documents', []))} information sources")
        
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
        2. Is this a follow-up question that should use existing history?
        3. Do we have sufficient information from our database and general knowledge?
        4. What might be missing that would require web search?
        5. Is this a current/recent information request?

        Decision Guidelines:
        - Set need_web_search to true if:
          * The question asks for current/recent information (2024, 2025, upcoming, latest, etc.)
          * The question contains technical/procedural terms (apply, register, contact, email, phone, etc.)
          * The question asks for "what is", "tell me about", "information about" with likely current info needs
          * Available information is insufficient or unclear
          * The question requires external context not in available information
          * The user asks for specific details not covered
          * We have no or very few relevant information sources
          * The question asks for specific professor contact information or current availability
          * The question asks for current course offerings or schedules
        - Set need_web_search to false if:
          * Available information is comprehensive and sufficient
          * The question is about general knowledge that's well covered
          * The answer can be provided from existing information
          * We have very good similarity scores (< 0.6) from available information
          * It's a simple greeting or casual conversation
          * The general tool has provided a satisfactory answer
          * The question is basic and doesn't require current information
          * It's a follow-up question (try again, check again, repeat, what about, etc.)
          * The user is asking to rephrase or clarify a previous answer
          * The question refers to "my previous question" or "last question"
          * The question asks to "try again" or "check again"
          * We have relevant history available and the question is about previous context

        Examples:
        - "try again with my previous question" → need_web_search: false (use history)
        - "check again" → need_web_search: false (use history)
        - "what about my last question" → need_web_search: false (use history)
        - "repeat that" → need_web_search: false (use history)
        - "tell me about Professor Dehnad" → need_web_search: true (current info needed)
        - "what courses are available in 2025" → need_web_search: true (current info needed)
        - "what is machine learning" → need_web_search: false (general knowledge)
        - "how do I apply for admission" → need_web_search: true (current process needed)

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
                
                # If web search is needed, generate a specific search query
                if reasoning_result.get('need_web_search', False):
                    web_query = await self._generate_web_search_query(query, history_results, chroma_results, general_answer)
                    state["web_search_query"] = web_query
                    print(f"🔍 REASON: Generated web search query: '{web_query}'")
                
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
    
    async def _generate_web_search_query(self, original_query: str, history_results: Dict, chroma_results: Dict, general_answer: str) -> str:
        """Generate a specific web search query based on conversation context and available information"""
        llm = self.llm_router.get_llm()
        
        # Build conversation context
        conversation_context = ""
        if history_results.get("relevant_history"):
            conversation_context = "Conversation History:\n"
            for i, entry in enumerate(history_results["relevant_history"][-3:]):  # Last 3 conversations
                conversation_context += f"Q{i+1}: {entry.get('query', 'Unknown')}\n"
                conversation_context += f"A{i+1}: {entry.get('response', 'Unknown')[:200]}...\n"
        
        # Build available information context
        available_info = []
        if chroma_results.get("documents"):
            available_info.append(f"Found {len(chroma_results['documents'])} relevant information sources")
        if general_answer:
            available_info.append("General knowledge available")
        
        context_info = "\n".join(available_info) if available_info else "No specific information available"
        
        web_query_prompt = f"""
        You are an AI assistant that needs to generate a specific, targeted web search query for Stevens Institute of Technology information.

        Original User Question: "{original_query}"

        {conversation_context}

        Available Information:
        {context_info}

        Your task is to create a specific web search query that will find the most relevant and current information to answer the user's question.

        Guidelines for creating the search query:
        1. **Make it specific and targeted** - don't use vague terms
        2. **Include "Stevens Institute of Technology"** if the question is about Stevens
        3. **Use specific keywords** that would appear in relevant web pages
        4. **Include current year (2024/2025)** if asking about current information
        5. **Use proper names** (professor names, course names, department names) if mentioned
        6. **Include action words** (apply, contact, register, admission) if relevant
        7. **Keep it concise** but comprehensive (3-8 words typically work best)
        8. **Consider the conversation context** - if this is a follow-up, make the query more specific

        Examples of good web search queries:
        - "Professor Dehnad Stevens Institute of Technology contact email 2024"
        - "Stevens Institute of Technology computer science courses 2025"
        - "Stevens Institute of Technology admission requirements application deadline"
        - "Stevens Institute of Technology machine learning faculty research"
        - "Stevens Institute of Technology graduate programs application process"
        - "Stevens Institute of Technology campus location address"

        Generate a specific web search query that will find the most relevant information:

        Web Search Query:
        """
        
        try:
            print(f"🔍 REASON: Generating specific web search query...")
            response = await llm.ainvoke([{"role": "user", "content": web_query_prompt}])
            
            web_query = response.content.strip()
            # Clean up the query
            web_query = web_query.replace('"', '').replace("'", "").strip()
            
            # Fallback to original query if generation fails
            if not web_query or len(web_query) < 5:
                web_query = f"{original_query} Stevens Institute of Technology"
                print(f"⚠️ REASON: Web query generation failed, using fallback: '{web_query}'")
            else:
                print(f"✅ REASON: Generated specific web search query: '{web_query}'")
            
            return web_query
            
        except Exception as e:
            print(f"❌ REASON: Error generating web search query: {str(e)}")
            # Fallback to enhanced original query
            fallback_query = f"{original_query} Stevens Institute of Technology"
            print(f"🔄 REASON: Using fallback web search query: '{fallback_query}'")
            return fallback_query
    
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
        original_query = state.get("query", "")
        web_search_query = state.get("web_search_query", original_query)
        reasoning_result = state.get("reasoning_result", {})
        
        print(f"\n🌐 WEB: Starting web search based on reasoning decision")
        print(f"📝 WEB: Original query: '{original_query}'")
        print(f"🔍 WEB: Generated search query: '{web_search_query}'")
        print(f"📝 WEB: Reasoning: {reasoning_result.get('reasoning', 'No reasoning')}")
        
        try:
            # Create a modified state with the generated web search query
            web_search_state = state.copy()
            web_search_state["query"] = web_search_query  # Use the generated query for web search
            
            # Perform web search using the web agent with the generated query
            web_results = await self.web_agent.process(web_search_state)
            
            # Add the original query back to the results for context
            if web_results.get("web_results"):
                web_results["web_results"]["original_query"] = original_query
                web_results["web_results"]["search_query_used"] = web_search_query
            
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
                    "urls": [],
                    "original_query": original_query,
                    "search_query_used": web_search_query
                }
            }
    
    async def _final_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Final node - synthesizes answer using ReAct pattern with all available information"""
        query = state.get("query", "")
        tool_decision = state.get("tool_decision", {})
        
        print(f"\n🎯 FINAL: Synthesizing answer using ReAct pattern")
        
        # Check if this is a simple query that needs direct response
        if tool_decision.get("simple_query", False):
            print(f"✅ FINAL: Simple query detected - using direct response with conversation context")
            llm = self.llm_router.get_llm()
            
            # Get conversation history for context even in simple queries
            history_results = state.get("history_results", {})
            history_context = ""
            if history_results.get("relevant_history"):
                history_context = "\n\nConversation History:\n"
                for i, entry in enumerate(history_results["relevant_history"]):
                    history_context += f"Q{i+1}: {entry.get('query', 'Unknown')}\n"
                    history_context += f"A{i+1}: {entry.get('response', 'Unknown')}\n"
            
            # Simple response prompt for basic interactions with conversation context
            simple_prompt = f"""
            You are a helpful academic advisor for Stevens Institute of Technology. 
            You are having a conversation with a user.
            
            Current user message: "{query}"
            {history_context}
            
            Provide a helpful, informative, and appropriate response that considers the conversation context. 
            Be conversational and provide useful information when possible. If you can answer their question directly, do so comprehensively.
            If you need more information to help them, ask clarifying questions.
            
            IMPORTANT: Provide ONLY your direct response to the user. Do not include any reasoning, thinking process, or internal thoughts. Just give the direct answer as if you're responding in a normal conversation.
            
            Response:
            """
            
            try:
                response = await llm.ainvoke([{"role": "user", "content": simple_prompt}])
                answer = response.content.strip()
                print(f"FINAL: Simple response generated with context: {answer[:100]}...")
                state["answer"] = answer
                return state
            except Exception as e:
                print(f"FINAL: Error generating simple response: {str(e)}")
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
        
        # Check if this is a follow-up question and handle it specially
        is_follow_up = history_results.get("is_follow_up", False)
        if is_follow_up and history_results.get("relevant_history"):
            print(f"🔄 FINAL: Detected follow-up question, using history directly")
            # For follow-up questions, use the most recent history entry
            latest_history = history_results["relevant_history"][-1] if history_results["relevant_history"] else None
            if latest_history:
                previous_query = latest_history.get("query", "")
                previous_response = latest_history.get("response", "")
                
                # Create a direct response for follow-up questions
                follow_up_prompt = f"""
                The user is asking a follow-up question: "{query}"
                
                Based on the conversation history, their previous question was: "{previous_query}"
                And your previous answer was: "{previous_response}"
                
                For follow-up questions like "try again with my previous question", "check again", etc., 
                provide the same information from your previous response, but you can add any additional 
                relevant information if needed.
                
                IMPORTANT: Provide ONLY your direct response to the user. Do not include any reasoning, thinking process, or internal thoughts. Just give the direct answer as if you're responding in a normal conversation.
                
                Response:
                """
                
                try:
                    response = await llm.ainvoke([{"role": "user", "content": follow_up_prompt}])
                    answer = response.content.strip()
                    print(f"✅ FINAL: Follow-up response generated using history")
                    state["answer"] = answer
                    return state
                except Exception as e:
                    print(f"❌ FINAL: Error generating follow-up response: {str(e)}")
                    # Fallback to previous response
                    state["answer"] = previous_response
                    return state
        
        # Build comprehensive context
        context_parts = []
        
        # Add available information
        if chroma_results.get("documents"):
            context_parts.append("Available Information:")
            for i, doc in enumerate(chroma_results["documents"][:5]):
                context_parts.append(f"[{i+1}]: {doc['content']}")
            print(f"📊 FINAL: Using {len(chroma_results.get('documents', []))} information sources")
        
        # Add web results
        if web_results.get("scraped_content") or web_results.get("web_content"):
            context_parts.append("Additional Information:")
            web_content_to_show = web_results.get("scraped_content") or web_results.get("web_content")
            
            # Clean web content to remove any JSON artifacts
            if web_content_to_show:
                # Remove any remaining JSON-like artifacts
                web_content_to_show = re.sub(r'Source:\s*https?://[^\s]+\s*', '', web_content_to_show)
                web_content_to_show = re.sub(r'---\s*', ' ', web_content_to_show)
                web_content_to_show = re.sub(r'\s+', ' ', web_content_to_show).strip()
            
            context_parts.append(web_content_to_show[:1000] + "...")
            print(f"🌐 FINAL: Using web search content")
        
        # Add general knowledge
        if general_answer:
            context_parts.append("General Knowledge:")
            context_parts.append(general_answer[:500] + "...")
            print(f"🧠 FINAL: Using general knowledge")
        
        # Add history - structure it as a proper conversation flow
        if history_results.get("relevant_history"):
            context_parts.append("CONVERSATION HISTORY (Use this context to understand the conversation flow):")
            print(f"📚 FINAL: Found {len(history_results['relevant_history'])} history entries")
            
            # Structure the conversation as Q1, A1, Q2, A2, Q3, A3, etc.
            for i, entry in enumerate(history_results["relevant_history"]):
                context_parts.append(f"Q{i+1}: {entry.get('query', 'Unknown')}")
                context_parts.append(f"A{i+1}: {entry.get('response', 'Unknown')}")
                print(f"📚 FINAL: History entry {i+1}: Q='{entry.get('query', 'Unknown')[:50]}...' A='{entry.get('response', 'Unknown')[:50]}...'")
            
            # Add current question as the next in sequence
            context_parts.append(f"Q{len(history_results['relevant_history'])+1}: {query}")
            context_parts.append("(You need to provide A{len(history_results['relevant_history'])+1} - the answer to this question)")
            
            print(f"📚 FINAL: Using conversation history with {len(history_results['relevant_history'])} previous Q&A pairs")
            print(f"📚 FINAL: Is follow-up: {history_results.get('is_follow_up', False)}")
        else:
            print(f"⚠️ FINAL: No relevant history found")
            print(f"📚 FINAL: History results keys: {list(history_results.keys()) if history_results else 'None'}")
        
        # Add reasoning context
        if reasoning_result.get("reasoning"):
            context_parts.append("Reasoning Context:")
            context_parts.append(f"Web search needed: {reasoning_result.get('need_web_search', False)}")
            context_parts.append(f"Reasoning: {reasoning_result.get('reasoning', 'No reasoning')}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific information available."
        
        # ReAct-style final synthesis prompt
        final_prompt = f"""
        You are a helpful academic advisor for Stevens Institute of Technology. Your goal is to provide comprehensive, accurate, and useful information to help students with their questions.

        Current User Question: "{query}"

        Available Information:
        {context}

        INSTRUCTIONS:
        1. **Provide a complete and helpful answer using all available information**
        2. **If information is available in the context, provide it directly and comprehensively**
        3. **If you have partial information, provide what you know and mention what additional details might be helpful**
        4. **Include specific details, dates, requirements, or other concrete information when available**
        5. **Include relevant links or sources for credibility and further reference**
        6. **Be conversational and helpful - provide actionable information rather than just directing users to websites**
        7. **If the answer is not present in the context, provide a helpful response and suggest where they might find more information**
        8. **Use conversation history to understand context and provide relevant, contextual answers**
        9. **Reference previous questions and answers when relevant to provide better context**
        10. **Be specific about Stevens Institute of Technology when relevant**

        CONVERSATION CONTEXT USAGE:
        - **ALWAYS consider the conversation history when answering**
        - **If the current question relates to previous questions, reference that context**
        - **If the user asks follow-up questions, use the conversation flow to provide better answers**
        - **If the question is about something mentioned before, build upon previous answers**
        - **Maintain conversation continuity and coherence**

        Special Handling for Follow-up Questions:
        - If the user says "try again with my previous question", find the most recent question in the conversation history and provide that answer again
        - If the user says "check again", look at the most recent conversation and repeat or clarify that information
        - If the user says "what about my last question", find the most recent question and provide the answer
        - If the user says "repeat that", find the most recent answer and repeat it
        - For these follow-up questions, DO NOT ask the user to provide the question - use the conversation history to find it
        - If you find relevant previous questions in the history, provide those answers directly
        - If no relevant history is found, then ask the user to clarify what they want to know

        Remember: You are part of an ongoing conversation. Use the context to provide the most relevant and helpful answer.

        IMPORTANT: Provide ONLY your final answer to the user's question. Do not include any reasoning, thinking process, or internal thoughts. Just give the direct answer as if you're responding in a normal conversation.

        Answer:
        """

        try:
            print(f"🤖 FINAL: Using LLM to synthesize answer...")
            response = await llm.ainvoke([{"role": "user", "content": final_prompt}])
            
            answer = response.content.strip()
            
            # Clean up any reasoning text that might have slipped through
            answer = self._clean_response_text(answer)
            
            print(f"✅ FINAL: Answer synthesized successfully")
            print(f"📝 FINAL: Answer length: {len(answer)} characters")
            
            state["answer"] = answer
            return state
            
        except Exception as e:
            print(f"FINAL: Error synthesizing answer: {str(e)}")
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
                    "reasoning_result": final_state.get("reasoning_result", {}),
                    "chat_name": final_state.get("chat_name", "New Chat")  # Include chat_name in metadata
                }
            }
            
            print(f"📝 LangGraph: Final state keys: {list(final_state.keys())}")
            print(f"📝 LangGraph: chat_name in final_state: '{final_state.get('chat_name', 'NOT_FOUND')}'")
            print(f"📝 LangGraph: chat_name in result metadata: '{result['metadata']['chat_name']}'")
            print(f"📝 LangGraph: Returning result with chat_name: '{result['metadata']['chat_name']}'")
            
            print(f"✅ PROCESS: Returning result with answer length: {len(answer)}")
            return result
            
        except Exception as e:
            print(f"❌ PROCESS: Error in query processing: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment."
            }
    
    def _clean_response_text(self, text: str) -> str:
        """Clean response text by removing reasoning artifacts and formatting issues"""
        if not text:
            return ""
        
        # Remove common reasoning artifacts that might slip through
        reasoning_patterns = [
            r"Let me think about this\.\.\.",
            r"I need to consider\.\.\.",
            r"Based on my analysis\.\.\.",
            r"Let me analyze this\.\.\.",
            r"I should look into this\.\.\.",
            r"Let me check\.\.\.",
            r"I'll need to\.\.\.",
            r"First, let me\.\.\.",
            r"To answer this\.\.\.",
            r"Looking at this\.\.\.",
            r"I can see that\.\.\.",
            r"From what I can tell\.\.\.",
            r"It appears that\.\.\.",
            r"I notice that\.\.\.",
            r"Based on the information\.\.\.",
            r"According to the data\.\.\.",
            r"The information shows\.\.\.",
            r"I can determine that\.\.\.",
            r"After reviewing\.\.\.",
            r"Upon examination\.\.\.",
        ]
        
        # Remove reasoning patterns
        for pattern in reasoning_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Replace multiple newlines with double newline
        text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove any remaining reasoning artifacts at the start
        text = re.sub(r'^(Let me|I need to|Based on|I should|I\'ll|First|To answer|Looking|I can see|From what|It appears|I notice|According to|The information|I can determine|After|Upon).*?\.\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Ensure the response doesn't start with lowercase (indicating incomplete sentence)
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Remove any trailing incomplete sentences
        text = re.sub(r'\.\s*$', '.', text)
        
        return text.strip() 