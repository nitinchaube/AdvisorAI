import React from "react";
import { NavLink } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";
import "./StaticHeader.css";
import { useNavigate } from "react-router-dom";


const StaticHeader = ({ 
  showSignIn = true, 
  showSignUp = true,
  className = "" 
}) => {

  const navigate = useNavigate();
  return (
    <header className={`static-header-section ${className}`}>
      <nav className="static-nav-bar">
        <div className="static-nav-logo">
          <div className="static-logo-container" onClick={() => navigate("/")}>
            <div className="static-logo-icon-wrapper">
              <Sparkles className="static-logo-icon" />
            </div>
            <span className="static-logo-text">Advisor<span className="static-logo-highlight">AI</span></span>
          </div>
        </div>
        
        <div className="static-nav-actions">
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
        </div>
      </nav>
    </header>
  );
};

export default StaticHeader;
