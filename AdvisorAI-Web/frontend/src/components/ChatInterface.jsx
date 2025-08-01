import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Paperclip, Mic, History, Info, Plus } from "lucide-react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { chatCache } from '../utils/chatCache';

// Simple markdown renderer component
const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  // Convert markdown to HTML-like JSX
  const renderMarkdown = (text) => {
    // Bold text: **text** or __text__
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Italic text: *text* or _text_
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Links: [text](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>');
    
    // Numbered lists: 1. item
    text = text.replace(/^(\d+\.\s+)(.*)$/gm, '<li class="list-decimal ml-4">$2</li>');
    
    // Bullet lists: * item or - item
    text = text.replace(/^[\*\-]\s+(.*)$/gm, '<li class="list-disc ml-4">$1</li>');
    
    // Headers: # Header
    text = text.replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');
    
    // Code blocks: `code`
    text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Line breaks
    text = text.replace(/\n/g, '<br />');
    
    return text;
  };

  const processedContent = renderMarkdown(content);

  return (
    <div 
      className="text-sm leading-relaxed"
      dangerouslySetInnerHTML={{ __html: processedContent }}
    />
  );
};

const ChatInterface = ({ 
  onToggleHistory, 
  currentSessionId,   onSessionUpdate,
  sessionTitle = "AI Academic Advisor",
  onNewChat
}) => {
  const { currentUser } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [currentSources, setCurrentSources] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Load messages for current session
  const loadSessionMessages = async (sessionId) => {
    if (!sessionId) {
      // No session selected, show welcome message
      setMessages([
        {
          id: 1,
          type: 'ai',
          content: "Hello! I'm your AI academic advisor. I can help you with course selection, professor recommendations, academic planning, and much more. What would you like to know?",
          timestamp: new Date().toLocaleTimeString(),
          sources: null
        }
      ]);
      return;
    }

    // Try to load from cache first
    const cached = chatCache.getSessionMessages(sessionId);
    if (cached && Array.isArray(cached)) {
      if (cached.length === 0) {
        setMessages([
          {
            id: 1,
            type: 'ai',
            content: "Hello! I'm your AI academic advisor. I can help you with course selection, professor recommendations, academic planning, and much more. What would you like to know?",
            timestamp: new Date().toLocaleTimeString(),
            sources: null
          }
        ]);
      } else {
        setMessages(cached);
      }
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.getChatSessionMessages(sessionId);
      if (response.success) {
        const formattedMessages = response.messages.map(msg => ({
          id: msg.id,
          type: msg.role === 'user' ? 'user' : 'ai',
          content: msg.content,
          timestamp: new Date(msg.timestamp).toLocaleTimeString(),
          sources: msg.sources || null
        }));
        if (formattedMessages.length === 0) {
          setMessages([
            {
              id: 1,
              type: 'ai',
              content: "Hello! I'm your AI academic advisor. I can help you with course selection, professor recommendations, academic planning, and much more. What would you like to know?",
              timestamp: new Date().toLocaleTimeString(),
              sources: null
            }
          ]);
        } else {
          setMessages(formattedMessages);
        }
        // Cache the messages
        chatCache.setSessionMessages(sessionId, formattedMessages);
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
      setMessages([
        {
          id: 1,
          type: 'system',
          content: "Could not restore your previous chat session. Please start a new chat.",
          timestamp: new Date().toLocaleTimeString(),
          sources: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Load messages when session changes
  useEffect(() => {
    loadSessionMessages(currentSessionId);
  }, [currentSessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => {
      const updated = [...prev, userMessage];
      // Update cache
      if (currentSessionId) chatCache.setSessionMessages(currentSessionId, updated);
      return updated;
    });
    setInputMessage('');
    setIsTyping(true);
    setShowSources(false);
    setCurrentSources(null);

    try {
      // If no current session, create one when user first starts chatting
      let sessionId = currentSessionId;
      if (!sessionId) {
        try {
          const sessionResponse = await apiService.createChatSession('New Chat');
          if (sessionResponse.success) {
            sessionId = sessionResponse.session_id;
            // Update the parent component with the new session
            if (onNewChat) {
              onNewChat(sessionId);
            }
            console.log('📱 Created new chat session for first message:', sessionId);
          }
        } catch (sessionError) {
          console.error('Error creating session for first message:', sessionError);
        }
      }

      // Get chat history for context
      const chatHistory = messages
        .filter(msg => msg.type === 'user' || msg.type === 'ai')
        .slice(-6) // Last 6 messages for context
        .map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }));

      // Send message to RAG service with session ID
      const response = await apiService.sendChatMessage(inputMessage, chatHistory, sessionId);
      
      if (response.success) {
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: response.response,
          timestamp: new Date().toLocaleTimeString(),
          sources: response.sources
        };

        setMessages(prev => {
          const updated = [...prev, aiMessage];
          // Update cache
          if (sessionId) chatCache.setSessionMessages(sessionId, updated);
          return updated;
        });
        setCurrentSources(response.sources);
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        timestamp: new Date().toLocaleTimeString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleSources = () => {
    setShowSources(!showSources);
  };

  return (
    <div className="h-full w-full flex flex-col bg-white/90 backdrop-blur-sm">
      {/* Header */}
      <div className="flex-shrink-0 p-6 border-b border-gray-200/50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">{sessionTitle}</h2>
            <p className="text-sm text-gray-500 font-medium">Ask me anything about courses, professors, academic planning</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600 font-medium hidden sm:block">Online</span>
            </div>
            
            {/* New Chat Button */}
            {onNewChat && (
              <button
                onClick={onNewChat}
                className="p-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl transition-all duration-300 hover:shadow-lg"
                title="New Chat"
              >
                <Plus className="w-5 h-5" />
              </button>
            )}
            
            {/* Chat History Toggle Button - Only visible on mobile */}
            <button
              onClick={onToggleHistory}
              className="md:hidden p-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl transition-all duration-300 hover:shadow-lg"
              title="Toggle Chat History"
            >
              <History className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-3 max-w-3xl ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.type === 'user' 
                      ? 'bg-gradient-to-br from-blue-600 to-purple-600' 
                      : 'bg-gradient-to-br from-gray-600 to-gray-700'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-white" />
                    )}
                  </div>
                  
                  <div className={`flex flex-col ${
                    message.type === 'user' ? 'items-end' : 'items-start'
                  }`}>
                    <div className={`px-4 py-3 rounded-2xl max-w-2xl ${
                      message.type === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : message.error
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      {message.type === 'user' ? (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      ) : (
                        <MarkdownRenderer content={message.content} />
                      )}
                      
                      {/* Sources button for AI messages */}
                      {message.type === 'ai' && message.sources && (
                        <button
                          onClick={() => {
                            setCurrentSources(message.sources);
                            setShowSources(!showSources);
                          }}
                          className="mt-2 flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          <Info className="w-3 h-3" />
                          <span>View Sources</span>
                        </button>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 mt-2">{message.timestamp}</span>
                  </div>
                </div>
              </div>
            ))
          }
          
          {(isTyping || isStreaming) && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-700 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 bg-gray-100 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Sources Panel */}
      {showSources && currentSources && (
        <div className="flex-shrink-0 p-4 border-t border-gray-200/50 bg-gray-50/50">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">Sources & Information</h3>
              <button
                onClick={() => setShowSources(false)}
                className="px-3 py-1 text-xs bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 transition"
              >
                X
              </button>
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <p><strong>Collections used:</strong> {currentSources.collections_used?.join(', ') || 'None'}</p>
              <p><strong>Documents retrieved:</strong> {currentSources.documents_retrieved || 0}</p>
              <p><strong>Web search performed:</strong> {currentSources.web_search_performed ? 'Yes' : 'No'}</p>
              <p><strong>User info included:</strong> {currentSources.user_info_included ? 'Yes' : 'No'}</p>
              <p><strong>Chat history included:</strong> {currentSources.chat_history_included ? 'Yes' : 'No'}</p>
              
              {currentSources.top_documents && currentSources.top_documents.length > 0 && (
                <div className="mt-2">
                  <p className="font-semibold">Top Documents:</p>
                  {currentSources.top_documents.map((doc, index) => (
                    <div key={index} className="ml-2 mt-1 p-2 bg-white rounded border">
                      <p><strong>Collection:</strong> {doc.collection}</p>
                      <p><strong>Score:</strong> {doc.score?.toFixed(4) || 'N/A'}</p>
                      <p><strong>Preview:</strong> {doc.content_preview}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex-shrink-0 p-6 border-t border-gray-200/50">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about courses, professors, academic planning, or anything else..."
                className="w-full pl-4 pr-12 py-3 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none bg-white/80 backdrop-blur-sm transition-all duration-200"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isTyping || isStreaming}
              />
              <div className="absolute right-3 bottom-3 flex items-center space-x-2">
                <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200">
                  <Paperclip className="w-4 h-4" />
                </button>
                <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200">
                  <Mic className="w-4 h-4" />
                </button>
              </div>
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping || isStreaming}
              className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <div className="flex items-center space-x-1">
              <Sparkles className="w-3 h-3" />
              <span>Powered by AI</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;