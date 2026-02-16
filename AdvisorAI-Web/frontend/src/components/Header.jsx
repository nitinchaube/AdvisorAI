import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import logo from "../utils/logo.png";
import {
  User,
  LogOut,
  Menu,
  X,
  Crown,
  Shield,
  GraduationCap,
  Edit,
  ChevronRight,
  Home,
  Briefcase,
} from "lucide-react";

const Header = ({ onMenuToggle, sidebarOpen }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const { currentUser, userProfile, logout, isAdmin } = useAuth();
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
    <header className="bg-gradient-to-r from-slate-800 to-slate-700 backdrop-blur-xl border-b border-slate-600/20 px-3 sm:px-5 py-3 sm:py-4 shadow-2xl sticky top-0 z-50">
      <div className="flex items-center justify-between w-full">
        {/* Left side - Menu button and title */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-xl hover:bg-white/10 transition-all duration-300 hover:shadow-lg hover:scale-105 border border-white/10"
            title={sidebarOpen ? "Close detailed menu" : "Open detailed menu"}
          >
            {sidebarOpen ? (
              <X className="w-4 h-4 text-white" />
            ) : (
              <Menu className="w-4 h-4 text-white" />
            )}
          </button>

          <Link
            to="/"
            className="flex items-center space-x-2 sm:space-x-3 hover:scale-105 transition-all duration-300"
          >
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-white/10 overflow-hidden flex-shrink-0">
              <img src={logo} alt="AdvisorAI Logo" className="w-5 h-5 sm:w-6 sm:h-6 object-contain" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-white">
                Advisor<span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">AI</span>
              </h1>
            </div>
          </Link>
        </div>

        {/* Right side - Portfolio button and User menu */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Portfolio Button */}
          {userProfile?.portfolioName ? (
            <a
              href={`/portfolio/${userProfile.portfolioName}`}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative flex items-center space-x-2.5 px-3 sm:px-5 py-2 sm:py-2.5 text-slate-200 hover:text-white font-medium transition-all duration-300 hover:scale-105"
            >
              <div className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-400 to-purple-400 group-hover:w-full transition-all duration-300"></div>
              <div className="relative flex items-center space-x-2">
                <Briefcase className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                <span className="text-sm hidden sm:inline">View Portfolio</span>
              </div>
            </a>
          ) : (
            <button
              onClick={() => navigate("/profile-completion")}
              className="group relative flex items-center space-x-2.5 px-3 sm:px-5 py-2 sm:py-2.5 text-slate-400 hover:text-slate-300 font-medium transition-all duration-300 cursor-pointer"
              title="Complete your profile to get a portfolio"
            >
              <div className="relative flex items-center space-x-2">
                <Briefcase className="w-4 h-4" />
                <span className="text-sm hidden sm:inline">Set Portfolio</span>
              </div>
            </button>
          )}

          {/* Enhanced User Menu */}
          <div className="relative user-menu-container">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-3 p-2.5 rounded-xl hover:bg-white/10 transition-all duration-300 hover:shadow-lg hover:scale-105 group border border-white/10"
            >
              {/* Profile Avatar with Status */}
              <div className="relative">
                <div className="w-9 h-9 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 border-2 border-white/10">
                  <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
              </div>

              {/* User Info */}
              <div className="hidden sm:block text-left">
                <div className="flex items-center space-x-2">
                  <p className="text-sm font-semibold text-white">
                    {currentUser?.displayName ||
                      currentUser?.email?.split("@")[0] ||
                      "User"}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <GraduationCap className="w-3 h-3 text-slate-300" />
                  <p className="text-xs text-slate-300 font-medium">
                    {currentUser?.email || "Student"}
                  </p>
                </div>
              </div>
            </button>

            {/* Enhanced Dropdown Menu */}
            {showUserMenu && (
              <div
                className="absolute right-0 mt-3 w-[calc(100vw-2rem)] sm:w-80 max-w-80 max-h-[80vh] bg-gradient-to-br from-slate-800/95 via-slate-700/90 to-slate-600/95 backdrop-blur-2xl rounded-3xl shadow-2xl border border-slate-500/20 py-6 z-50 overflow-y-auto overflow-x-hidden"
                style={{ pointerEvents: "auto" }}
              >
                {/* Background decoration */}
                <div
                  className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-indigo-500/5"
                  style={{ zIndex: 1 }}
                ></div>
                <div
                  className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-2xl"
                  style={{ zIndex: 1 }}
                ></div>
                <div
                  className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-br from-indigo-500/10 to-blue-500/10 rounded-full blur-2xl"
                  style={{ zIndex: 1 }}
                ></div>

                {/* User Profile Section */}
                <div className="relative px-6 py-4 border-b border-slate-500/20">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-xl ring-4 ring-white/10 border-2 border-white/10">
                        <User className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                      </div>
                      <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full border-3 border-slate-800 shadow-lg animate-pulse"></div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-bold text-white truncate">
                          {currentUser?.displayName ||
                            currentUser?.email?.split("@")[0] ||
                            "User"}
                        </h3>
                        
                      </div>
                      <p className="text-sm text-slate-300 mb-2 truncate">
                        {currentUser?.email || "user@example.com"}
                      </p>
                      <div className="flex items-center space-x-2">
                        <GraduationCap className="w-3 h-3 text-slate-300 flex-shrink-0" />
                        <span className="text-xs text-slate-300 truncate">
                          {currentUser?.email ? "Student" : "Guest User"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

              

                {/* Menu Items */}
                <div className="relative py-2" style={{ zIndex: 10 }}>
                  {/* <Link
                    to="/profile-data"
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-slate-300 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                        <User className="w-4 h-4" />
                      </div>
                      <span className="font-medium">View Profile</span>
                    </div>
                    <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                  </Link> */}

                  <Link
                    to="/profile-completion"
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-slate-300 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
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
                    className="w-full flex items-center justify-between px-6 py-3 text-sm text-slate-300 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
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

                  {userProfile?.portfolioName ? (
                    <a
                      href={`/portfolio/${userProfile.portfolioName}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-slate-300 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-white/10 rounded-lg group-hover:bg-white/20 transition-all duration-300 group-hover:scale-110">
                          <Briefcase className="w-4 h-4" />
                        </div>
                        <span className="font-medium">View Portfolio</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                    </a>
                  ) : (
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        navigate("/profile-completion");
                      }}
                      className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-slate-400 hover:text-slate-300 group mx-2 rounded-xl cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-white/5 rounded-lg group-hover:bg-white/10 transition-all duration-300">
                          <Briefcase className="w-4 h-4" />
                        </div>
                        <span className="font-medium">Set Portfolio</span>
                      </div>
                      <ChevronRight className="w-4 h-4 opacity-30" />
                    </button>
                  )}

                  {isAdmin() && (
                    <Link
                      to="/admin"
                      className="w-full flex items-center justify-between px-6 py-3 text-sm text-slate-300 hover:bg-white/10 transition-all duration-300 hover:text-white group mx-2 rounded-xl"
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
                    handleLogout();
                  }}
                  className="w-full flex items-center space-x-3 px-6 py-3 text-sm text-red-300 hover:bg-red-500/20 transition-all duration-300 hover:text-red-200 group mx-2 rounded-xl cursor-pointer relative"
                  style={{
                    pointerEvents: "auto",
                    zIndex: 10,
                    position: "relative",
                  }}
                >
                  <div className="p-2 bg-red-500/20 rounded-lg group-hover:bg-red-500/30 transition-all duration-300 group-hover:scale-110">
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
