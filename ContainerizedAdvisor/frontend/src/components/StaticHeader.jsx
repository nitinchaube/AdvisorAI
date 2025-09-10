import React from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, LayoutDashboard, User, LogOut } from "lucide-react";
import "./StaticHeader.css";
import { useNavigate } from "react-router-dom";
import logo from "../utils/logo.png";

const StaticHeader = ({ 
  showSignIn = true, 
  showSignUp = true,
  className = "",
  currentUser = null,
  onLogout = null
}) => {

  const navigate = useNavigate();
  
  return (
    <header className={`static-header-section ${className}`}>
      <nav className="static-nav-bar">
        <div className="static-nav-logo">
          <div className="static-logo-container" onClick={() => navigate("/")}>
            <div className="static-logo-icon-wrapper">
              <img src={logo} alt="AdvisorAI Logo" className="static-logo-image" />
            </div>
            <span className="static-logo-text">Advisor<span className="static-logo-highlight">AI</span></span>
          </div>
        </div>
        
        <div className="static-nav-actions">
          {currentUser ? (
            // Authenticated user actions
            <>
              <NavLink to="/dashboard" className="static-nav-link">
                <LayoutDashboard className="static-nav-icon" />
                Dashboard
              </NavLink>
              <NavLink to="/profile-completion" className="static-nav-link">
                <User className="static-nav-icon" />
                Profile
              </NavLink>
              <button onClick={onLogout} className="static-nav-link">
                <LogOut className="static-nav-icon" />
                Log Out
              </button>
            </>
          ) : (
            // Non-authenticated user actions
            <>
              {showSignIn && (
                <NavLink to="/login" className="static-nav-link">
                  Sign In
                </NavLink>
              )}
              {showSignUp && (
                <NavLink to="/signup" className="static-nav-button">
                  Get Started
                  <ArrowRight className="static-button-icon" />
                </NavLink>
              )}
            </>
          )}
        </div>
      </nav>
    </header>
  );
};

export default StaticHeader;
