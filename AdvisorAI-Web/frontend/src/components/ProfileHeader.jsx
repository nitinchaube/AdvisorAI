import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import logo from "../utils/logo.png";
import {
  LayoutDashboard,
  Briefcase,
  LogOut,
  User,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";
import "./ProfileHeader.css";

const ProfileHeader = () => {
  const { currentUser, userProfile, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (e) {
      console.error("Logout error:", e);
    }
  };

  // Close user dropdown on outside click
  React.useEffect(() => {
    const handler = (e) => {
      if (!e.target.closest(".ph-user-dropdown-wrap")) setUserMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const displayName =
    currentUser?.displayName || currentUser?.email?.split("@")[0] || "User";

  return (
    <header className="ph-header">
      <nav className="ph-nav-bar">

        {/* ── Logo ─────────────────────────────────────────────────────── */}
        <div className="ph-logo-area">
          <div className="ph-logo-container" onClick={() => navigate("/")}>
            <div className="ph-logo-icon-wrapper">
              <img src={logo} alt="AdvisorAI Logo" className="ph-logo-image" />
            </div>
            <span className="ph-logo-text">
              Advisor<span className="ph-logo-highlight">AI</span>
            </span>
          </div>
        </div>

        {/* ── Hamburger (mobile) ───────────────────────────────────────── */}
        <button
          className="ph-hamburger-btn"
          onClick={() => setMobileMenuOpen((p) => !p)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* ── Nav actions ─────────────────────────────────────────────── */}
        <div className={`ph-nav-actions ${mobileMenuOpen ? "ph-mobile-open" : ""}`}>

          {/* Dashboard */}
          <button
            className="ph-nav-link"
            onClick={() => { navigate("/dashboard"); setMobileMenuOpen(false); }}
          >
            <LayoutDashboard className="ph-nav-icon" />
            Dashboard
          </button>

          {/* View Portfolio */}
          {userProfile?.portfolioName && (
            <a
              href={`/portfolio/${userProfile.portfolioName}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ph-nav-link"
              onClick={() => setMobileMenuOpen(false)}
            >
              <Briefcase className="ph-nav-icon" />
              Portfolio
            </a>
          )}

          {/* User menu */}
          <div className="ph-user-dropdown-wrap">
            <button
              className="ph-nav-button"
              onClick={() => setUserMenuOpen((p) => !p)}
            >
              <User className="ph-nav-icon" />
              {displayName}
              <ChevronDown
                size={14}
                className={`ph-chevron ${userMenuOpen ? "ph-chevron--open" : ""}`}
              />
            </button>

            {userMenuOpen && (
              <div className="ph-dropdown">
                <div className="ph-dropdown-info">
                  <p className="ph-dropdown-name">{displayName}</p>
                  <p className="ph-dropdown-email">{currentUser?.email}</p>
                </div>
                <div className="ph-dropdown-divider" />
                <button
                  className="ph-dropdown-item"
                  onClick={() => { setUserMenuOpen(false); navigate("/dashboard"); }}
                >
                  <LayoutDashboard size={15} />
                  Dashboard
                </button>
                <div className="ph-dropdown-divider" />
                <button
                  className="ph-dropdown-item ph-dropdown-item--danger"
                  onClick={() => { setUserMenuOpen(false); handleLogout(); }}
                >
                  <LogOut size={15} />
                  Logout
                </button>
              </div>
            )}
          </div>

        </div>
      </nav>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="ph-mobile-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}
    </header>
  );
};

export default ProfileHeader;
