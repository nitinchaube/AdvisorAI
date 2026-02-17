import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile,
  sendEmailVerification,
  sendPasswordResetEmail,
} from "firebase/auth";
import { auth } from "../config/firebase";
import { apiService } from "../services/api";
import { chatCache } from "../utils/chatCache";

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [userProfile, setUserProfile] = useState(null);
  const [emailVerified, setEmailVerified] = useState(false);

  // Sign up function with email verification
  async function signup(email, password, displayName) {
    try {
      setError("");
      const result = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      );

      // Update profile with display name
      if (displayName) {
        await updateProfile(result.user, { displayName });
      }

      // Send email verification
      await sendEmailVerification(result.user);

      return result;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  }

  // Login function
  async function login(email, password) {
    try {
      setError("");
      console.log("AuthContext: Attempting Firebase login...");
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log("AuthContext: Firebase login successful");
      return result;
    } catch (error) {
      console.error("AuthContext: Firebase login error:", error);
      setError(error.message);
      throw error;
    }
  }

  // Forgot/ Reset password
  async function resetPassword(email) {
    try {
      setError("");
      await sendPasswordResetEmail(auth, email);
      return true;
    } catch (error) {
      console.error("AuthContext: Password reset error:", error);
      setError(error.message);
      throw error;
    }
  }
  

  // Send email verification
  async function sendVerificationEmail() {
    try {
      if (currentUser && !currentUser.emailVerified) {
        await sendEmailVerification(currentUser);
        return true;
      }
      return false;
    } catch (error) {
      console.error("AuthContext: Send verification email error:", error);
      setError(error.message);
      throw error;
    }
  }

  // Check email verification status
  async function checkEmailVerification() {
    try {
      if (currentUser) {
        // Reload user to get latest verification status
        await currentUser.reload();
        const verified = currentUser.emailVerified;
        setEmailVerified(verified);
        return verified;
      }
      return false;
    } catch (error) {
      console.error("AuthContext: Check email verification error:", error);
      return false;
    }
  }

  // Verify email with backend
  async function verifyEmailWithBackend() {
    try {
      if (currentUser) {
        const idToken = await currentUser.getIdToken();
        const response = await apiService.verifyEmail(idToken);
        if (response.emailVerified) {
          setEmailVerified(true);
          // Reload user profile to get updated verification status
          await loadUserProfile();
        }
        return response;
      }
      return { emailVerified: false };
    } catch (error) {
      console.error("AuthContext: Verify email with backend error:", error);
      throw error;
    }
  }

  // Check verification status from backend
  async function checkVerificationStatus() {
    try {
      const response = await apiService.checkVerificationStatus();
      setEmailVerified(response.emailVerified);
      return response;
    } catch (error) {
      console.error("AuthContext: Check verification status error:", error);
      return { emailVerified: false };
    }
  }

  // Logout function
  async function logout() {
    try {
      // Clear user profile state
      setUserProfile(null);
      setEmailVerified(false);
      // Clear backend token
      localStorage.removeItem("backendToken");
      // Clear chat cache
      chatCache.clearAll();
      // Sign out from Firebase
      await signOut(auth);
      console.log("AuthContext: Logout successful");
    } catch (error) {
      console.error("AuthContext: Logout error:", error);
      throw error;
    }
  }

  // Mark profile as completed by refetching from the backend
  async function markProfileCompleted() {
    console.log(
      "AuthContext: Marking profile as completed by refetching profile..."
    );
    await loadUserProfile();
  }

  // Check if profile is completed from the userProfile state
  function isProfileCompleted() {
    const isCompleted = userProfile?.profileCompleted === true;
    console.log(
      "AuthContext: Profile completion check from state - userProfile:",
      userProfile,
      "final:",
      isCompleted
    );
    return isCompleted;
  }

  // Check if email is verified
  function isEmailVerified() {
    return emailVerified || currentUser?.emailVerified || false;
  }

  // Load user profile from backend
  const loadUserProfile = useCallback(async () => {
    // No need to check for currentUser here, as this is checked in the useEffect
    console.log("AuthContext: Firing loadUserProfile");
    try {
      const response = await apiService.getUserProfile();
      if (response.success && response.profile) {
        setUserProfile(response.profile);
        setEmailVerified(response.profile.emailVerified || false);
        console.log("AuthContext: User profile loaded:", response.profile);
        return response.profile;
      }
      // If the profile is empty or request fails, set it to a default state
      setUserProfile({ profileCompleted: false });
      return null;
    } catch (error) {
      console.error("AuthContext: Error loading user profile:", error);
      // If it's a 404 (profile not found), that's okay for new users
      if (error.message.includes("404") || error.message.includes("not found")) {
        console.log("AuthContext: Profile not found, setting default state");
        setUserProfile({ profileCompleted: false });
        return null;
      }
      // For other errors, set a default state to avoid blocking rendering
      setUserProfile({ profileCompleted: false });
      return null;
    }
  }, []);

  // Get current user's ID token
  async function getIdToken() {
    if (currentUser) {
      return await currentUser.getIdToken();
    }
    return null;
  }

  function isAdmin() {
    return userProfile?.role === "admin";
  }

  useEffect(() => {

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('AuthContext: Auth state changed:', user ? user.uid : 'No user');

      if (user) {
        setCurrentUser(user);
        setEmailVerified(user.emailVerified);
        
        // Auto-get backend token if user is authenticated but no backend token exists
        const backendToken = localStorage.getItem('backendToken');
        if (!backendToken) {
          try {
            console.log('🔑 Auto-getting backend token for authenticated user...');
            const idToken = await user.getIdToken();
            const backendResponse = await apiService.signinWithBackend(idToken);
            localStorage.setItem('backendToken', backendResponse.access_token);
            console.log('✅ Backend token auto-retrieved and stored');
          } catch (error) {
            console.error('❌ Failed to auto-get backend token:', error);
          }
        }
      } else {
        // Clear all user-related state on logout
        setCurrentUser(null);
        setUserProfile(null);
        setEmailVerified(false);
        localStorage.removeItem("backendToken");
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  // Effect to load user profile when user is available
  useEffect(() => {
    const loadProfileIfNeeded = async () => {
      if (currentUser) {
        try {
          console.log("AuthContext: User detected, loading profile...");
          await loadUserProfile();
        } catch (error) {
          console.error("AuthContext: Failed to load user profile:", error);
        }
      }
    };

    loadProfileIfNeeded();
  }, [currentUser, loadUserProfile]);

  const value = {
    currentUser,
    userProfile,
    emailVerified,
    signup,
    login,
    logout,
    resetPassword,
    getIdToken,
    markProfileCompleted,
    isProfileCompleted,
    loadUserProfile,
    error,
    setError,
    loading,
    isAdmin,
    sendVerificationEmail,
    checkEmailVerification,
    verifyEmailWithBackend,
    checkVerificationStatus,
    isEmailVerified,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
