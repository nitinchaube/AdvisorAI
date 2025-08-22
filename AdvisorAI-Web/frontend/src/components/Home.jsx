import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { 
  Brain, 
  ArrowRight, 
  Star, 
  CheckCircle, 
  Sparkles,
  BookOpen,
  Lightbulb,
  Globe,
  Play,
  User,
  LogOut,
  LayoutDashboard,
  Edit,
  GraduationCap,
  Target,
  Users,
  Award,
  Shield,
  Mail,
  TrendingUp,
  Clock,
  Zap,
  ChevronRight
} from "lucide-react";
import StaticHeader from "./StaticHeader";
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
      {/* Header Section */}
      {currentUser ? (
        <header className="header-section">
          <nav className="nav-bar">
            <div className="nav-logo">
              <div className="logo-container">
                <div className="logo-icon-wrapper">
                  <Brain className="logo-icon" />
                </div>
                <span className="logo-text">Advisor<span className="logo-highlight">AI</span></span>
              </div>
            </div>
            <div className="nav-actions">
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
            </div>
          </nav>
        </header>
      ) : (
        <StaticHeader showSignIn={true} showSignUp={true} />
      )}

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
        </div>
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

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <div className="how-it-works-container">
          <div className="section-header">
            <div className="section-badge">
              <Zap className="badge-icon" />
              <span>Simple Process</span>
            </div>
            <h2 className="section-title">How It Works</h2>
            <p className="section-subtitle">Get started in just three simple steps and begin your journey to academic success</p>
          </div>
          
          <div className="steps-container">
            <div className="step-item">
              <div className="step-number">01</div>
              <div className="step-content">
                <h3 className="step-title">Create Your Profile</h3>
                <p className="step-description">Tell us about your academic background, interests, and goals to get personalized recommendations.</p>
              </div>
            </div>
            
            <div className="step-item">
              <div className="step-number">02</div>
              <div className="step-content">
                <h3 className="step-title">Get AI Guidance</h3>
                <p className="step-description">Receive intelligent suggestions for courses, universities, and career paths tailored to your profile.</p>
              </div>
            </div>
            
            <div className="step-item">
              <div className="step-number">03</div>
              <div className="step-content">
                <h3 className="step-title">Achieve Your Goals</h3>
                <p className="step-description">Follow your personalized roadmap and track your progress toward academic and career success.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <div className="cta-background">
            <div className="cta-pattern"></div>
          </div>
          <div className="cta-content">
            <h2 className="cta-title">
              {currentUser ? 'Ready to Explore More Academic Opportunities?' : 'Ready to Transform Your Academic Journey?'}
            </h2>
            <p className="cta-description">
              {currentUser ? 
                'Discover new courses, get personalized recommendations, and take your academic journey to the next level.' :
                'Join thousands of students who are already making smarter academic decisions with AI-powered guidance.'
              }
            </p>
            {currentUser ? (
              <NavLink to="/dashboard" className="cta-button">
                <LayoutDashboard className="button-icon" />
                Explore Dashboard
              </NavLink>
            ) : (
              <NavLink to="/signup" className="cta-button">
                <Play className="button-icon" />
                Start Your Journey
              </NavLink>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-main">
            <div className="footer-brand">
              <div className="footer-logo">
                <div className="footer-logo-icon-wrapper">
                  <Brain className="footer-logo-icon" />
                </div>
                <span>AdvisorAI</span>
              </div>
              <p className="footer-text">
                Empowering students with AI-driven academic guidance for a brighter future. Make smarter decisions, achieve your goals, and unlock your potential.
              </p>
            </div>
            
            <div className="footer-links">
              <div className="footer-link-group">
                <h4>Product</h4>
                <a href="#" className="footer-link">Features</a>
                <a href="#" className="footer-link">Pricing</a>
                <a href="#" className="footer-link">API</a>
                <a href="#" className="footer-link">Documentation</a>
              </div>
              
              <div className="footer-link-group">
                <h4>Company</h4>
                <a href="#" className="footer-link">About</a>
                <a href="#" className="footer-link">Blog</a>
                <a href="#" className="footer-link">Careers</a>
                <a href="#" className="footer-link">Press</a>
              </div>
              
              <div className="footer-link-group">
                <h4>Support</h4>
                <a href="#" className="footer-link">Help Center</a>
                <a href="#" className="footer-link">Contact</a>
                <a href="#" className="footer-link">Status</a>
                <a href="#" className="footer-link">Community</a>
              </div>
              
              <div className="footer-link-group">
                <h4>Legal</h4>
                <a href="#" className="footer-link">Privacy Policy</a>
                <a href="#" className="footer-link">Terms of Service</a>
                <a href="#" className="footer-link">Cookie Policy</a>
                <a href="#" className="footer-link">GDPR</a>
              </div>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; {new Date().getFullYear()} AdvisorAI. All rights reserved.</p>
            <div className="footer-social">
              <a href="#" className="social-link">
                <Mail className="social-icon" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
