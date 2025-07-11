import React, { useState } from "react";
import { MessageCircle, Clock, Search, X } from "lucide-react";

const ChatHistory = ({ onClose }) => {
  const [selectedChat, setSelectedChat] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  const chatHistory = [
    {
      id: 1,
      title: "Course Recommendations for CS",
      lastMessage: "I need help choosing my next semester courses for Computer Science major...",
      timestamp: "2 hours ago",
      unread: true,
      category: "Course Planning"
    },
    {
      id: 2,
      title: "Professor Information",
      lastMessage: "Can you tell me about Dr. Smith's teaching style and course difficulty?",
      timestamp: "1 day ago",
      unread: false,
      category: "Professor Review"
    },
    {
      id: 3,
      title: "Academic Planning",
      lastMessage: "I want to plan my graduation timeline and optimize my course schedule...",
      timestamp: "3 days ago",
      unread: false,
      category: "Academic Planning"
    },
    {
      id: 4,
      title: "Internship Guidance",
      lastMessage: "Looking for advice on finding internships in software development...",
      timestamp: "1 week ago",
      unread: false,
      category: "Career Guidance"
    }
  ];

  const handleChatSelect = (chatId) => {
    setSelectedChat(chatId);
    // Here you would typically load the selected chat into the main chat interface
    console.log(`Selected chat: ${chatId}`);
  };

  return (
    <div className="h-full w-full bg-white/90 backdrop-blur-sm border-l border-gray-200/50 flex flex-col">
      <div className="flex-shrink-0 p-4 border-b border-gray-200/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Chat History</h2>
              <p className="text-xs text-gray-500">Previous conversations</p>
            </div>
          </div>
          
          {/* Close Button - Only visible on mobile */}
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden p-2 bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white rounded-xl transition-all duration-300 hover:shadow-lg"
              title="Close Chat History"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

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

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {chatHistory
            .filter(chat => 
              chat.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
              chat.lastMessage.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .map((chat) => (
            <div 
              key={chat.id} 
              className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                selectedChat === chat.id
                  ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 shadow-md'
                  : 'bg-white/50 border-gray-200/50 hover:bg-gray-50/80 hover:border-gray-300'
              }`}
              onClick={() => handleChatSelect(chat.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className={`font-semibold text-sm ${
                  selectedChat === chat.id ? 'text-blue-700' : 'text-gray-900'
                }`}>
                  {chat.title}
                </h3>
                {chat.unread && (
                  <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full"></div>
                )}
              </div>
              
              <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                {chat.lastMessage}
              </p>
              
              <div className="flex items-center justify-between">
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                  {chat.category}
                </span>
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>{chat.timestamp}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatHistory;