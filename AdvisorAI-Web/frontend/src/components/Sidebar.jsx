import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
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

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      id: 'chat',
      label: 'Chat with AI',
      icon: MessageCircle,
      description: 'Ask questions and get AI-powered advice',
      path: '/chat'
    },
    {
      id: 'history',
      label: 'Chat History',
      icon: History,
      description: 'View your previous conversations',
      path: '/chat-history'
    },
    {
      id: 'ratings',
      label: 'Ratings & Reviews',
      icon: Star,
      description: 'Rate professors and courses',
      path: '/ratings'
    },
    {
      id: 'courses',
      label: 'Course Explorer',
      icon: BookOpen,
      description: 'Browse and search courses',
      path: '/course-explorer'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: TrendingUp,
      description: 'View your academic insights',
      path: '/analytics'
    },
    {
      id: 'schedule',
      label: 'Schedule',
      icon: Calendar,
      description: 'Plan your academic calendar',
      path: '/schedule'
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: FileText,
      description: 'Manage your academic files',
      path: '/documents'
    }
  ];

  const getActiveTab = () => {
    const currentPath = location.pathname;
    const menuItem = menuItems.find(item => item.path === currentPath);
    return menuItem ? menuItem.id : 'chat';
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const activeTab = getActiveTab();

  return (
    <div className="h-full w-80 bg-gradient-to-br from-white via-slate-50 to-blue-50/30 backdrop-blur-xl border-r border-slate-200/60 shadow-xl flex flex-col">
      {/* Navigation */}
      <div className="flex-1 overflow-y-auto">
        <nav className="p-6">
          <div className="space-y-4">
            {/* Main Chat with AI Feature */}
            <div className="mb-6">
              <button
                onClick={() => handleNavigation('/chat')}
                className={`w-full flex items-center space-x-4 px-6 py-5 rounded-2xl transition-all duration-300 text-left group hover:scale-105 ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-r from-blue-400/20 to-cyan-500/20 text-slate-800 border-2 border-blue-400/60 shadow-lg shadow-blue-400/20 backdrop-blur-sm' 
                    : 'bg-white/80 text-slate-700 border border-slate-200/60 shadow-sm hover:shadow-md hover:border-blue-400/50'
                }`}
              >
                <div className={`p-3 rounded-xl transition-all duration-300 ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-br from-blue-400 to-cyan-500 text-white shadow-md' 
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  <MessageCircle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-bold text-lg">Chat with AI</span>
                    <div className="w-2 h-2 bg-gradient-to-r from-blue-400 to-cyan-500 rounded-full animate-pulse"></div>
                  </div>
                  <p className="text-sm text-slate-600">Your intelligent academic assistant</p>
                </div>
              </button>
            </div>

            {/* Other Menu Items */}
            <div className="space-y-3">
              {menuItems.filter(item => item.id !== 'chat').map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigation(item.path)}
                  className={`w-full flex items-center space-x-4 px-4 py-4 rounded-2xl transition-all duration-300 text-left group hover:scale-105 ${
                    activeTab === item.id 
                      ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-slate-800 border border-blue-400/50 shadow-lg shadow-blue-500/20 backdrop-blur-sm' 
                      : 'text-slate-600 hover:bg-white/80 hover:text-slate-800 hover:shadow-md border border-transparent hover:border-slate-200/60'
                  }`}
                >
                  <div className={`p-2 rounded-xl transition-all duration-300 ${
                    activeTab === item.id 
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-md' 
                      : 'bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-600'
                  }`}>
                    <item.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <span className={`font-semibold ${activeTab === item.id ? 'text-slate-800' : 'text-slate-600 group-hover:text-slate-800'}`}>
                      {item.label}
                    </span>
                    <p className={`text-xs mt-1 ${activeTab === item.id ? 'text-slate-600' : 'text-slate-500 group-hover:text-slate-600'}`}>
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