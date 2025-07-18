import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { 
  Brain, 
  Zap, 
  ArrowRight, 
  Star, 
  CheckCircle, 
  Sparkles,
  BookOpen,
  Lightbulb,
  Globe,
  Play,
  ChevronDown,
  User,
  LogOut,
  LayoutDashboard,
  Edit
} from "lucide-react";
import "./Home.css";

const Home = () => {
  const [isVisible, setIsVisible] = useState(false);
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="home-container">
      {/* Animated Background */}
      <div className="animated-background">
        <div className="floating-shapes">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="floating-shape"
              style={{
                '--delay': `${Math.random() * 3}s`,
                '--duration': `${2 + Math.random() * 3}s`,
                '--x': `${Math.random() * 100}%`,
                '--y': `${Math.random() * 100}%`,
                '--size': `${20 + Math.random() * 60}px`
              }}
            />
          ))}
        </div>
      </div>

      {/* Header Section */}
      <header className="header-section">
        <nav className="nav-bar">
          <div className="nav-logo">
            <div className="logo-container">
              <Brain className="logo-icon" />
              <span className="logo-text">Advisor<span className="logo-highlight">AI</span></span>
            </div>
          </div>
          <div className="nav-actions">
            {currentUser ? (
              <>
                <NavLink to="/dashboard" className="nav-link">
                  <LayoutDashboard className="nav-icon" />
                  Dashboard
                </NavLink>
                <NavLink to="/profile" className="nav-link">
                  <User className="nav-icon" />
                  Profile
                </NavLink>
                <button onClick={logout} className="nav-link">
                  <LogOut className="nav-icon" />
                  Log Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="nav-link">
                  Sign In
                </NavLink>
                <NavLink to="/signup" className="nav-button">
                  Get Started
                  <ArrowRight className="button-icon" />
                </NavLink>
              </>
            )}
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles className="badge-icon" />
            <span>
              {currentUser ? 'Welcome back!' : 'AI-Powered Academic Guidance'}
            </span>
          </div>
          
          <h1 className="hero-title">
            {currentUser ? (
              <>
                Welcome back, <span className="title-highlight">{currentUser.displayName || currentUser.email?.split('@')[0] || 'Student'}!</span>
                <br />
                Ready to continue your academic journey?
              </>
            ) : (
              <>
                Your Personal
                <span className="title-highlight"> Academic Advisor</span>
                <br />
                Powered by AI
              </>
            )}
          </h1>
          
          <p className="hero-description">
            {currentUser ? (
              'Access your personalized dashboard, update your profile, or explore new academic opportunities with AI-powered guidance.'
            ) : (
              'Make smarter academic choices with personalized AI guidance. From course selection to university applications, get expert advice tailored to your unique goals and aspirations.'
            )}
          </p>
          
          <div className="hero-actions">
            {currentUser ? (
              <>
                <NavLink to="/dashboard" className="primary-button">
                  <LayoutDashboard className="button-icon" />
                  Go to Dashboard
                </NavLink>
                <NavLink to="/profile-completion" className="secondary-button">
                  <Edit className="button-icon" />
                  Update Profile
            </NavLink>
              </>
            ) : (
              <>
                <NavLink to="/signup" className="primary-button">
                  <Play className="button-icon" />
                  Start Your Journey
            </NavLink>
                <button className="secondary-button">
                  <BookOpen className="button-icon" />
                  Learn More
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <div className="cta-content">
            <h2 className="cta-title">
              {currentUser ? 'Ready to Explore More Academic Opportunities?' : 'Ready to Transform Your Academic Journey?'}
            </h2>
            <p className="cta-description">
              {currentUser ? 
                'Discover new courses, get personalized recommendations, and take your academic journey to the next level.' :
                'Join thousands of students who are already making smarter academic decisions with AI'
              }
            </p>
            {currentUser ? (
              <NavLink to="/dashboard" className="cta-button">
                <LayoutDashboard className="button-icon" />
                Explore Dashboard
              </NavLink>
            ) : (
              <NavLink to="/signup" className="cta-button">
                <Star className="button-icon" />
                Start Free Today
              </NavLink>
            )}
            </div>
            </div>
          </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-logo">
            <Brain className="footer-logo-icon" />
            <span>AdvisorAI</span>
          </div>
          <p className="footer-text">
            Empowering students with AI-driven academic guidance
          </p>
          <div className="footer-links">
            <a href="#" className="footer-link">Privacy Policy</a>
            <a href="#" className="footer-link">Terms of Service</a>
            <a href="#" className="footer-link">Contact Us</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} AdvisorAI. All rights reserved.</p>
        </div>
        </footer>

      {/* Scroll Indicator */}
      <div className="scroll-indicator">
        <ChevronDown className="scroll-icon" />
      </div>
    </div>
  );
};

export default Home;
