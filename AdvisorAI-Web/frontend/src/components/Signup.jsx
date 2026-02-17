import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";
import { 
  Mail, 
  Lock, 
  X, 
  Eye, 
  EyeOff,
  CheckCircle
} from "lucide-react";
import StaticHeader from "./StaticHeader";
import logo from "../utils/logo.png";
import BenefitsSection from "./common/BenefitsSection";
import BottomSection from "./common/BottomSection";

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
  const { signup } = useAuth();
  const navigate = useNavigate();

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
      
      // Step 5: Check if email verification is required
      if (backendResponse.verification_required) {
        setSuccess("Account created successfully! Please verify your email to continue.");
        console.log("📧 Email verification required, redirecting to verification page...");
        
        // Redirect to email verification after a short delay
        setTimeout(() => {
          navigate('/email-verification');
        }, 2000);
      } else {
        setSuccess("Account created successfully! Redirecting to profile completion...");
        console.log("🎉 Signup completed successfully");
        
        // Redirect to profile completion after a short delay
        setTimeout(() => {
          navigate('/profile-completion');
        }, 2000);
      }
      
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



  return (
    <div className="signup-container">
            {/* Header Section */}
      <StaticHeader showSignIn={true} showSignUp={false} />

      {/* Main Content */}
      <div className="signup-content">
        {/* Top Section - Signup Form and Why Choose Us Side by Side */}
        <div className="top-section">
          {/* Left Side - Form */}
          <div className="form-section">
          <div className="form-container">
            {/* <div className="form-header">
              <h1 className="welcome-title">
                Create Account
              </h1>
            </div> */}

            <form className="signup-form" onSubmit={handleSubmit}>
              <div className="form-field">
                <label className="field-label">Full Name</label>
                <input
                  className="field-input"
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="Enter your full name"
                  autoComplete="off"
                  disabled={loading}
                />
              </div>

              <div className="form-field">
                <label className="field-label">Email</label>
                <input
                  className="field-input"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                  autoComplete="off"
                  disabled={loading}
                />
              </div>

              <div className="form-field">
                <label className="field-label">
                  Password
                </label>
                <div className="password-field">
                  <input
                    className="field-input password-input"
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    placeholder="Create a password"
                    autoComplete="new-password"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="toggle-icon" /> : <Eye className="toggle-icon" />}
                  </button>
                </div>
              </div>

              <div className="form-field">
                <label className="field-label">Confirm Password</label>
                <div className="password-field">
                  <input
                    className="field-input password-input"
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    value={form.confirmPassword}
                    onChange={handleChange}
                    placeholder="Confirm password"
                    autoComplete="new-password"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    disabled={loading}
                    title={showConfirmPassword ? "Hide password" : "Show password"}
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

              <button className="submit-button" type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <div className="button-spinner" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <span>Create Account</span>
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

        {/* Right Side - Why Choose Us */}
        <BenefitsSection />
        </div>

        {/* Bottom Section - What You'll Get (Horizontal Layout) */}
        <BottomSection />
      </div>
      
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
                <Mail className="footer-social-icon" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Signup;
