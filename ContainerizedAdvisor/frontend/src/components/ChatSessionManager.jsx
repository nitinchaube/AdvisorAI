import React, { useState, useEffect } from "react";
import { MessageCircle, Plus, Trash2, Edit3, X, Search, Clock, MoreVertical } from "lucide-react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

const ChatSessionManager = ({ 
  onSessionSelect, 
  onNewChat, 
  onClose, 
  currentSessionId,
  onSessionUpdate 
}) => {
  const { currentUser } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingSession, setEditingSession] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isUpdatingSession, setIsUpdatingSession] = useState(false);
  const [isDeletingSession, setIsDeletingSession] = useState(false);

  // Load chat sessions
  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await apiService.getChatSessions();
      if (response.success) {
        setSessions(response.sessions);
        console.log(`📱 Loaded ${response.sessions.length} chat sessions`);
      } else {
        console.error('Failed to load chat sessions:', response.error);
      }
    } catch (error) {
      console.error('Error loading chat sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Refresh sessions (called when new chat is created or session is updated)
  const refreshSessions = async () => {
    await loadSessions();
  };

  // Create new chat session
  const handleNewChat = async () => {
    if (isCreatingSession) return; // Prevent duplicate creation
    
    try {
      setIsCreatingSession(true);
      const response = await apiService.createChatSession('New Chat');
      if (response.success) {
        const newSession = {
          id: response.session_id,
          title: 'New Chat',
          created_at: new Date().toISOString(),
          last_updated: new Date().toISOString(),
          message_count: 0,
          messages: []
        };
        
        // Add to local state immediately for better UX
        setSessions(prev => [newSession, ...prev]);
        
        // Notify parent component
        onNewChat(response.session_id);
        
        console.log("📱 Created new chat session:", response.session_id);
        
        // Refresh sessions to ensure consistency
        setTimeout(() => {
          refreshSessions();
        }, 100);
      } else {
        throw new Error(response.error || "Failed to create session");
      }
    } catch (error) {
      console.error('Error creating new chat session:', error);
      // Remove from local state if creation failed
      setSessions(prev => prev.filter(s => s.id !== 'temp'));
    } finally {
      setIsCreatingSession(false);
    }
  };

  // Select a chat session
  const handleSessionSelect = (sessionId) => {
    if (sessionId === currentSessionId) return; // No need to select same session
    onSessionSelect(sessionId);
  };

  // Update session title
  const handleUpdateSession = async (sessionId, newTitle) => {
    if (isUpdatingSession || !newTitle.trim()) return;
    
    try {
      setIsUpdatingSession(true);
      const response = await apiService.updateChatSession(sessionId, newTitle);
      if (response.success) {
        // Update local state
        setSessions(prev => prev.map(session => 
          session.id === sessionId 
            ? { ...session, title: newTitle, last_updated: new Date().toISOString() }
            : session
        ));
        
        setEditingSession(null);
        setEditTitle('');
        
        // Notify parent component
        if (onSessionUpdate) {
          onSessionUpdate(sessionId, newTitle);
        }
        
        console.log("📱 Updated session title:", newTitle);
        
        // Refresh sessions to ensure consistency
        setTimeout(() => {
          refreshSessions();
        }, 100);
      } else {
        throw new Error(response.error || "Failed to update session");
      }
    } catch (error) {
      console.error('Error updating session:', error);
      // Revert edit title to original
      const originalSession = sessions.find(s => s.id === sessionId);
      if (originalSession) {
        setEditTitle(originalSession.title);
      }
    } finally {
      setIsUpdatingSession(false);
    }
  };

  // Delete session
  const handleDeleteSession = async (sessionId) => {
    if (isDeletingSession) return;
    
    if (!window.confirm('Are you sure you want to delete this chat session? This action cannot be undone.')) {
      return;
    }

    try {
      setIsDeletingSession(true);
      const response = await apiService.deleteChatSession(sessionId);
      if (response.success) {
        // Remove from local state
        setSessions(prev => prev.filter(session => session.id !== sessionId));
        
        // If we deleted the current session, create a new one
        if (sessionId === currentSessionId) {
          handleNewChat();
        }
        
        console.log("📱 Deleted chat session:", sessionId);
        
        // Refresh sessions to ensure consistency
        setTimeout(() => {
          refreshSessions();
        }, 100);
      } else {
        throw new Error(response.error || "Failed to delete session");
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    } finally {
      setIsDeletingSession(false);
    }
  };

  // Start editing session title
  const startEditing = (session) => {
    setEditingSession(session.id);
    setEditTitle(session.title);
  };

  // Cancel editing
  const cancelEditing = () => {
    setEditingSession(null);
    setEditTitle('');
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

  // Get last message preview
  const getLastMessagePreview = (session) => {
    const messages = session.messages || [];
    if (messages.length === 0) {
      return "No messages yet";
    }
    
    const lastMessage = messages[messages.length - 1];
    const content = lastMessage.content || "";
    return content.length > 50 ? content.substring(0, 50) + "..." : content;
  };

  // Filter sessions based on search
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getLastMessagePreview(session).toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    loadSessions();
    
    // Set up periodic refresh every 30 seconds to keep sessions up to date
    const refreshInterval = setInterval(() => {
      refreshSessions();
    }, 30000);
    
    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  return (
    <div className="h-full w-full bg-white/90 backdrop-blur-sm border-l border-gray-200/50 flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Chat Sessions</h2>
              <p className="text-xs text-gray-500">Your conversations</p>
            </div>
          </div>
          
          {/* Close Button - Only visible on mobile */}
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden p-2 bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white rounded-xl transition-all duration-300 hover:shadow-lg"
              title="Close Chat Sessions"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* New Chat Button */}
        <button
          onClick={handleNewChat}
          disabled={isCreatingSession}
          className="w-full mb-4 p-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-blue-400 disabled:to-purple-400 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center space-x-2 disabled:cursor-not-allowed"
        >
          {isCreatingSession ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <Plus className="w-4 h-4" />
          )}
          <span className="font-medium">
            {isCreatingSession ? 'Creating...' : 'New Chat'}
          </span>
        </button>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search chats..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-gray-50/50 backdrop-blur-sm transition-all duration-200 text-sm"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-8">
            <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 text-sm">
              {searchTerm ? 'No chats found matching your search.' : 'No chat sessions yet. Start a new conversation!'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredSessions.map((session) => (
              <div 
                key={session.id} 
                className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer group ${
                  currentSessionId === session.id
                    ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 shadow-md'
                    : 'bg-white/50 border-gray-200/50 hover:bg-gray-50/80 hover:border-gray-300'
                }`}
                onClick={() => handleSessionSelect(session.id)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    {editingSession === session.id ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleUpdateSession(session.id, editTitle);
                          } else if (e.key === 'Escape') {
                            cancelEditing();
                          }
                        }}
                        onBlur={() => handleUpdateSession(session.id, editTitle)}
                        className="w-full px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        autoFocus
                        disabled={isUpdatingSession}
                      />
                    ) : (
                      <h3 className={`font-semibold text-sm truncate ${
                        currentSessionId === session.id ? 'text-blue-700' : 'text-gray-900'
                      }`}>
                        {session.title}
                      </h3>
                    )}
                  </div>
                  
                  {/* Action buttons */}
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {editingSession !== session.id && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(session);
                          }}
                          className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                          title="Edit title"
                          disabled={isUpdatingSession}
                        >
                          <Edit3 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(session.id);
                          }}
                          className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                          title="Delete session"
                          disabled={isDeletingSession}
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
                
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                  {getLastMessagePreview(session)}
                </p>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {session.message_count} messages
                  </span>
                  <div className="flex items-center space-x-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(session.last_updated)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSessionManager; 