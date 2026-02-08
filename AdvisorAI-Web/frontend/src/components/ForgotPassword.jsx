import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Mail, ArrowLeft, X, CheckCircle, Shield } from "lucide-react";
import StaticHeader from "./StaticHeader";
import "./Login.css";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const { resetPassword } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setMessage("");
      await resetPassword(email);
      setMessage(
        "Password reset email sent! Check your inbox and follow the link to reset your password."
      );
    } catch (error) {
      console.error("Password reset error:", error);
      if (error.code === "auth/user-not-found") {
        setError("No account found with this email address.");
      } else if (error.code === "auth/invalid-email") {
        setError("Invalid email address.");
      } else if (error.code === "auth/too-many-requests") {
        setError("Too many requests. Please try again later.");
      } else {
        setError("Failed to send password reset email. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <StaticHeader showSignIn={true} showSignUp={true} />

      <div className="login-content">
        <div className="top-section" style={{ justifyItems: "center" }}>
          <div className="form-section">
            <div className="form-container">
              <form className="signup-form" onSubmit={handleSubmit}>
                <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem" }}>
                  Reset Your Password
                </h2>
                <p style={{ color: "#6b7280", fontSize: "0.9rem", marginBottom: "1rem", lineHeight: 1.5 }}>
                  Enter the email address associated with your account and we'll send you a link to reset your password.
                </p>

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

                {error && (
                  <div className="error-message">
                    <X className="error-icon" />
                    <span>{error}</span>
                  </div>
                )}

                {message && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      padding: "0.75rem 1rem",
                      borderRadius: "8px",
                      fontSize: "0.875rem",
                      fontWeight: 500,
                      background: "#f0fdf4",
                      border: "1px solid #bbf7d0",
                      color: "#16a34a",
                    }}
                  >
                    <CheckCircle style={{ width: "1.25rem", height: "1.25rem", flexShrink: 0 }} />
                    <span>{message}</span>
                  </div>
                )}

                <button className="submit-button" type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <div className="button-spinner" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail style={{ width: "1.25rem", height: "1.25rem" }} />
                      <span>Send Reset Link</span>
                    </>
                  )}
                </button>

                <div className="form-footer">
                  <p className="signup-prompt">
                    Remember your password?
                    <Link to="/login" className="signup-link">
                      Back to Login
                    </Link>
                  </p>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;