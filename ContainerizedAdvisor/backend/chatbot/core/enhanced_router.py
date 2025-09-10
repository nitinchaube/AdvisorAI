import json
import re
from typing import Dict, Any, List

class EnhancedRouter:
    """Enhanced router that handles local LLM responses better"""
    
    @staticmethod
    def parse_llm_response(response_content: str) -> Dict[str, Any]:
        """Parse LLM response with multiple fallback strategies"""
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(response_content.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown
        try:
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract tools array
        try:
            tools_match = re.search(r'"tools":\s*\[[^\]]+\]', response_content)
            if tools_match:
                tools_str = tools_match.group()
                tools = json.loads(f"{{{tools_str}}}")["tools"]
                return {
                    "tools": tools,
                    "primary_tool": tools[0] if tools else "chroma",
                    "reasoning": "Extracted from partial JSON",
                    "confidence": "medium"
                }
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Extract individual fields
        try:
            tools = []
            if '"chroma"' in response_content.lower():
                tools.append("chroma")
            if '"general"' in response_content.lower():
                tools.append("general")
            if '"web"' in response_content.lower():
                tools.append("web")
            if '"history"' in response_content.lower():
                tools.append("history")
            
            if not tools:
                tools = ["chroma"]  # Default
            
            return {
                "tools": tools,
                "primary_tool": tools[0],
                "reasoning": "Extracted from text analysis",
                "confidence": "low"
            }
        except Exception:
            pass
        
        # Strategy 5: Fallback to rule-based
        return None
    
    @staticmethod
    def validate_tool_decision(tool_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix tool decision"""
        valid_tools = ["general", "chroma", "web", "history"]
        
        # Ensure tools list exists and is valid
        tools = tool_decision.get("tools", ["chroma"])
        if not isinstance(tools, list):
            tools = ["chroma"]
        
        # Filter valid tools
        tools = [tool for tool in tools if tool in valid_tools]
        if not tools:
            tools = ["chroma"]
        
        # Ensure history is always included
        if "history" not in tools:
            tools.append("history")
        
        # Set primary tool
        primary_tool = tool_decision.get("primary_tool", tools[0])
        if primary_tool not in valid_tools:
            primary_tool = tools[0]
        
        return {
            "tools": tools,
            "primary_tool": primary_tool,
            "reasoning": tool_decision.get("reasoning", "Validated tool selection"),
            "confidence": tool_decision.get("confidence", "medium")
        } 