import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";
import { 
  User, 
  Mail, 
  Lock, 
  CheckCircle, 
  X, 
  Eye, 
  EyeOff, 
  Brain,
  Sparkles,
  ArrowRight,
  Shield,
  Zap,
  Star,
  Key,
  Clock,
  Users
} from "lucide-react";
import "./Login.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [currentFeature, setCurrentFeature] = useState(0);
  const { login, isProfileCompleted } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Auto-rotate features
    const interval = setInterval(() => {
      setCurrentFeature(prev => (prev + 1) % 3);
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      console.log("🚀 Starting login process...");

      // Step 1: Sign in with Firebase
      console.log("🔥 Signing in with Firebase...");
      const result = await login(email, password);
      console.log("✅ Firebase login successful:", result.user.uid);
      
      // Step 2: Get the ID token
      console.log("🎫 Getting ID token...");
      const idToken = await result.user.getIdToken();
      console.log("✅ ID token received");
      
      // Step 3: Sign in with backend
      console.log("🔗 Signing in with backend...");
      const backendResponse = await apiService.signinWithBackend(idToken);
      console.log("✅ Backend login successful:", backendResponse);
      
      // Step 4: Store the backend token
      localStorage.setItem('backendToken', backendResponse.access_token);
      console.log("💾 Token stored in localStorage");
      
      // Step 5: Check if user has completed profile
      console.log("🔍 Checking user profile status...");
      const profileCompleted = isProfileCompleted();
      console.log("📊 Profile completed:", profileCompleted);
      
      if (profileCompleted) {
        console.log("🎯 Redirecting to dashboard...");
        navigate('/dashboard');
      } else {
        console.log("🎯 Redirecting to profile completion...");
        navigate('/profile-completion');
      }
      
    } catch (error) {
      console.error('❌ Login error:', error);
      
      // Handle specific Firebase errors
      if (error.code === 'auth/user-not-found') {
        setError("No account found with this email address.");
      } else if (error.code === 'auth/wrong-password') {
        setError("Incorrect password.");
      } else if (error.code === 'auth/invalid-email') {
        setError("Invalid email address.");
      } else if (error.code === 'auth/too-many-requests') {
        setError("Too many failed attempts. Please try again later.");
      } else if (error.message) {
        setError(`Login failed: ${error.message}`);
      } else {
        setError("Failed to log in. Please check your credentials.");
      }
    } finally {
      setLoading(false);
      console.log("🏁 Login process completed");
    }
  };

  const features = [
    {
      icon: <Brain className="feature-icon" />,
      title: "AI-Powered Insights",
      description: "Get personalized academic guidance from advanced AI algorithms"
    },
    {
      icon: <Zap className="feature-icon" />,
      title: "Instant Access",
      description: "Quick and secure access to your academic dashboard"
    },
    {
      icon: <Shield className="feature-icon" />,
      title: "Secure & Private",
      description: "Your data is protected with enterprise-grade security"
    }
  ];

  const testimonials = [
    {
      text: "AdvisorAI helped me choose the perfect courses for my career goals!",
      author: "Sarah M.",
      role: "Computer Science Student"
    },
    {
      text: "The AI recommendations are incredibly accurate and personalized.",
      author: "Michael R.",
      role: "Engineering Student"
    },
    {
      text: "Finally, an AI that understands academic planning!",
      author: "Emma L.",
      role: "Business Student"
    }
  ];

  return (
    <div className="login-container">
      {/* Animated Background */}
      <div className="animated-background">
        <div className="floating-particles">
          {[...Array(15)].map((_, i) => (
            <div
              key={i}
              className="particle"
              style={{
                '--delay': `${Math.random() * 3}s`,
                '--duration': `${2 + Math.random() * 3}s`,
                '--x': `${Math.random() * 100}%`,
                '--y': `${Math.random() * 100}%`
              }}
            />
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="login-content">
        {/* Left Side - Form */}
        <div className="form-section">
          <div className="form-container">
            <div className="form-header">
              <div className="logo-container">
                <Brain className="logo-icon" />
                <span className="logo-text">Advisor<span className="logo-highlight">AI</span></span>
              </div>
              
              <div className="welcome-text">
                <div className="welcome-badge">
                  <Sparkles className="badge-icon" />
                  <span>Welcome Back!</span>
                </div>
                
                <h1 className="welcome-title">
                  Sign In to Your Account
                </h1>
                
                <p className="welcome-description">
                  Continue your academic journey with AI-powered guidance. 
                  Access your personalized dashboard and recommendations.
                </p>
              </div>
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">
                  <Mail className="label-icon" />
                  Email Address
                </label>
                <input
                  className="form-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  autoComplete="email"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <Lock className="label-icon" />
                  Password
                </label>
                <div className="password-input-container">
                  <input
                    className="form-input password-input"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? <EyeOff className="toggle-icon" /> : <Eye className="toggle-icon" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <X className="error-icon" />
                  <span>{error}</span>
                </div>
              )}

              <button className="login-button" type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <div className="loading-spinner" />
                    Signing In...
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="button-icon" />
                  </>
                )}
              </button>

              <div className="form-footer">
                <p className="signup-prompt">
                  Don't have an account? 
                  <Link to="/signup" className="signup-link">
                    Create Account
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </div>

        {/* Right Side - Features & Testimonials */}
        <div className="features-section">
          <div className="features-container">
            <div className="features-header">
              <h2 className="features-title">Why Students Love AdvisorAI</h2>
              <p className="features-subtitle">
                Join thousands of students making smarter academic decisions
              </p>
            </div>

            <div className="features-showcase">
              {features.map((feature, index) => (
                <div key={index} className={`feature-card ${currentFeature === index ? 'active' : ''}`}>
                  <div className="feature-icon-container">
                    {feature.icon}
                  </div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">{feature.description}</p>
                </div>
              ))}
            </div>

            <div className="testimonials-section">
              <h3 className="testimonials-title">What Our Users Say</h3>
              <div className="testimonials-list">
                {testimonials.map((testimonial, index) => (
                  <div key={index} className="testimonial-item">
                    <div className="testimonial-content">
                      <p className="testimonial-text">"{testimonial.text}"</p>
                      <div className="testimonial-author">
                        <span className="author-name">{testimonial.author}</span>
                        <span className="author-role">{testimonial.role}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="stats-preview">
              <div className="stat-item">
                <div className="stat-number">10K+</div>
                <div className="stat-label">Active Users</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">95%</div>
                <div className="stat-label">Satisfaction</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">24/7</div>
                <div className="stat-label">AI Support</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
