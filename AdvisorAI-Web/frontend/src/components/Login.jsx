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
  ArrowRight,
  Shield,
} from "lucide-react";

import StaticHeader from "./StaticHeader";
import BenefitsSection from "./common/BenefitsSection";
import BottomSection from "./common/BottomSection";
import "./Login.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [currentFeature, setCurrentFeature] = useState(0);
  const { login, loadUserProfile } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Auto-rotate features
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % 3);
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
      console.log("✅ Backend login successful");

      // Step 4: Check email verification status FIRST (before loading profile)
      console.log("📧 Checking email verification status...");
      if (backendResponse.verification_required || !result.user.emailVerified) {
        console.log("🔐 Email verification required, redirecting to verification page...");
        navigate('/email-verification');
        return; // CRITICAL: Return here, don't continue to profile loading
      }

      // Step 5: Load user profile and navigate based on completion status
      console.log("🔍 Loading user profile...");
      const profile = await loadUserProfile();
      console.log("✅ User profile loaded:", profile);

      if (profile && profile.profileCompleted) {
        console.log("📊 Profile complete, navigating to chat...");
        navigate("/chat");
      } else {
        console.log(
          "📊 Profile not complete or failed to load, navigating to profile completion..."
        );
        navigate("/profile-completion");
      }
    } catch (error) {
      console.error("❌ Login error:", error);

      // Handle specific Firebase errors
      if (error.code === "auth/user-not-found") {
        setError("No account found with this email address.");
      } else if (error.code === "auth/wrong-password") {
        setError("Incorrect password.");
      } else if (error.code === "auth/invalid-email") {
        setError("Invalid email address.");
      } else if (error.code === "auth/too-many-requests") {
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



  return (
    <div className="login-container">
      {/* Header Section */}
      <StaticHeader showSignIn={false} showSignUp={true} />
      
      {/* Main Content */}
      <div className="login-content">
        {/* Top Section - Login Form and Features Side by Side */}
        <div className="top-section">
          {/* Left Side - Form */}
          <div className="form-section">
            <div className="form-container">
              <form className="signup-form" onSubmit={handleSubmit}>
                <div className="form-field">
                  <label className="field-label">Email</label>
                  <input
                    className="field-input"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    autoComplete="email"
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
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      autoComplete="current-password"
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

                <div style={{ textAlign: "right", marginTop: "-0.5rem" }}>
                  <Link
                    to="/forgot-password"
                    style={{
                      color: "#3b82f6",
                      fontSize: "0.85rem",
                      textDecoration: "none",
                      fontWeight: 500,
                    }}
                  >
                    Forgot password?
                  </Link>
                </div>

                {error && (
                  <div className="error-message">
                    <X className="error-icon" />
                    <span>{error}</span>
                  </div>
                )}

                <button className="submit-button" type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <div className="button-spinner" />
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
                  <Shield className="footer-logo-icon" />
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

export default Login;
