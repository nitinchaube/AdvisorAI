import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  Bell,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  Search,
  Crown,
  Shield,
  BookOpen,
  GraduationCap,
  Mail,
  Phone,
  MapPin,
  Edit,
  Database,
  ChevronRight,
  Check,
  Home,
} from "lucide-react";

const Header = ({ onMenuToggle, sidebarOpen }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notifications] = useState([
    { id: 1, message: "New course recommendations available", unread: true },
    { id: 2, message: "Your chat session has been saved", unread: false },
  ]);

  const { currentUser, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      // Don't close if clicking on logout button or its children
      if (event.target.closest('button[onClick*="handleLogout"]')) {
        return;
      }

      if (showUserMenu && !event.target.closest(".user-menu-container")) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showUserMenu]);

  const unreadCount = notifications.filter((n) => n.unread).length;

  const handleLogout = async () => {
    try {
      console.log("Header: Logout button clicked");
      await logout();
      console.log("Header: Logout successful, navigating to login");
      setShowUserMenu(false);
      navigate("/login");
    } catch (error) {
      console.error("Header: Logout error:", error);
    }
  };

  return (
    <header className="bg-white/10 backdrop-blur-xl border-b border-white/20 px-6 py-4 shadow-2xl sticky top-0 z-50">
      <div className="flex items-center justify-between">
        {/* Left side - Menu button and title */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-xl hover:bg-white/20 transition-all duration-300 hover:shadow-lg hover:scale-105"
            title={sidebarOpen ? "Close detailed menu" : "Open detailed menu"}
          >
            {sidebarOpen ? (
              <X className="w-5 h-5 text-white" />
            ) : (
              <Menu className="w-5 h-5 text-white" />
            )}
          </button>

          <Link
            to="/"
            className="flex items-center space-x-3 hover:scale-105 transition-all duration-300"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 rounded-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
                AdvisorAI
              </h1>
              <p className="text-xs text-purple-200 font-medium">
                Your Academic Assistant
              </p>
            </div>
          </Link>
        </div>

        {/* Center - Search bar */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-purple-300 w-4 h-4" />
            <input
              type="text"
              placeholder="Search courses, professors, or ask a question..."
              className="w-full pl-12 pr-4 py-3 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 bg-white/10 backdrop-blur-sm text-white placeholder-purple-200 transition-all duration-300"
            />
          </div>
        </div>

        {/* Right side - Notifications and user menu */}
        <div className="flex items-center space-x-3">
          {/* Notifications */}
          <div className="relative">
            <button
              className="relative p-3 text-purple-200 hover:text-white hover:bg-white/20 rounded-xl transition-all duration-300 hover:shadow-lg hover:scale-105"
              onClick={() => setShowUserMenu(false)}
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-r from-rose-500 to-pink-500 text-white text-xs rounded-full flex items-center justify-center font-semibold shadow-lg animate-pulse">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>

          {/* Enhanced User Menu */}
          <div className="relative user-menu-container">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-3 p-3 rounded-xl hover:bg-white/20 transition-all duration-300 hover:shadow-lg hover:scale-105 group"
            >
              {/* Profile Avatar with Status */}
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 rounded-full flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300">
                  <User className="w-6 h-6 text-white" />
                </div>
                {/* Online Status Indicator */}
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full border-2 border-white shadow-lg animate-pulse"></div>
              </div>

              {/* User Info */}
              <div className="hidden sm:block text-left">
                <div className="flex items-center space-x-2">
                  <p className="text-sm font-semibold text-white">
                    {currentUser?.displayName ||
                      currentUser?.email?.split("@")[0] ||
                      "User"}
                  </p>
                  <div className="flex items-center space-x-1">
                    <Crown className="w-3 h-3 text-yellow-400" />
                    <span className="text-xs text-yellow-300 font-medium">
                      Premium
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <GraduationCap className="w-3 h-3 text-purple-300" />
                  <p className="text-xs text-purple-200 font-medium">
                    {currentUser?.email || "Student"}
                  </p>
                </div>
              </div>
            </button>

            {/* Enhanced Dropdown Menu */}
            {showUserMenu && (
              <div
                className="absolute right-0 mt-3 w-80 max-h-[80vh] bg-gradient-to-br from-slate-900/95 via-purple-900/90 to-indigo-900/95 backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/20 py-6 z-50 overflow-y-auto overflow-x-hidden"
                style={{ pointerEvents: "auto" }}
              >
                {/* Background decoration */}
                <div
                  className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-pink-500/5 to-rose-500/5"
                  style={{ zIndex: 1 }}
                ></div>
                <div
                  className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-2xl"
                  style={{ zIndex: 1 }}
                ></div>
                <div
                  className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-full blur-2xl"
                  style={{ zIndex: 1 }}
                ></div>

                {/* User Profile Section */}
                <div className="relative px-6 py-4 border-b border-white/10">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <div className="w-16 h-16 bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 rounded-full flex items-center justify-center shadow-xl ring-4 ring-white/10">
                        <User className="w-8 h-8 text-white" />
                      </div>
                      <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full border-3 border-slate-900 shadow-lg animate-pulse"></div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-bold text-white truncate">
                          {currentUser?.displayName ||
                            currentUser?.email?.split("@")[0] ||
                            "User"}
                        </h3>
                        <div className="flex items-center space-x-1 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 px-3 py-1 rounded-full border border-yellow-500/30">
                          <Crown className="w-3 h-3 text-yellow-400" />
                          <span className="text-xs text-yellow-300 font-semibold">
                            Premium
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-purple-200 mb-2 truncate">
                        {currentUser?.email || "user@example.com"}
                      </p>
                      <div className="flex items-center space-x-2">
                        <GraduationCap className="w-3 h-3 text-purple-300 flex-shrink-0" />
                        <span className="text-xs text-purple-300 truncate">
                          {currentUser?.email ? "Student" : "Guest User"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="relative px-6 py-4 border-b border-white/10">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors duration-300">
                      <div className="text-xl font-bold text-white mb-1">
                        24
                      </div>
                      <div className="text-xs text-purple-300 font-medium">
                        Courses
                      </div>
                    </div>
                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors duration-300">
                      <div className="text-xl font-bold text-white mb-1">
                        3.8
                      </div>
                      <div className="text-xs text-purple-300 font-medium">
                        GPA
                      </div>
                    </div>
                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors duration-300">
                      <div className="text-xl font-bold text-white mb-1">
                        156
                      </div>
                      <div className="text-xs text-purple-300 font-medium">
                        Credits
                      </div>
                    </div>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="relative py-2" style={{ zIndex: 10 }}>
                  <Link
                    to="/profile-data"
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                        <User className="w-4 h-4" />
                      </div>
                      <span className="font-medium">View Profile</span>
                    </div>
                    <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                  </Link>

                  <Link
                    to="/profile-completion"
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                        <Edit className="w-4 h-4" />
                      </div>
                      <span className="font-medium">Edit Profile</span>
                    </div>
                    <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                  </Link>

                  <Link
                    to="/"
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                        <Home className="w-4 h-4" />
                      </div>
                      <span className="font-medium">Home</span>
                    </div>
                    <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                  </Link>

                  <button className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl">
                    <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                      <BookOpen className="w-4 h-4" />
                    </div>
                    <span className="font-medium">My Courses</span>
                  </button>

                  <button className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl">
                    <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                      <Settings className="w-4 h-4" />
                    </div>
                    <span className="font-medium">Settings</span>
                  </button>
                  {isAdmin() && (
                    <Link
                      to="/admin"
                      className="w-full flex items-center justify-between px-6 py-3 text-sm text-purple-200 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                          <Shield className="w-4 h-4" />
                        </div>
                        <span className="font-medium">Admin Portal</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                    </Link>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    alert("Logout button clicked!");
                    console.log("Logout button clicked!");
                    handleLogout();
                  }}
                  className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-rose-300 hover:bg-rose-500/20 transition-all duration-300 hover:text-rose-200 group mx-2 rounded-xl cursor-pointer relative"
                  style={{
                    pointerEvents: "auto",
                    zIndex: 10,
                    position: "relative",
                  }}
                >
                  <div className="p-2 bg-rose-500/20 rounded-lg group-hover:bg-rose-500/30 transition-all duration-300 group-hover:scale-110">
                    <LogOut className="w-4 h-4" />
                  </div>
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
