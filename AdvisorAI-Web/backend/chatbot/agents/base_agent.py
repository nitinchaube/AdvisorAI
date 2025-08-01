from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain.schema import BaseMessage

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state"""
        pass
    
    def get_name(self) -> str:
        """Get the agent name"""
        return self.name 