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
  Star
} from "lucide-react";
import "./Signup.css";

const Signup = () => {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const { signup } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Auto-advance steps for demo effect
    if (currentStep < 2) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.name || !form.email || !form.password || !form.confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");
      console.log("🚀 Starting signup process...");

      // Step 1: Sign up with Firebase only
      console.log("🔥 Creating Firebase account...");
      const result = await signup(form.email, form.password, form.name);
      console.log("✅ Firebase account created:", result.user.uid);
      
      // Step 2: Get the ID token
      console.log("🎫 Getting ID token...");
      const idToken = await result.user.getIdToken();
      console.log("✅ ID token received");
      
      // Step 3: Sign in with backend to get JWT token
      console.log("🔗 Signing in with backend...");
      const backendResponse = await apiService.signinWithBackend(idToken);
      console.log("✅ Backend signin successful:", backendResponse);
      
      // Step 4: Store the backend token
      localStorage.setItem('backendToken', backendResponse.access_token);
      console.log("💾 Backend token stored");
      
      setSuccess("Account created successfully! Redirecting to profile completion...");
      console.log("🎉 Signup completed successfully");
      
      // Redirect to profile completion after a short delay
      setTimeout(() => {
        navigate('/profile-completion');
      }, 2000);
      
    } catch (error) {
      console.error('❌ Signup error:', error);
      
      // Handle specific Firebase errors
      if (error.code === 'auth/email-already-in-use') {
        setError("An account with this email already exists.");
      } else if (error.code === 'auth/invalid-email') {
        setError("Invalid email address.");
      } else if (error.code === 'auth/weak-password') {
        setError("Password is too weak. Please choose a stronger password.");
      } else if (error.message) {
        setError(`Failed to create account: ${error.message}`);
      } else {
        setError("Failed to create account. Please try again.");
      }
    } finally {
      setLoading(false);
      console.log("🏁 Signup process completed");
    }
  };

  const benefits = [
    {
      icon: <Brain className="benefit-icon" />,
      title: "AI-Powered Guidance",
      description: "Get personalized academic advice from advanced AI"
    },
    {
      icon: <Zap className="benefit-icon" />,
      title: "Instant Answers",
      description: "Quick responses to all your academic questions"
    },
    {
      icon: <Shield className="benefit-icon" />,
      title: "Secure & Private",
      description: "Your data is protected with enterprise-grade security"
    }
  ];

  return (
    <div className="signup-container">
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
      <div className="signup-content">
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
                  <span>Join the Future of Academic Guidance</span>
                </div>
                
                <h1 className="welcome-title">
                  Create Your Account
                </h1>
                
                <p className="welcome-description">
                  Start your journey with AI-powered academic guidance. 
                  Get personalized recommendations and expert advice.
                </p>
              </div>
            </div>

            <form className="signup-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">
                  <User className="label-icon" />
                  Full Name
                </label>
          <input
                  className="form-input"
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
                  placeholder="Enter your full name"
            autoComplete="off"
                  disabled={loading}
          />
        </div>

              <div className="form-group">
                <label className="form-label">
                  <Mail className="label-icon" />
                  Email Address
                </label>
          <input
                  className="form-input"
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="Enter your email"
            autoComplete="off"
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
            name="password"
            value={form.password}
            onChange={handleChange}
                    placeholder="Create a strong password"
            autoComplete="new-password"
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

              <div className="form-group">
                <label className="form-label">
                  <Lock className="label-icon" />
                  Confirm Password
                </label>
                <div className="password-input-container">
          <input
                    className="form-input password-input"
                    type={showConfirmPassword ? "text" : "password"}
            name="confirmPassword"
            value={form.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            autoComplete="new-password"
                    disabled={loading}
          />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    disabled={loading}
                  >
                    {showConfirmPassword ? <EyeOff className="toggle-icon" /> : <Eye className="toggle-icon" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <X className="error-icon" />
                  <span>{error}</span>
                </div>
              )}

              {success && (
                <div className="success-message">
                  <CheckCircle className="success-icon" />
                  <span>{success}</span>
                </div>
              )}

              <button className="signup-button" type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <div className="loading-spinner" />
                    Creating Account...
                  </>
                ) : (
                  <>
                    <span>Create Account</span>
                    <ArrowRight className="button-icon" />
                  </>
                )}
              </button>

              <div className="form-footer">
                <p className="login-prompt">
                  Already have an account? 
                  <Link to="/login" className="login-link">
                    Sign In
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </div>

        {/* Right Side - Benefits */}
        <div className="benefits-section">
          <div className="benefits-container">
            <div className="benefits-header">
              <h2 className="benefits-title">Why Choose AdvisorAI?</h2>
              <p className="benefits-subtitle">
                Join thousands of students making smarter academic decisions
              </p>
            </div>

            <div className="benefits-list">
              {benefits.map((benefit, index) => (
                <div key={index} className={`benefit-item ${currentStep === index ? 'active' : ''}`}>
                  <div className="benefit-icon-container">
                    {benefit.icon}
                  </div>
                  <div className="benefit-content">
                    <h3 className="benefit-title">{benefit.title}</h3>
                    <p className="benefit-description">{benefit.description}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="stats-preview">
              <div className="stat-item">
                <div className="stat-number">10K+</div>
                <div className="stat-label">Students</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">95%</div>
                <div className="stat-label">Satisfaction</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">24/7</div>
                <div className="stat-label">Support</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
