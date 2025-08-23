import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Paperclip, Mic, History, Info, Plus, ThumbsUp, ThumbsDown, Copy, Check } from "lucide-react";
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
  currentSessionId,   
  onSessionUpdate,
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
  const [copiedMessages, setCopiedMessages] = useState(new Set());
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const messagesEndRef = useRef(null);

  // Copy message content to clipboard
  const copyToClipboard = async (content, messageId) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessages(prev => new Set([...prev, messageId]));
      setTimeout(() => {
        setCopiedMessages(prev => {
          const newSet = new Set(prev);
          newSet.delete(messageId);
          return newSet;
        });
      }, 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  // Handle feedback submission
  const handleFeedback = async (messageId, feedback) => {
    try {
      await apiService.submitFeedback(messageId, feedback);
      // Update the message to show feedback was submitted
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, feedback: feedback }
          : msg
      ));
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

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
      setSessionInitialized(true);
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
      setSessionInitialized(true);
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
      setSessionInitialized(true);
    }
  };

  // Load messages when session changes
  useEffect(() => {
    console.log("📱 ChatInterface: Session changed to:", currentSessionId);
    setSessionInitialized(false);
    loadSessionMessages(currentSessionId);
  }, [currentSessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping || isStreaming || !sessionInitialized) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    // Store the current input message
    const currentInput = inputMessage;
    setInputMessage('');
    setIsTyping(true);
    setShowSources(false);
    setCurrentSources(null);

    // Add user message immediately
    setMessages(prev => {
      const updated = [...prev, userMessage];
      // Update cache
      if (currentSessionId) chatCache.setSessionMessages(currentSessionId, updated);
      return updated;
    });

    try {
      // Ensure we have a valid session ID
      if (!currentSessionId) {
        console.error('No session ID available for message');
        throw new Error('No active chat session');
      }

      // Get chat history for context (include the current user message)
      const chatHistory = messages
        .filter(msg => msg.type === 'user' || msg.type === 'ai')
        .slice(-6) // Last 6 messages for context
        .map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }));

      // Send message to RAG service with session ID
      const response = await apiService.sendChatMessage(currentInput, chatHistory, currentSessionId);
      
      console.log("📱 Raw API response received:", response);
      
      if (response.success) {
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: response.response,
          timestamp: new Date().toLocaleTimeString(),
          sources: response.sources
        };

        // Debug logging for response structure
        console.log("📱 Chat response received:", {
          success: response.success,
          chat_name: response.chat_name,
          sources: response.sources,
          hasChatName: !!response.chat_name,
          chatNameValue: response.chat_name,
          fullResponse: response
        });
        
        console.log("📱 Checking if chat_name exists and is different from 'New Chat'");
        console.log("📱 response.chat_name:", response.chat_name);
        console.log("📱 response.chat_name !== 'New Chat':", response.chat_name !== 'New Chat');
        console.log("📱 Both conditions met:", response.chat_name && response.chat_name !== 'New Chat');

        setMessages(prev => {
          const updated = [...prev, aiMessage];
          // Update cache
          if (currentSessionId) chatCache.setSessionMessages(currentSessionId, updated);
          return updated;
        });
        setCurrentSources(response.sources);

        // Check if session title should be updated
        if (response.chat_name && response.chat_name !== 'New Chat') {
          // Update session title if it's still "New Chat"
          try {
            console.log("📝 Updating session title from 'New Chat' to:", response.chat_name);
            console.log("📝 Calling apiService.updateChatSession with:", currentSessionId, response.chat_name);
            const updateResponse = await apiService.updateChatSession(currentSessionId, response.chat_name);
            console.log("📝 updateChatSession response:", updateResponse);
            if (onSessionUpdate) {
              console.log("📝 Calling onSessionUpdate callback with:", currentSessionId, response.chat_name);
              onSessionUpdate(currentSessionId, response.chat_name);
            }
          } catch (error) {
            console.error('Error updating session title:', error);
          }
        } else {
          console.log("📝 Not updating session title. Conditions not met:");
          console.log("📝 - response.chat_name exists:", !!response.chat_name);
          console.log("📝 - response.chat_name !== 'New Chat':", response.chat_name !== 'New Chat');
        }
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
    <div className="h-full w-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex-shrink-0 p-6 border-b border-slate-200 bg-white">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-cyan-600 rounded-xl flex items-center justify-center shadow-md border border-blue-300/30">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-slate-800">{sessionTitle}</h2>
            <p className="text-sm text-slate-600 font-medium">Ask me anything about courses, professors, academic planning</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-blue-600 font-medium hidden sm:block">Online</span>
            </div>
            
            {/* New Chat Button */}
            {onNewChat && (
              <button
                onClick={onNewChat}
                className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl transition-all duration-300 hover:shadow-md hover:scale-105 border border-blue-300/30"
                title="New Chat"
              >
                <Plus className="w-5 h-5" />
              </button>
            )}
            
            {/* Chat History Toggle Button - Only visible on mobile */}
            <button
              onClick={onToggleHistory}
              className="md:hidden p-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl transition-all duration-300 hover:shadow-md hover:scale-105 border border-blue-300/30"
              title="Toggle Chat History"
            >
              <History className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-50/30">
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
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 border border-blue-300/30' 
                      : 'bg-gradient-to-br from-blue-400 to-cyan-600 border border-blue-300/30'
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
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md border border-blue-300/30'
                        : message.error
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : 'bg-white text-slate-800 border border-slate-200/60 shadow-sm'
                    }`}>
                      {message.type === 'user' ? (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      ) : (
                        <MarkdownRenderer content={message.content} />
                      )}
                    </div>
                    
                    {/* Action buttons positioned below message */}
                    <div className="flex items-center justify-start mt-2 space-x-3">
                      {/* Sources button for AI messages */}
                      {message.type === 'ai' && message.sources && (
                        <button
                          onClick={() => {
                            setCurrentSources(message.sources);
                            setShowSources(!showSources);
                          }}
                          className="flex items-center justify-center w-6 h-6 text-slate-500 hover:text-blue-600 transition-colors"
                          title="View Sources"
                        >
                          <Info className="w-4 h-4" />
                        </button>
                      )}
                      
                      {/* Copy button */}
                      <button
                        onClick={() => copyToClipboard(message.content, message.id)}
                        className="flex items-center justify-center w-6 h-6 text-slate-500 hover:text-slate-700 transition-colors"
                        title="Copy message"
                      >
                        {copiedMessages.has(message.id) ? (
                          <Check className="w-4 h-4 text-blue-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      
                      {/* Feedback buttons for AI messages */}
                      {message.type === 'ai' && (
                        <>
                          <button
                            onClick={() => handleFeedback(message.id, 'positive')}
                            disabled={message.feedback === 'positive'}
                            className={`flex items-center justify-center w-6 h-6 transition-colors ${
                              message.feedback === 'positive'
                                ? 'text-blue-600'
                                : 'text-slate-500 hover:text-blue-600'
                            }`}
                            title="Helpful"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleFeedback(message.id, 'negative')}
                            disabled={message.feedback === 'negative'}
                            className={`flex items-center justify-center w-6 h-6 transition-colors ${
                              message.feedback === 'negative'
                                ? 'text-red-600'
                                : 'text-slate-500 hover:text-red-600'
                            }`}
                            title="Not helpful"
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                    
                    <span className="text-xs text-slate-500 mt-2">{message.timestamp}</span>
                  </div>
                </div>
              </div>
            ))
          }
          
          {(isTyping || isStreaming) && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-cyan-600 rounded-full flex items-center justify-center border border-blue-300/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 bg-white rounded-2xl border border-slate-200/60 shadow-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
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
        <div className="flex-shrink-0 p-4 border-t border-slate-200 bg-slate-50/50">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-700">Sources & Information</h3>
              <button
                onClick={() => setShowSources(false)}
                className="px-3 py-1 text-xs bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 hover:scale-105 border border-blue-300/30"
              >
                X
              </button>
            </div>
            <div className="text-xs text-slate-600 space-y-1">
              <p><strong>Collections used:</strong> {currentSources.collections_used?.join(', ') || 'None'}</p>
              <p><strong>Documents retrieved:</strong> {currentSources.documents_retrieved || 0}</p>
              <p><strong>Web search performed:</strong> {currentSources.web_search_performed ? 'Yes' : 'No'}</p>
              <p><strong>User info included:</strong> {currentSources.user_info_included ? 'Yes' : 'No'}</p>
              <p><strong>Chat history included:</strong> {currentSources.chat_history_included ? 'Yes' : 'No'}</p>
              
              {currentSources.top_documents && currentSources.top_documents.length > 0 && (
                <div className="mt-2">
                  <p className="font-semibold">Top Documents:</p>
                  {currentSources.top_documents.map((doc, index) => (
                    <div key={index} className="ml-2 mt-1 p-2 bg-white rounded border border-slate-200/60 shadow-sm">
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
      <div className="flex-shrink-0 p-6 border-t border-slate-200 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={currentSessionId ? "Ask me anything about stevens ..." : "Start a new chat to begin..."}
                className="w-full pl-4 pr-12 py-3 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none bg-white transition-all duration-200 shadow-sm"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isTyping || isStreaming || !currentSessionId}
              />
              <div className="absolute right-3 bottom-3 flex items-center space-x-2">
                <button className="p-1 text-slate-400 hover:text-slate-600 transition-colors duration-200">
                  <Paperclip className="w-4 h-4" />
                </button>
                <button className="p-1 text-slate-400 hover:text-slate-600 transition-colors duration-200">
                  <Mic className="w-4 h-4" />
                </button>
              </div>
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping || isStreaming || !currentSessionId}
              className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-slate-300 disabled:to-slate-400 text-white rounded-xl transition-all duration-200 shadow-md hover:shadow-lg disabled:shadow-none disabled:cursor-not-allowed hover:scale-105 border border-blue-300/30"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
         
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;