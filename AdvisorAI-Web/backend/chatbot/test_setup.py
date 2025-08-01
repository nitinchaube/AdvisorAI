#!/usr/bin/env python3
"""
Simple test script to verify chatbot setup and imports
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports to ensure they work correctly"""
    print("Testing imports...")
    
    try:
        # Test config imports
        from config.settings import settings
        print("✅ Config imports successful")
        
        # Test core imports
        from core.llm_router import LLMRouter
        from core.memory_store import get_memory_store
        print("✅ Core imports successful")
        
        # Test tools imports
        from tools.chroma_tool import ChromaTool
        from tools.web_tool import WebTool
        from tools.history_tool import HistoryTool
        from tools.general_tool import GeneralTool
        print("✅ Tools imports successful")
        
        # Test agents imports
        from agents.base_agent import BaseAgent
        from agents.chroma_agent import ChromaAgent
        from agents.web_agent import WebAgent
        from agents.history_agent import HistoryAgent
        from agents.general_agent import GeneralAgent
        print("✅ Agents imports successful")
        
        # Test main orchestrator
        from core.langgraph_graph import LangGraphOrchestrator
        print("✅ LangGraph orchestrator import successful")
        
        print("\n🎉 All imports successful! The chatbot setup is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without requiring API keys"""
    print("\nTesting basic functionality...")
    
    try:
        # Test settings
        from config.settings import settings
        print(f"✅ Settings loaded: LLM_PROVIDER={settings.LLM_PROVIDER}")
        
        # Test memory store
        from core.memory_store import get_memory_store
        memory_store = get_memory_store()
        print("✅ Memory store initialized")
        
        # Test tools initialization
        from tools.chroma_tool import ChromaTool
        chroma_tool = ChromaTool()
        print("✅ Chroma tool initialized")
        
        print("\n🎉 Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing chatbot setup...")
    print("=" * 50)
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    print("\n" + "=" * 50)
    if imports_ok and functionality_ok:
        print("✅ All tests passed! The chatbot is ready to use.")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python example_usage.py")
        print("3. Or run: python main.py to start the API server")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 