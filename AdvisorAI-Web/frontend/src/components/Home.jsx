import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { 
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
  ChevronRight,
  MessageCircle,
  Briefcase,
  History,
  Search,
  BarChart3,
  Database,
  FileText
} from "lucide-react";
import StaticHeader from "./StaticHeader";
import logo from "../utils/logo.png";
import "./Home.css";

const Home = () => {
  const [isVisible, setIsVisible] = useState(false);
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: MessageCircle,
      title: "AI-Powered Chat Assistant",
      description: "Get instant answers about Stevens courses, professors, admissions, and campus life. Our AI understands context and provides personalized guidance.",
      color: "blue"
    },
    {
      icon: BookOpen,
      title: "Course Explorer",
      description: "Browse and search through Stevens Institute of Technology's comprehensive course catalog. Find courses by department, prerequisites, and more.",
      color: "green"
    },
    {
      icon: Briefcase,
      title: "Job Search",
      description: "Discover full-time job opportunities tailored for Stevens students and alumni. Filter by location, industry, and experience level.",
      color: "purple"
    },
    {
      icon: GraduationCap,
      title: "Internship Search",
      description: "Find internship opportunities perfect for Stevens students. Connect with companies looking for your skills and expertise.",
      color: "teal"
    },
    {
      icon: History,
      title: "Chat History",
      description: "Access your complete conversation history. Review past questions, answers, and continue previous discussions seamlessly.",
      color: "gray"
    },
    {
      icon: TrendingUp,
      title: "Analytics Dashboard",
      description: "Track your academic journey with detailed analytics. Monitor your questions, tool usage, topic interests, and engagement patterns.",
      color: "indigo"
    },
    {
      icon: Database,
      title: "Stevens Knowledge Base",
      description: "Access comprehensive information about Stevens Institute of Technology including faculty profiles, research areas, and academic programs.",
      color: "orange"
    },
    {
      icon: Search,
      title: "Web Search Integration",
      description: "Get real-time information from Stevens' official website and other trusted sources. Always up-to-date with the latest information.",
      color: "pink"
    },
    {
      icon: User,
      title: "Personal Profile",
      description: "Create and manage your academic profile. Store your resume, skills, and preferences for personalized recommendations.",
      color: "cyan"
    },
    {
      icon: FileText,
      title: "Portfolio Builder",
      description: "Build and share your professional portfolio. Showcase your projects, achievements, and skills to potential employers.",
      color: "amber"
    }
  ];

  return (
    <div className="home-container">
      {/* Header Section */}
      <StaticHeader 
        showSignIn={!currentUser} 
        showSignUp={!currentUser} 
        currentUser={currentUser}
        onLogout={logout}
      />

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles className="badge-icon" />
            <span>
              {currentUser ? 'Welcome back to AdvisorAI!' : 'Stevens Institute of Technology'}
            </span>
          </div>
          
          <h1 className="hero-title">
            {currentUser ? (
              <>
                Welcome back, <span className="title-highlight">{currentUser.displayName || currentUser.email?.split('@')[0] || 'Stevens Student'}!</span>
                <br />
                Ready to continue your Stevens journey?
              </>
            ) : (
              <>
                Your Personal
                <span className="title-highlight"> Stevens Academic Advisor</span>
                <br />
                Powered by AI
              </>
            )}
          </h1>
          
          <p className="hero-description">
            {currentUser ? (
              'Access your personalized dashboard, explore Stevens courses, search for jobs and internships, or chat with our AI advisor for instant guidance.'
            ) : (
              'Get personalized academic guidance specifically for Stevens Institute of Technology. Ask questions about courses, professors, admissions, campus life, and career opportunities. Our AI-powered advisor has access to comprehensive Stevens information and provides expert advice tailored to your needs.'
            )}
          </p>
          
          <div className="hero-actions">
            {currentUser ? (
              <>
                <NavLink to="/chat" className="primary-button">
                  <MessageCircle className="button-icon" />
                  Start Chatting
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
                  Get Started Free
                </NavLink>
                <NavLink to="/login" className="secondary-button">
                  <User className="button-icon" />
                  Sign In
                </NavLink>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" style={{ padding: '6rem 0', background: 'linear-gradient(to bottom, #f8fafc, #ffffff)' }}>
        <div className="how-it-works-container" style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 2rem' }}>
          <div className="section-header" style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div className="section-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', borderRadius: '9999px', color: 'white', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>
              <Zap className="badge-icon" style={{ width: '1rem', height: '1rem' }} />
              <span>Complete Feature Set</span>
            </div>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '1rem' }}>
              Everything You Need for Your Stevens Journey
            </h2>
            <p className="section-subtitle" style={{ fontSize: '1.125rem', color: '#64748b', maxWidth: '600px', margin: '0 auto' }}>
              Discover all the powerful features designed specifically for Stevens Institute of Technology students
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', 
            gap: '2rem',
            marginTop: '3rem'
          }}>
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const colorMap = {
                blue: ['#3b82f6', '#06b6d4'],
                green: ['#10b981', '#059669'],
                purple: ['#8b5cf6', '#ec4899'],
                teal: ['#14b8a6', '#06b6d4'],
                gray: ['#6b7280', '#475569'],
                indigo: ['#6366f1', '#8b5cf6'],
                orange: ['#f97316', '#ef4444'],
                pink: ['#ec4899', '#f43f5e'],
                cyan: ['#06b6d4', '#3b82f6'],
                amber: ['#f59e0b', '#f97316']
              };
              
              const gradientColors = colorMap[feature.color] || colorMap.blue;
              
              return (
                <div 
                  key={index}
                  style={{
                    background: 'white',
                    borderRadius: '1.5rem',
                    padding: '2rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                    border: '1px solid #e2e8f0',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
                  }}
                >
                  <div style={{
                    width: '3.5rem',
                    height: '3.5rem',
                    borderRadius: '1rem',
                    background: `linear-gradient(135deg, ${gradientColors[0]}, ${gradientColors[1]})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}>
                    <Icon style={{ width: '1.75rem', height: '1.75rem', color: 'white' }} />
                  </div>
                  <h3 style={{ 
                    fontSize: '1.25rem', 
                    fontWeight: '700', 
                    color: '#1e293b', 
                    marginBottom: '0.75rem' 
                  }}>
                    {feature.title}
                  </h3>
                  <p style={{ 
                    fontSize: '0.9375rem', 
                    color: '#64748b', 
                    lineHeight: '1.6' 
                  }}>
                    {feature.description}
                  </p>
                </div>
              );
            })}
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
            <p className="section-subtitle">Get started in just three simple steps and begin your Stevens academic journey</p>
          </div>
          
          <div className="steps-container">
            <div className="step-item">
              <div className="step-number">01</div>
              <div className="step-content">
                <h3 className="step-title">Create Your Profile</h3>
                <p className="step-description">Sign up and complete your profile with your academic background, interests, and career goals to get personalized Stevens-specific recommendations.</p>
              </div>
            </div>
            
            <div className="step-item">
              <div className="step-number">02</div>
              <div className="step-content">
                <h3 className="step-title">Chat with AI Advisor</h3>
                <p className="step-description">Ask questions about Stevens courses, professors, admissions, campus resources, or career opportunities. Get instant, accurate answers powered by Stevens' knowledge base.</p>
              </div>
            </div>
            
            <div className="step-item">
              <div className="step-number">03</div>
              <div className="step-content">
                <h3 className="step-title">Explore & Achieve</h3>
                <p className="step-description">Use our course explorer, job search, internship finder, and analytics dashboard to make informed decisions and track your progress at Stevens.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Stevens Section */}
      <section style={{ 
        padding: '6rem 0', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 2rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
              Why Choose AdvisorAI for Stevens?
            </h2>
            <p style={{ fontSize: '1.125rem', opacity: 0.9, maxWidth: '700px', margin: '0 auto' }}>
              Built specifically for Stevens Institute of Technology students with comprehensive knowledge of courses, faculty, and campus resources
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
            gap: '2rem',
            marginTop: '3rem'
          }}>
            {[
              {
                icon: Database,
                title: 'Stevens Knowledge Base',
                description: 'Access to comprehensive Stevens information including faculty profiles, course catalogs, and research areas'
              },
              {
                icon: Search,
                title: 'Real-Time Web Search',
                description: 'Get the latest information directly from Stevens official website and trusted sources'
              },
              {
                icon: MessageCircle,
                title: 'Context-Aware AI',
                description: 'Our AI remembers your conversation history and provides personalized guidance based on your profile'
              },
              {
                icon: Award,
                title: 'Quality Assured',
                description: 'Every answer is reviewed and refined to ensure accuracy and relevance to Stevens students'
              }
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <div key={index} style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '1.5rem',
                  padding: '2rem',
                  border: '1px solid rgba(255, 255, 255, 0.2)'
                }}>
                  <div style={{
                    width: '3rem',
                    height: '3rem',
                    borderRadius: '0.75rem',
                    background: 'rgba(255, 255, 255, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1.5rem'
                  }}>
                    <Icon style={{ width: '1.5rem', height: '1.5rem' }} />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.75rem' }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: '0.9375rem', opacity: 0.9, lineHeight: '1.6' }}>
                    {item.description}
                  </p>
                </div>
              );
            })}
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
              {currentUser ? 'Ready to Explore More Stevens Resources?' : 'Ready to Transform Your Stevens Experience?'}
            </h2>
            <p className="cta-description">
              {currentUser ? 
                'Discover courses, search for jobs and internships, track your progress, and get personalized AI guidance for your Stevens journey.' :
                'Join Stevens students who are making smarter academic decisions with AI-powered guidance tailored specifically for Stevens Institute of Technology.'
              }
            </p>
            {currentUser ? (
              <NavLink to="/chat" className="cta-button">
                <MessageCircle className="button-icon" />
                Start Chatting Now
              </NavLink>
            ) : (
              <NavLink to="/signup" className="cta-button">
                <Play className="button-icon" />
                Get Started Free
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
                  <img src={logo} alt="AdvisorAI Logo" className="footer-logo-icon" style={{ width: '1.5rem', height: '1.5rem', objectFit: 'contain' }} />
                </div>
                <span>AdvisorAI</span>
              </div>
              <p className="footer-text">
                Empowering Stevens Institute of Technology students with AI-driven academic guidance. Get personalized advice about courses, professors, admissions, and career opportunities.
              </p>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; {new Date().getFullYear()} AdvisorAI for Stevens Institute of Technology. All rights reserved.</p>
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
