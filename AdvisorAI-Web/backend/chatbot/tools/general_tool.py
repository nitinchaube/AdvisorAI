from typing import Dict, Any
from core.llm_router import LLMRouter
from config.settings import settings

class GeneralTool:
    """Tool for handling general knowledge questions"""
    
    def __init__(self):
        self.llm_router = LLMRouter()
    
    async def answer_general_question(self, query: str, context: str = "") -> Dict[str, Any]:
        """Answer general questions using LLM directly"""
        try:
            print(f"🧠 GENERAL: Processing query: '{query}'")
            llm = self.llm_router.get_llm()
            
            prompt = f"""
            You are a helpful AI assistant for Stevens Institute of Technology. Answer the following question.
            
            Question: {query}
            
            {f"Context: {context}" if context else ""}
            
            Instructions:
            1. Provide a clear, accurate, and helpful answer
            2. If the question is about Stevens Institute of Technology, use specific information
            3. For general questions, provide informative responses
            4. Be concise but thorough
            5. If you don't know something, say so clearly
            6. Avoid speculation or making up information
            
            Answer:
            """
            
            print(f"🤖 GENERAL: Using LLM to generate answer...")
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            print(f" GENERAL: Answer generated successfully")
            
            return {
                "answer": response.content,
                "query": query,
                "tool": "general",
                "success": True
            }
            
        except Exception as e:
            print(f" GENERAL: Error generating answer: {str(e)}")
            return {
                "error": f"General tool failed: {str(e)}",
                "success": False
            }
    
    async def classify_question_type(self, query: str) -> Dict[str, Any]:
        """Classify if a question is general or domain-specific"""
        try:
            llm = self.llm_router.get_llm()
            
            classification_prompt = f"""
            Classify the following question as either "general" or "domain_specific".
            
            Question: "{query}"
            
            Classification rules:
            - "general": Questions about general knowledge, concepts, definitions, or topics not specific to Stevens Institute of Technology
            - "domain_specific": Questions about Stevens Institute of Technology courses, faculty, programs, policies, or specific academic information
            
            Return ONLY the classification: "general" or "domain_specific"
            """
            
            response = await llm.ainvoke([{"role": "user", "content": classification_prompt}])
            classification = response.content.strip().lower()
            
            return {
                "classification": classification,
                "query": query,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": f"Classification failed: {str(e)}",
                "success": False
            }
    
    async def get_general_knowledge(self, topic: str) -> Dict[str, Any]:
        """Get general knowledge about a specific topic"""
        try:
            llm = self.llm_router.get_llm()
            
            knowledge_prompt = f"""
            Provide a brief overview of: {topic}
            
            Include:
            - Basic definition or explanation
            - Key concepts or points
            - Relevance to academic or general knowledge
            
            Keep it concise but informative.
            """
            
            response = await llm.ainvoke([{"role": "user", "content": knowledge_prompt}])
            
            return {
                "topic": topic,
                "knowledge": response.content,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": f"Knowledge retrieval failed: {str(e)}",
                "success": False
            } 