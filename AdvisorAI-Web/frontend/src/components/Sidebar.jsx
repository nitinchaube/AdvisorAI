import React, { useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  MessageCircle,
  History,
  Star,
  BookOpen,
  Bot,
  TrendingUp,
  Brain,
  Sparkles,
  Briefcase,
  GraduationCap,
  Palette,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const sidebarRef = useRef(null);
  const { isAdmin } = useAuth();

  // Preserve scroll position when navigating
  useEffect(() => {
    if (sidebarRef.current) {
      const savedScrollTop = sessionStorage.getItem('sidebarScrollTop');
      if (savedScrollTop) {
        sidebarRef.current.scrollTop = parseInt(savedScrollTop);
      }
    }
  }, [location.pathname]);

  // Save scroll position before navigation
  const handleNavigation = (path) => {
    if (sidebarRef.current) {
      sessionStorage.setItem('sidebarScrollTop', sidebarRef.current.scrollTop.toString());
    }
    navigate(path);
  };

  const menuItems = [
    {
      id: "chat",
      label: "Chat with AI",
      icon: MessageCircle,
      description: "Ask questions and get AI-powered advice",
      path: "/chat",
    },
    {
      id: "job-search",
      label: "Job Search",
      icon: Briefcase,
      description: "Find full-time job opportunities",
      path: "/job-search",
    },
    {
      id: "internship-search",
      label: "Internship Search",
      icon: GraduationCap,
      description: "Discover internship opportunities",
      path: "/internship-search",
    },
    {
      id: "history",
      label: "Chat History",
      icon: History,
      description: "View your previous conversations",
      path: "/chat-history",
    },
    {
      id: "courses",
      label: "Course Explorer",
      icon: BookOpen,
      description: "Browse and search courses",
      path: "/course-explorer",
    },
    
    
    {
      id: "analytics",
      label: "Analytics",
      icon: TrendingUp,
      description: "View your academic insights",
      path: "/analytics",
    },
  ];

  const getActiveTab = () => {
    const currentPath = location.pathname;
    const menuItem = menuItems.find(item => item.path === currentPath);
    return menuItem ? menuItem.id : 'chat';
  };

  const activeTab = getActiveTab();

  const activeItemStyle = {
    background: `linear-gradient(to right, var(--theme-sidebar-active-from), var(--theme-sidebar-active-to))`,
    borderColor: `var(--theme-sidebar-active-border)`,
    boxShadow: `0 4px 15px var(--theme-sidebar-active-from)`,
  };
  const activeIconStyle = {
    background: `linear-gradient(to bottom right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
  };

  return (
    <div className="h-full w-72 sm:w-80 backdrop-blur-xl border-r border-slate-200/60 shadow-xl flex flex-col" style={{ background: "linear-gradient(to bottom right, white, #f8fafc, rgba(239,246,255,0.5))" }}>
      {/* Navigation */}
      <div className="flex-1 overflow-y-auto" ref={sidebarRef}>
        <nav className="p-6">
          <div className="space-y-4">
            {/* Main Chat with AI Feature */}
            <div className="mb-6">
              <button
                onClick={() => handleNavigation("/chat")}
                className={`w-full flex items-center space-x-4 px-6 py-5 rounded-2xl transition-all duration-300 text-left group hover:scale-105 border-2 ${
                  activeTab === "chat"
                    ? "text-slate-800 shadow-lg backdrop-blur-sm"
                    : "bg-white/80 text-slate-700 border-transparent border shadow-sm hover:shadow-md"
                }`}
                style={activeTab === "chat" ? activeItemStyle : {}}
              >
                <div
                  className="p-3 rounded-xl transition-all duration-300 shadow-md text-white"
                  style={activeTab === "chat" ? activeIconStyle : { background: "var(--theme-accent-bg)", color: "var(--theme-accent-dark)" }}
                >
                  <MessageCircle className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-bold text-lg">Chat with AI</span>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: "var(--theme-accent)" }}></div>
                  </div>
                  <p className="text-sm text-slate-600">
                    Your intelligent academic assistant
                  </p>
                </div>
              </button>
            </div>

            {/* Other Menu Items */}
            <div className="space-y-3">
              {menuItems
                .filter((item) => item.id !== "chat")
                .map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.path)}
                    className={`w-full flex items-center space-x-4 px-4 py-4 rounded-2xl transition-all duration-300 text-left group hover:scale-105 border ${
                      activeTab === item.id
                        ? "text-slate-800 shadow-lg backdrop-blur-sm"
                        : "text-slate-600 hover:bg-white/80 hover:text-slate-800 hover:shadow-md border-transparent hover:border-slate-200/60"
                    }`}
                    style={activeTab === item.id ? activeItemStyle : {}}
                  >
                    <div
                      className="p-2 rounded-xl transition-all duration-300 text-white shadow-md"
                      style={activeTab === item.id ? activeIconStyle : { background: "var(--theme-accent-bg)", color: "var(--theme-accent-dark)" }}
                    >
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <span
                        className={`font-semibold ${
                          activeTab === item.id
                            ? "text-slate-800"
                            : "text-slate-600 group-hover:text-slate-800"
                        }`}
                      >
                        {item.label}
                      </span>
                      <p
                        className={`text-xs mt-1 ${
                          activeTab === item.id
                            ? "text-slate-600"
                            : "text-slate-500 group-hover:text-slate-600"
                        }`}
                      >
                        {item.description}
                      </p>
                    </div>
                  </button>
                ))}
            </div>

            {/* Admin Tools Section */}
            {isAdmin && isAdmin() && (
              <div className="mt-8 pt-6 border-t border-slate-200/60">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
                  Admin Tools
                </h3>
                <div className="space-y-3">
                  <button
                    onClick={() => handleNavigation("/website-theme")}
                    className={`w-full flex items-center space-x-4 px-4 py-4 rounded-2xl transition-all duration-300 text-left group hover:scale-105 border ${
                      activeTab === "website-theme"
                        ? "text-slate-800 shadow-lg backdrop-blur-sm"
                        : "text-slate-600 hover:bg-white/80 hover:text-slate-800 hover:shadow-md border-transparent hover:border-slate-200/60"
                    }`}
                    style={activeTab === "website-theme" ? activeItemStyle : {}}
                  >
                    <div
                      className="p-2 rounded-xl transition-all duration-300 text-white shadow-md"
                      style={activeTab === "website-theme" ? activeIconStyle : { background: "var(--theme-accent-bg)", color: "var(--theme-accent-dark)" }}
                    >
                      <Palette className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <span className={`font-semibold ${activeTab === "website-theme" ? "text-slate-800" : "text-slate-600 group-hover:text-slate-800"}`}>
                        Website Theme
                      </span>
                      <p className={`text-xs mt-1 ${activeTab === "website-theme" ? "text-slate-600" : "text-slate-500 group-hover:text-slate-600"}`}>
                        Customize the website's color theme
                      </p>
                    </div>
                  </button>
                </div>
              </div>
            )}
          </div>
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;
