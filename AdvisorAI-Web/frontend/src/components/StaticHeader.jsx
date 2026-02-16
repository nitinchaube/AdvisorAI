import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, LayoutDashboard, User, LogOut, Menu, X } from "lucide-react";
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
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

        {/* Hamburger button — visible only on mobile via CSS */}
        <button
          className="static-hamburger-btn"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        
        <div className={`static-nav-actions ${mobileMenuOpen ? "mobile-open" : ""}`}>
          {currentUser ? (
            // Authenticated user actions
            <>
              <NavLink to="/dashboard" className="static-nav-link" onClick={() => setMobileMenuOpen(false)}>
                <LayoutDashboard className="static-nav-icon" />
                Dashboard
              </NavLink>
              <NavLink to="/profile-completion" className="static-nav-link" onClick={() => setMobileMenuOpen(false)}>
                <User className="static-nav-icon" />
                Profile
              </NavLink>
              <button onClick={() => { onLogout?.(); setMobileMenuOpen(false); }} className="static-nav-link">
                <LogOut className="static-nav-icon" />
                Log Out
              </button>
            </>
          ) : (
            // Non-authenticated user actions
            <>
              {showSignIn && (
                <NavLink to="/login" className="static-nav-link" onClick={() => setMobileMenuOpen(false)}>
                  Sign In
                </NavLink>
              )}
              {showSignUp && (
                <NavLink to="/signup" className="static-nav-button" onClick={() => setMobileMenuOpen(false)}>
                  Get Started
                  <ArrowRight className="static-button-icon" />
                </NavLink>
              )}
            </>
          )}
        </div>
      </nav>

      {/* Overlay to close menu when tapping outside */}
      {mobileMenuOpen && (
        <div className="static-mobile-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}
    </header>
  );
};

export default StaticHeader;
