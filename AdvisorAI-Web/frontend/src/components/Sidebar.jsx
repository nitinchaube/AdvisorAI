import React from "react";
import { 
  MessageCircle, 
  History, 
  Star, 
  BookOpen, 
  Bot,
  TrendingUp,
  Calendar,
  FileText,
  Brain,
  Sparkles
} from "lucide-react";

const Sidebar = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    {
      id: 'chat',
      label: 'Chat with AI',
      icon: MessageCircle,
      description: 'Ask questions and get AI-powered advice'
    },
    {
      id: 'history',
      label: 'Chat History',
      icon: History,
      description: 'View your previous conversations'
    },
    {
      id: 'ratings',
      label: 'Ratings & Reviews',
      icon: Star,
      description: 'Rate professors and courses'
    },
    {
      id: 'courses',
      label: 'Course Explorer',
      icon: BookOpen,
      description: 'Browse and search courses'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: TrendingUp,
      description: 'View your academic insights'
    },
    {
      id: 'schedule',
      label: 'Schedule',
      icon: Calendar,
      description: 'Plan your academic calendar'
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: FileText,
      description: 'Manage your academic files'
    }
  ];

  return (
    <div className="h-full w-80 bg-white/10 backdrop-blur-xl border-r border-white/20 shadow-2xl flex flex-col">
      {/* Navigation */}
      <div className="flex-1 overflow-y-auto">
        <nav className="p-6">
          <div className="space-y-4">
            {/* Main Chat with AI Feature */}
            <div className="mb-6">
              <button
                onClick={() => setActiveTab('chat')}
                className={`w-full flex items-center space-x-4 px-6 py-5 rounded-2xl transition-all duration-300 text-left group hover:scale-105 ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-r from-purple-500/30 to-pink-500/30 text-white border-2 border-purple-400/50 shadow-2xl shadow-purple-500/30 backdrop-blur-sm' 
                    : 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-purple-400/30 shadow-xl hover:shadow-2xl hover:border-purple-400/50'
                }`}
              >
                <div className={`p-3 rounded-xl transition-all duration-300 ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-br from-purple-500 to-pink-600 text-white shadow-lg' 
                    : 'bg-white/20 text-white'
                }`}>
                  <MessageCircle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-bold text-lg">Chat with AI</span>
                    <div className="w-2 h-2 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full animate-pulse"></div>
                  </div>
                  <p className="text-sm text-purple-200">Your intelligent academic assistant</p>
                </div>
              </button>
            </div>



            {/* Other Menu Items */}
            <div className="space-y-3">
              {menuItems.filter(item => item.id !== 'chat').map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center space-x-4 px-4 py-4 rounded-2xl transition-all duration-300 text-left group hover:scale-105 ${
                    activeTab === item.id 
                      ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-purple-400/30 shadow-2xl shadow-purple-500/20 backdrop-blur-sm' 
                      : 'text-purple-200 hover:bg-white/10 hover:text-white hover:shadow-lg'
                  }`}
                >
                  <div className={`p-2 rounded-xl transition-all duration-300 ${
                    activeTab === item.id 
                      ? 'bg-gradient-to-br from-purple-500 to-pink-600 text-white shadow-lg' 
                      : 'bg-white/10 text-purple-300 group-hover:bg-white/20 group-hover:text-white'
                  }`}>
                    <item.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <span className={`font-semibold ${activeTab === item.id ? 'text-white' : 'text-purple-200 group-hover:text-white'}`}>
                      {item.label}
                    </span>
                    <p className={`text-xs mt-1 ${activeTab === item.id ? 'text-purple-200' : 'text-purple-300 group-hover:text-purple-200'}`}>
                      {item.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;