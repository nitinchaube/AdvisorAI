import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Paperclip, Mic, History, Info, Plus, ThumbsUp, ThumbsDown, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { chatCache } from '../utils/chatCache';

// Code block with copy button (ChatGPT-style)
const CodeBlock = ({ children, language, ...props }) => {
  const [copied, setCopied] = useState(false);
  const codeString = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="relative my-4 group">
      {language && (
        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 text-slate-300 text-xs font-mono rounded-t-lg">
          <span>{language}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2 py-1 hover:bg-slate-700 rounded transition-colors"
            title="Copy code"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      )}
      <pre className={`bg-slate-900 text-slate-100 rounded-lg overflow-x-auto ${language ? 'rounded-t-none' : 'rounded-lg'} p-4 my-0`}>
        <code className="text-sm font-mono leading-relaxed" {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
};

// Proper markdown renderer component with react-markdown (ChatGPT-style)
const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  return (
    <div className="text-sm leading-relaxed markdown-content break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
        // Custom styling for code blocks
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';
          
          return !inline ? (
            <CodeBlock language={language} {...props}>
              {children}
            </CodeBlock>
          ) : (
            <code className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-sm font-mono text-slate-800 dark:text-slate-200" {...props}>
              {children}
            </code>
          );
        },
        // Custom styling for links
        a({ children, ...props }) {
          return (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {children}
            </a>
          );
        },
        // Custom styling for lists (ChatGPT-style)
        ul({ children, ...props }) {
          return (
            <ul className="list-disc my-3 space-y-1 ml-6" {...props}>
              {children}
            </ul>
          );
        },
        ol({ children, ...props }) {
          return (
            <ol className="list-decimal my-3 space-y-1 ml-6" {...props}>
              {children}
            </ol>
          );
        },
        li({ children, ...props }) {
          return (
            <li className="pl-2 leading-relaxed" {...props}>
              {children}
            </li>
          );
        },
        // Custom styling for paragraphs (ChatGPT-style)
        p({ children, ...props }) {
          // Check if paragraph only contains whitespace or is empty
          const text = String(children).trim();
          if (!text) return null;
          
          return (
            <p className="my-3 leading-relaxed text-slate-800" {...props}>
              {children}
            </p>
          );
        },
        // Custom styling for headers
        h1({ children, ...props }) {
          return (
            <h1 className="text-xl font-bold mt-4 mb-2 text-slate-900" {...props}>
              {children}
            </h1>
          );
        },
        h2({ children, ...props }) {
          return (
            <h2 className="text-lg font-bold mt-4 mb-2 text-slate-900" {...props}>
              {children}
            </h2>
          );
        },
        h3({ children, ...props }) {
          return (
            <h3 className="text-base font-semibold mt-3 mb-2 text-slate-900" {...props}>
              {children}
            </h3>
          );
        },
        // Custom styling for blockquotes (ChatGPT-style)
        blockquote({ children, ...props }) {
          return (
            <blockquote className="border-l-4 border-slate-300 pl-4 my-3 italic text-slate-600 bg-slate-50 py-2 rounded-r" {...props}>
              {children}
            </blockquote>
          );
        },
        // Horizontal rule
        hr({ ...props }) {
          return (
            <hr className="my-4 border-slate-200" {...props} />
          );
        },
        // Strong text
        strong({ children, ...props }) {
          return (
            <strong className="font-semibold text-slate-900" {...props}>
              {children}
            </strong>
          );
        },
        // Emphasis text
        em({ children, ...props }) {
          return (
            <em className="italic text-slate-700" {...props}>
              {children}
            </em>
          );
        },
        // Strikethrough text
        del({ children, ...props }) {
          return (
            <del className="line-through text-slate-500" {...props}>
              {children}
            </del>
          );
        },
        // Inline code (already handled in code component, but ensure it's preserved)
        // Text nodes - preserve all text formatting
        // Custom styling for tables (ChatGPT-style)
        table({ children, ...props }) {
          return (
            <div className="overflow-x-auto my-4 border border-slate-200 rounded-lg">
              <table className="min-w-full divide-y divide-slate-200" {...props}>
                {children}
              </table>
            </div>
          );
        },
        thead({ children, ...props }) {
          return (
            <thead className="bg-slate-50" {...props}>
              {children}
            </thead>
          );
        },
        tbody({ children, ...props }) {
          return (
            <tbody className="bg-white divide-y divide-slate-200" {...props}>
              {children}
            </tbody>
          );
        },
        th({ children, ...props }) {
          return (
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider" {...props}>
              {children}
            </th>
          );
        },
        td({ children, ...props }) {
          return (
            <td className="px-4 py-3 text-sm text-slate-800" {...props}>
              {children}
            </td>
          );
        },
      }}
      >
        {content}
      </ReactMarkdown>
    </div>
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
  const [thinkingStatus, setThinkingStatus] = useState('Thinking…');
  const [thinkingUrls, setThinkingUrls] = useState([]);
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
      // Submit feedback to backend
      await apiService.submitFeedback(messageId, feedback);
      
      // Update the message to show feedback was submitted
      setMessages(prev => {
        const updated = prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, feedback: feedback }
            : msg
        );
        
        // Update cache with feedback included
        if (currentSessionId) {
          chatCache.setSessionMessages(currentSessionId, updated);
        }
        
        return updated;
      });
      
      console.log(`📱 Feedback submitted: ${feedback} for message ${messageId}`);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  // Load messages for current session
  const loadSessionMessages = async (sessionId) => {
    if (!sessionId) {
      // No session selected, show welcome message
      const welcomeMessage = {
        id: 1,
        type: 'ai',
        content: "Hello! I'm your AI academic advisor. I can help you with course selection, professor recommendations, academic planning, and much more. What would you like to know?",
        timestamp: new Date().toLocaleTimeString(),
        sources: null,
        feedback: null,
        context: null
      };
      setMessages([welcomeMessage]);
      setSessionInitialized(true);
      return;
    }

    // Try to load from cache first
    const cached = chatCache.getSessionMessages(sessionId);
    if (cached && Array.isArray(cached) && cached.length > 0) {
      console.log("📱 Loaded messages from cache:", cached.length);
      // Ensure all cached messages have feedback and context fields
      const validatedMessages = cached.map(msg => ({
        ...msg,
        feedback: msg.feedback || null,
        context: msg.context || null
      }));
      setMessages(validatedMessages);
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
          sources: msg.sources || null,
          feedback: msg.feedback || null, // Preserve feedback data
          context: msg.context || null // Preserve context data
        }));
        
        if (formattedMessages.length === 0) {
          // No messages in session, show welcome message
          const welcomeMessage = {
            id: 1,
            type: 'ai',
            content: "Hello! I'm your AI academic advisor. I can help you with course selection, professor recommendations, academic planning, and much more. What would you like to know?",
            timestamp: new Date().toLocaleTimeString(),
            sources: null,
            feedback: null,
            context: null
          };
          setMessages([welcomeMessage]);
        } else {
          console.log("📱 Loaded messages from API:", formattedMessages.length);
          setMessages(formattedMessages);
        }
        
        // Cache the messages with feedback and context
        chatCache.setSessionMessages(sessionId, formattedMessages);
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
      const errorMessage = {
        id: 1,
        type: 'ai',
        content: "Could not restore your previous chat session. Please start a new chat.",
        timestamp: new Date().toLocaleTimeString(),
        sources: null,
        feedback: null,
        context: null
      };
      setMessages([errorMessage]);
    } finally {
      setLoading(false);
      setSessionInitialized(true);
    }
  };

  // Load messages when session changes
  useEffect(() => {
    console.log("📱 ChatInterface: Session changed to:", currentSessionId);
    setSessionInitialized(false);
    setMessages([]); // Clear messages before loading new session
    loadSessionMessages(currentSessionId);
  }, [currentSessionId]);

  // Ensure chat history consistency - always maintain last 3 Q&A pairs
  const ensureChatHistoryConsistency = (messages) => {
    if (!messages || messages.length === 0) return messages;
    
    // Filter to only user and AI messages (exclude system messages)
    const conversationMessages = messages.filter(msg => msg.type === 'user' || msg.type === 'ai');
    
    // If we have more than 6 messages, ensure we keep the last 6 (3 Q&A pairs)
    if (conversationMessages.length > 6) {
      const lastSixMessages = conversationMessages.slice(-6);
      console.log("📱 Ensuring chat history consistency - keeping last 6 messages:", lastSixMessages.length);
      return lastSixMessages;
    }
    
    return conversationMessages;
  };

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
      timestamp: new Date().toLocaleTimeString(),
      feedback: null,
      context: {
        previousMessages: messages.filter(msg => msg.type === 'user' || msg.type === 'ai').slice(-4),
        timestamp: new Date().toISOString()
      }
    };

    const currentInput = inputMessage;
    setInputMessage('');
    setIsTyping(true);       // show bouncing dots while pipeline runs
    setIsStreaming(false);
    setThinkingStatus('Thinking…');
    setThinkingUrls([]);
    setShowSources(false);
    setCurrentSources(null);

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);

    if (currentSessionId) {
      chatCache.setSessionMessages(currentSessionId, updatedMessages);
    }

    // ID for the AI message we'll progressively build
    const aiMsgId = Date.now() + 1;

    try {
      if (!currentSessionId) {
        throw new Error('No active chat session');
      }

      const chatHistory = updatedMessages
        .filter(msg => msg.type === 'user' || msg.type === 'ai')
        .slice(-6)
        .map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content,
        }));

      let accumulated = "";
      let streamStarted = false;

      await apiService.streamChatMessage(
        currentInput,
        chatHistory,
        currentSessionId,

        // ── onToken ──────────────────────────────────────────────
        (token) => {
          if (!streamStarted) {
            streamStarted = true;
            setIsTyping(false);   // stop bouncing dots
            setIsStreaming(true); // signal that text is flowing in
            // Insert an empty AI message placeholder
            setMessages(prev => [
              ...prev,
              {
                id: aiMsgId,
                type: 'ai',
                content: '',
                timestamp: new Date().toLocaleTimeString(),
                sources: null,
                feedback: null,
                context: null,
              },
            ]);
          }
          accumulated += token;
          const snap = accumulated;
          setMessages(prev =>
            prev.map(m => (m.id === aiMsgId ? { ...m, content: snap } : m))
          );
        },

        // ── onStatus – update the live step indicator ────────────
        (status, event) => {
          setThinkingStatus(status);
          if (event && event.urls) {
            setThinkingUrls(event.urls);
          }
        },

        // ── onDone ───────────────────────────────────────────────
        (meta) => {
          setIsStreaming(false);
          const finalContent = accumulated.trim();
          const sources = meta.sources || {};
          setCurrentSources(sources);

          setMessages(prev => {
            const updated = prev.map(m =>
              m.id === aiMsgId
                ? {
                    ...m,
                    content: finalContent,
                    sources,
                    context: {
                      previousMessages: chatHistory,
                      userQuestion: currentInput,
                      timestamp: new Date().toISOString(),
                    },
                  }
                : m
            );
            const consistent = ensureChatHistoryConsistency(updated);
            if (currentSessionId) chatCache.setSessionMessages(currentSessionId, consistent);
            return updated;
          });

          // Update session title when the backend provides one
          const chatName = meta.chat_name;
          if (chatName && chatName !== 'New Chat') {
            if (onSessionUpdate) onSessionUpdate(currentSessionId, chatName);
            apiService.updateChatSession(currentSessionId, chatName).catch(() => {});
          }
        },
      );
    } catch (error) {
      console.error('Chat error:', error);
      setIsStreaming(false);
      const errorMessage = {
        id: aiMsgId,
        type: 'ai',
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        timestamp: new Date().toLocaleTimeString(),
        error: true,
        feedback: null,
        context: null,
      };
      setMessages(prev => {
        const hasPlaceholder = prev.some(m => m.id === aiMsgId);
        const updated = hasPlaceholder
          ? prev.map(m => (m.id === aiMsgId ? errorMessage : m))
          : [...prev, errorMessage];
        const consistent = ensureChatHistoryConsistency(updated);
        if (currentSessionId) chatCache.setSessionMessages(currentSessionId, consistent);
        return updated;
      });
    } finally {
      setIsTyping(false);
      setIsStreaming(false);
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
                    } ${message.isStreaming ? 'animate-pulse' : ''}`}>
                      {message.type === 'user' ? (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                      ) : (
                        <div className="w-full">
                          <MarkdownRenderer content={message.content} />
                          {message.isStreaming && (
                            <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse" />
                          )}
                        </div>
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
          
          {/* Thinking indicator – shows live pipeline steps + URLs */}
          {isTyping && !isStreaming && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-cyan-600 rounded-full flex items-center justify-center border border-blue-300/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 bg-white rounded-2xl border border-slate-200/60 shadow-sm min-w-[220px] max-w-md">
                  {/* Status line */}
                  <div className="flex items-center space-x-3">
                    <div className="relative w-5 h-5 flex-shrink-0">
                      <div className="absolute inset-0 rounded-full border-2 border-blue-200"></div>
                      <div className="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                    </div>
                    <span className="text-sm text-slate-600 font-medium animate-pulse">
                      {thinkingStatus}
                    </span>
                  </div>
                  {/* Web URLs being fetched */}
                  {thinkingUrls.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-100 space-y-1">
                      {thinkingUrls.map((url, idx) => {
                        let displayUrl;
                        try { displayUrl = new URL(url).hostname + new URL(url).pathname; }
                        catch { displayUrl = url; }
                        if (displayUrl.length > 45) displayUrl = displayUrl.slice(0, 45) + '…';
                        return (
                          <div key={idx} className="flex items-center space-x-2 text-xs text-slate-400">
                            <span className="text-blue-400">🔗</span>
                            <span className="truncate">{displayUrl}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
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
              
              {/* Web search links */}
              {currentSources.reasoning?.web_search?.urls?.length > 0 && (
                <div className="mt-2">
                  <p className="font-semibold">Web pages consulted:</p>
                  <ul className="ml-2 mt-1 space-y-1 list-disc">
                    {currentSources.reasoning.web_search.urls.map((url, idx) => (
                      <li key={idx} className="ml-2">
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline break-all"
                        >
                          {url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
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