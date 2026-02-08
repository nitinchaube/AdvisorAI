from typing import List, Dict, Any
from core.memory_store import get_memory_store

class HistoryTool:
    """Tool for accessing conversation history"""
    
    def __init__(self):
        self.memory_store = get_memory_store()
    
    async def get_relevant_history(self, user_id: str, current_query: str, limit: int = 3, provided_history: str = "") -> Dict[str, Any]:
        """Get relevant conversation history for the current query"""
        try:
            # If provided history is available, use it
            if provided_history:
                print(f"📚 HISTORY: Using provided chat history for context")
                print(f"📚 HISTORY: Raw history length: {len(provided_history)} characters")
                # Parse the provided history format (Q: ... A: ...)
                history_entries = []
                lines = provided_history.split('\n')
                current_entry = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    if line.startswith('Q: '):
                        if current_entry and current_entry.get('query'):
                            history_entries.append(current_entry)
                        current_entry = {'query': line[3:].strip(), 'response': ''}
                    elif line.startswith('A: ') and current_entry:
                        current_entry['response'] = line[3:].strip()
                    elif current_entry and current_entry.get('query'):
                        # Handle multi-line responses
                        if current_entry.get('response'):
                            current_entry['response'] += ' ' + line
                
                if current_entry and current_entry.get('query'):
                    history_entries.append(current_entry)
                
                print(f"📚 HISTORY: Parsed {len(history_entries)} history entries")
                
                # Always return the last 3 conversations for context
                relevant_history = history_entries[-limit:] if history_entries else []
                
                if relevant_history:
                    print(f"📚 HISTORY: Returning {len(relevant_history)} relevant history entries")
                    for i, entry in enumerate(relevant_history, 1):
                        print(f"📚 HISTORY: Entry {i}: Q='{entry.get('query', '')[:50]}...' A='{entry.get('response', '')[:50]}...'")
                else:
                    print(f"⚠️ HISTORY: No relevant history entries found after parsing")
                
                return {
                    "relevant_history": relevant_history,
                    "total_history": len(history_entries),
                    "relevant_count": len(relevant_history),
                    "current_query": current_query,
                    "is_follow_up": self._is_follow_up_query(current_query),
                    "source": "provided",
                    "purpose": "conversation_context"
                }
            
            # Otherwise, fetch from memory store
            history = await self.memory_store.get_conversation_history(user_id, limit=limit)
            
            # Always return the last 3 conversations for context
            relevant_history = history[-limit:] if history else []
            is_follow_up = self._is_follow_up_query(current_query)
            
            print(f"📚 HISTORY: Returning last {len(relevant_history)} conversations for context")
            
            return {
                "relevant_history": relevant_history,
                "total_history": len(history),
                "relevant_count": len(relevant_history),
                "current_query": current_query,
                "is_follow_up": is_follow_up,
                "source": "memory",
                "purpose": "conversation_context"
            }
            
        except Exception as e:
            print(f"HISTORY: Error getting history: {str(e)}")
            return {
                "error": f"Failed to get history: {str(e)}",
                "relevant_history": [],
                "total_history": 0,
                "relevant_count": 0,
                "is_follow_up": False,
                "source": "error",
                "purpose": "context_reference_only"
            }
    
    def _is_follow_up_query(self, query: str) -> bool:
        """Check if a query is a follow-up question"""
        follow_up_indicators = [
            "check again", "check", "again", "more", "what else", "tell me more", 
            "additional", "further", "expand", "elaborate", "details", "specifically",
            "continue", "go on", "and?", "what about", "how about", "can you tell me more",
            "give me more", "show me more", "explain more", "describe more",
            "try again", "repeat", "rephrase", "clarify", "previous question",
            "last question", "my previous question", "what about my last question",
            "repeat that", "say that again", "can you repeat", "what was that",
            "remind me", "recall", "remember", "what did you say", "can you clarify",
            "previous questions", "my previous questions", "tell me about my previous",
            "what questions did i ask", "what did i ask", "show me my questions",
            "list my questions", "past questions", "conversation history", "chat history"
        ]
        
        query_lower = query.lower().strip()
        
        # Check for exact matches
        if any(indicator in query_lower for indicator in follow_up_indicators):
            return True
        
        # Check for pronouns that indicate follow-up
        follow_up_pronouns = ["it", "this", "that", "these", "those", "them", "they"]
        words = query_lower.split()
        if len(words) <= 3 and any(word in follow_up_pronouns for word in words):
            return True
        
        # Check for short queries that might be follow-ups
        if len(query_lower) <= 20 and any(word in query_lower for word in ["more", "else", "and", "what", "how", "why"]):
            return True
        
        # Check for specific follow-up patterns
        follow_up_patterns = [
            "try again with",
            "check again",
            "what about",
            "tell me more about",
            "can you repeat",
            "say that again",
            "remind me",
            "what was",
            "can you clarify"
        ]
        
        for pattern in follow_up_patterns:
            if pattern in query_lower:
                return True
        
        return False
    
    async def save_conversation(self, user_id: str, query: str, response: str, metadata: Dict = None):
        """Save a conversation turn to memory"""
        try:
            await self.memory_store.save_conversation(user_id, query, response, metadata)
            return {"success": True, "message": "Conversation saved"}
        except Exception as e:
            return {"error": f"Failed to save conversation: {str(e)}"}
    
    async def clear_history(self, user_id: str) -> Dict[str, Any]:
        """Clear conversation history for a user"""
        try:
            await self.memory_store.clear_history(user_id)
            return {"success": True, "message": "History cleared"}
        except Exception as e:
            return {"error": f"Failed to clear history: {str(e)}"} 