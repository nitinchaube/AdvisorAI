import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  MessageCircle,
  History,
  Star,
  BookOpen,
  TrendingUp,
  Calendar,
  FileText,
  Menu,
  Briefcase,
  GraduationCap,
} from "lucide-react";
import logo from "../utils/logo.png";

const CompactSidebar = ({ sidebarOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const menuItems = [
    {
      id: "chat",
      icon: MessageCircle,
      label: "Chat with AI",
      path: "/chat",
      color: "blue",
    },
    {
      id: "job-search",
      icon: Briefcase,
      label: "Job Search",
      path: "/job-search",
      color: "purple",
    },
    {
      id: "internship-search",
      icon: GraduationCap,
      label: "Internship Search",
      path: "/internship-search",
      color: "teal",
    },
    {
      id: "history",
      icon: History,
      label: "Chat History",
      path: "/chat-history",
      color: "gray",
    },
    {
      id: "courses",
      icon: BookOpen,
      label: "Course Explorer",
      path: "/course-explorer",
      color: "green",
    },
    {
      id: "ratings",
      icon: Star,
      label: "Ratings & Reviews",
      path: "/ratings",
      color: "yellow",
    },
    {
      id: "analytics",
      icon: TrendingUp,
      label: "Analytics",
      path: "/analytics",
      color: "indigo",
    },
  ];

  const getActiveTab = () => {
    const currentPath = location.pathname;
    const menuItem = menuItems.find((item) => item.path === currentPath);
    return menuItem ? menuItem.id : "chat";
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const activeTab = getActiveTab();

  const getColorClasses = (color, isActive) => {
    if (isActive) {
      const activeColors = {
        blue: "bg-blue-600 text-white",
        gray: "bg-gray-600 text-white",
        yellow: "bg-yellow-600 text-white",
        green: "bg-green-600 text-white",
        indigo: "bg-indigo-600 text-white",
        emerald: "bg-emerald-600 text-white",
        orange: "bg-orange-600 text-white",
        purple: "bg-purple-600 text-white",
        teal: "bg-teal-600 text-white",
      };
      return activeColors[color];
    }

    const inactiveColors = {
      blue: "bg-blue-100 text-blue-700 hover:bg-blue-200",
      gray: "bg-gray-100 text-gray-700 hover:bg-gray-200",
      yellow: "bg-yellow-100 text-yellow-700 hover:bg-yellow-200",
      green: "bg-green-100 text-green-700 hover:bg-green-200",
      indigo: "bg-indigo-100 text-indigo-700 hover:bg-indigo-200",
      emerald: "bg-emerald-100 text-emerald-700 hover:bg-emerald-200",
      orange: "bg-orange-100 text-orange-700 hover:bg-orange-200",
      purple: "bg-purple-100 text-purple-700 hover:bg-purple-200",
      teal: "bg-teal-100 text-teal-700 hover:bg-teal-200",
    };
    return inactiveColors[color];
  };

  return (
    <div className="h-full w-16 bg-white border-r-2 border-gray-300 shadow-lg flex flex-col z-30 relative">
      {/* Logo - Only visible when full sidebar is closed */}
      {!sidebarOpen && (
        <div className="flex-shrink-0 p-3 border-b-2 border-gray-300 bg-gray-50">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center shadow-md overflow-hidden">
            <img src={logo} alt="AdvisorAI" className="w-6 h-6 object-contain" />
          </div>
        </div>
      )}

      {/* Navigation Icons */}
      <div
        className={`flex-1 py-3 ${sidebarOpen ? "pt-3" : "pt-3"} bg-gray-50`}
      >
        <div className="space-y-2">
          {menuItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavigation(item.path)}
                className="group relative w-full flex items-center justify-center p-2 transition-all duration-200"
                title={item.label}
              >
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r-full shadow-md"></div>
                )}

                {/* Icon container */}
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200 shadow-sm ${getColorClasses(
                    item.color,
                    isActive
                  )}`}
                >
                  <item.icon className="w-5 h-5" />
                </div>

                {/* Tooltip */}
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
                  {item.label}
                  <div className="absolute right-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-l-4 border-l-gray-900 border-t-2 border-t-transparent border-b-2 border-b-transparent"></div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom section */}
      <div className="flex-shrink-0 p-3 border-t-2 border-gray-300 bg-gray-50">
        <button
          className="w-10 h-10 bg-gray-200 hover:bg-gray-300 rounded-lg flex items-center justify-center transition-all duration-200 text-gray-700 hover:text-gray-900 shadow-sm"
          title="Menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default CompactSidebar;
