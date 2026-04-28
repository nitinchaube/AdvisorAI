import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { sendEmailVerification, applyActionCode } from 'firebase/auth';
import { auth } from '../config/firebase';
import { apiService } from '../services/api';
import {
  VERIFY_EMAIL_COOLDOWN_SECONDS,
  startVerifyEmailCooldown,
  getRemainingVerifyEmailCooldown,
  clearVerifyEmailCooldown,
} from '../utils/verifyEmailCooldown';
import './EmailVerification.css';

const EmailVerification = () => {
  const { 
    currentUser, 
    loading,
    logout
  } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isResending, setIsResending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef(null);

  // Restore cooldown from localStorage on mount.
  // This also covers the "first send happened during signup" case:
  // AuthContext.signup() writes the same key after sending the
  // initial verification email, so the timer is already running
  // by the time this page renders.
  useEffect(() => {
    const remaining = getRemainingVerifyEmailCooldown();
    if (remaining > 0) {
      setCooldown(remaining);
    }
  }, []);

  // Countdown timer
  useEffect(() => {
    if (cooldown > 0) {
      cooldownRef.current = setInterval(() => {
        setCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(cooldownRef.current);
            clearVerifyEmailCooldown();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (cooldownRef.current) clearInterval(cooldownRef.current);
    };
  }, [cooldown]);

  // Check if user came from email verification link
  useEffect(() => {
    const mode = searchParams.get('mode');
    const oobCode = searchParams.get('oobCode');
    
    if (mode === 'verifyEmail' && oobCode && currentUser) {
      handleEmailVerification(oobCode);
    }
  }, [searchParams, currentUser]);

  useEffect(() => {
    if (currentUser && !loading) {
      // Check if email is already verified
      if (currentUser.emailVerified) {
        setEmailVerified(true);
        navigate('/chat');
      }
    }
  }, [currentUser, loading, navigate]);

  useEffect(() => {
    if (emailVerified) {
      // If email is verified, redirect to chat
      navigate('/chat');
    }
  }, [emailVerified, navigate]);

  const handleEmailVerification = async (oobCode) => {
    try {
      setMessage('Verifying email...');
      
      // Apply the verification code
      await applyActionCode(auth, oobCode);
      
      // Verify with backend (to update MongoDB status)
      const idToken = await currentUser.getIdToken();
      const response = await apiService.verifyEmail(idToken);
      
      if (response.emailVerified) {
        setMessage('Email verified successfully! Redirecting...');
        setTimeout(() => navigate('/chat'), 2000);
      }
    } catch (error) {
      console.error('Email verification error:', error);
      
      // Handle specific Firebase errors
      if (error.code === 'auth/expired-action-code') {
        setError('The verification link has expired. Please request a new one.');
      } else if (error.code === 'auth/invalid-action-code') {
        setError('The verification link is invalid or has already been used. Please request a new one.');
      } else if (error.code === 'auth/user-disabled') {
        setError('This account has been disabled. Please contact support.');
      } else {
        setError('Failed to verify email. Please try again.');
      }
    }
  };

  const handleResendVerification = async () => {
    if (cooldown > 0) return; // Safety guard

    try {
      setIsResending(true);
      setError('');
      setMessage('');
      
      if (currentUser) {
        // Send verification email using Firebase's new method
        await sendEmailVerification(currentUser, {
          url: window.location.origin + '/email-verification'
        });
        setMessage('Verification email sent! Please check your inbox.');

        startVerifyEmailCooldown();
        setCooldown(VERIFY_EMAIL_COOLDOWN_SECONDS);
      } else {
        setError('No user found. Please try logging in again.');
      }
    } catch (error) {
      console.error('Error sending verification email:', error);
      if (error.code === 'auth/too-many-requests') {
        setError('Too many requests. Please wait before requesting another verification email.');
      } else {
        setError(error.message || 'Failed to send verification email');
      }
    } finally {
      setIsResending(false);
    }
  };

  const handleCheckVerification = async () => {
    try {
      setError('');
      setMessage('');
      
      if (currentUser) {
        // Reload user to get latest verification status
        await currentUser.reload();
        
        if (currentUser.emailVerified) {
          // Verify with backend
          const idToken = await currentUser.getIdToken();
          const response = await apiService.verifyEmail(idToken);
          
          if (response.emailVerified) {
            setEmailVerified(true);
            setMessage('Email verified successfully! Redirecting...');
            setTimeout(() => navigate('/chat'), 2000);
          }
        } else {
          setMessage('Email not yet verified. Please check your email and click the verification link.');
        }
      }
    } catch (error) {
      console.error('Error checking verification:', error);
      setError(error.message || 'Failed to check verification status');
    }
  };

  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const formatCooldown = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${s}s`;
  };

  if (loading) {
    return (
      <div className="email-verification-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!currentUser) {
    navigate('/login');
    return null;
  }

  const isButtonDisabled = isResending || cooldown > 0;

  return (
    <div className="email-verification-container">
      <div className="email-verification-card">
        <div className="verification-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="#3B82F6"/>
          </svg>
        </div>
        
        <h1>Verify Your Email</h1>
        <p className="verification-text">
          We've sent a verification link to <strong>{currentUser.email}</strong>
        </p>
        <p className="verification-subtext">
          Please check your email and click the verification link to activate your account.
        </p>

        {message && (
          <div className={`message ${message.includes('successfully') ? 'success' : 'info'}`}>
            {message}
          </div>
        )}

        {error && (
          <div className="message error">
            {error}
          </div>
        )}

        <div className="verification-actions">
          <button 
            onClick={handleResendVerification}
            disabled={isButtonDisabled}
            className="resend-button"
            style={isButtonDisabled ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
          >
            {isResending
              ? 'Sending...'
              : cooldown > 0
              ? `Resend in ${formatCooldown(cooldown)}`
              : 'Resend Verification Email'}
          </button>
          
          <button 
            onClick={handleCheckVerification}
            className="check-button"
          >
            I've Verified My Email
          </button>
        </div>

        <div className="verification-help">
          <p>Didn't receive the email?</p>
          <ul>
            <li>Check your spam/junk folder</li>
            <li>Make sure the email address is correct</li>
            <li>Wait a few minutes for the email to arrive</li>
          </ul>
        </div>

        <button 
          onClick={handleSignOut}
          className="signout-button"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default EmailVerification;
