import requests
import json
import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from config.settings import settings

class LocalLLM(BaseLanguageModel):
    """Custom LLM class for local Mistral API"""
    
    def __init__(self):
        super().__init__()
        self.api_url = settings.LOCAL_LLM_URL
        self.model = settings.LOCAL_LLM_MODEL
        self.temperature = settings.LOCAL_LLM_TEMPERATURE
        self.max_tokens = settings.LOCAL_LLM_MAX_TOKENS
        print(f"🏠 Local LLM initialized: {self.api_url} with model {self.model}")
    
    @property
    def _llm_type(self) -> str:
        return "local_mistral"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Synchronous call to local LLM"""
        messages = [{"role": "user", "content": prompt}]
        response = self._make_request(messages, **kwargs)
        return response
    
    async def _acall(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Asynchronous call to local LLM"""
        messages = [{"role": "user", "content": prompt}]
        response = await self._make_request_async(messages, **kwargs)
        return response
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
        """Invoke the LLM with a list of messages"""
        # Convert LangChain messages to API format
        api_messages = self._convert_messages_to_api_format(messages)
        response = self._make_request(api_messages, **kwargs)
        
        # Create ChatResult
        generation = ChatGeneration(message=AIMessage(content=response))
        return ChatResult(generations=[generation])
    
    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
        """Asynchronous invoke the LLM with a list of messages"""
        # Convert LangChain messages to API format
        api_messages = self._convert_messages_to_api_format(messages)
        response = await self._make_request_async(api_messages, **kwargs)
        
        # Create ChatResult
        generation = ChatGeneration(message=AIMessage(content=response))
        return ChatResult(generations=[generation])
    
    def _convert_messages_to_api_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to API format"""
        api_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                api_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                api_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                api_messages.append({"role": "system", "content": message.content})
        return api_messages
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make synchronous request to local LLM API"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }
            
            print(f"�� Local LLM Request: {len(messages)} messages")
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ Local LLM Response: {len(content)} characters")
                return content
            else:
                error_msg = f"Local LLM API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"❌ Local LLM request failed: {str(e)}")
            raise e
    
    async def _make_request_async(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make asynchronous request to local LLM API"""
        try:
            import aiohttp
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }
            
            print(f"🏠 Local LLM Async Request: {len(messages)} messages")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        print(f"✅ Local LLM Async Response: {len(content)} characters")
                        return content
                    else:
                        error_text = await response.text()
                        error_msg = f"Local LLM API error: {response.status} - {error_text}"
                        print(f"❌ {error_msg}")
                        raise Exception(error_msg)
                        
        except Exception as e:
            print(f"❌ Local LLM async request failed: {str(e)}")
            raise e
