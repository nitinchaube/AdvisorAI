import React, { useState, useEffect } from "react";
import { MessageCircle, Clock, Search, Calendar, User, Bot, Trash2, Edit3, Eye, RefreshCw } from "lucide-react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

const ChatHistoryView = ({ onSessionSelect, onNewChat }) => {
  const { currentUser } = useAuth();
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSession, setSelectedSession] = useState(null);
  const [expandedSessions, setExpandedSessions] = useState(new Set());

  // Load comprehensive chat history
  const loadChatHistory = async () => {
    try {
      setLoading(true);
      const response = await apiService.getUserChatHistory();
      if (response.success) {
        setChatHistory(response.chat_history);
        console.log(`📱 Loaded ${response.total_sessions} sessions with ${response.total_messages} total messages`);
      } else {
        console.error('Failed to load chat history:', response.error);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  // Refresh chat history
  const refreshHistory = async () => {
    await loadChatHistory();
  };

  // Toggle session expansion
  const toggleSessionExpansion = (sessionId) => {
    const newExpanded = new Set(expandedSessions);
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId);
    } else {
      newExpanded.add(sessionId);
    }
    setExpandedSessions(newExpanded);
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  // Format date
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter sessions based on search
  const filteredSessions = chatHistory.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.messages.some(msg => 
      msg.content.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Get message preview
  const getMessagePreview = (content) => {
    return content.length > 100 ? content.substring(0, 100) + "..." : content;
  };

  useEffect(() => {
    loadChatHistory();
  }, []);

  return (
    <div className="h-full w-full bg-white/90 backdrop-blur-sm flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-6 border-b border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Chat History</h1>
              <p className="text-sm text-gray-500">All your conversations and messages</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={refreshHistory}
              disabled={loading}
              className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50"
              title="Refresh History"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            
            <button
              onClick={onNewChat}
              className="p-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl flex items-center space-x-2"
            >
              <MessageCircle className="w-4 h-4" />
              <span className="font-medium">New Chat</span>
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search conversations and messages..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-gray-50/50 backdrop-blur-sm transition-all duration-200"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-12">
            <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {searchTerm ? 'No conversations found' : 'No chat history yet'}
            </h3>
            <p className="text-gray-500 mb-6">
              {searchTerm ? 'Try adjusting your search terms.' : 'Start your first conversation to see it here!'}
            </p>
            {!searchTerm && (
              <button
                onClick={onNewChat}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
              >
                Start Your First Chat
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {filteredSessions.map((session) => (
              <div 
                key={session.session_id} 
                className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg overflow-hidden"
              >
                {/* Session Header */}
                <div className="p-6 border-b border-gray-200/50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {session.title}
                        </h3>
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                          {session.message_count} messages
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>Created: {formatDate(session.created_at)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>Updated: {formatTimestamp(session.last_updated)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => onSessionSelect(session.session_id)}
                        className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-lg transition-all duration-200"
                        title="Open Session"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => toggleSessionExpansion(session.session_id)}
                        className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg transition-all duration-200"
                        title={expandedSessions.has(session.session_id) ? "Collapse" : "Expand"}
                      >
                        <MessageCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Session Messages (Expandable) */}
                {expandedSessions.has(session.session_id) && (
                  <div className="p-6 bg-gray-50/50">
                    <div className="space-y-4">
                      {session.messages.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">No messages in this session</p>
                      ) : (
                        session.messages.map((message, index) => (
                          <div 
                            key={message.id || index}
                            className={`flex items-start space-x-3 ${
                              message.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                          >
                            <div className={`flex items-start space-x-3 max-w-3xl ${
                              message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                            }`}>
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                                message.role === 'user' 
                                  ? 'bg-gradient-to-br from-blue-600 to-purple-600' 
                                  : 'bg-gradient-to-br from-gray-600 to-gray-700'
                              }`}>
                                {message.role === 'user' ? (
                                  <User className="w-4 h-4 text-white" />
                                ) : (
                                  <Bot className="w-4 h-4 text-white" />
                                )}
                              </div>
                              
                              <div className={`flex flex-col ${
                                message.role === 'user' ? 'items-end' : 'items-start'
                              }`}>
                                <div className={`px-4 py-3 rounded-2xl max-w-2xl ${
                                  message.role === 'user'
                                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                                    : 'bg-white text-gray-900 border border-gray-200'
                                }`}>
                                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                    {getMessagePreview(message.content)}
                                  </p>
                                </div>
                                <span className="text-xs text-gray-500 mt-2">
                                  {formatDate(message.timestamp)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistoryView; 