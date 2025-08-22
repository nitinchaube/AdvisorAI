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

  // Sign up function
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

  // Logout function
  async function logout() {
    try {
      // Clear user profile state
      setUserProfile(null);
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

  // Load user profile from backend
  const loadUserProfile = useCallback(async () => {
    // No need to check for currentUser here, as this is checked in the useEffect
    console.log("AuthContext: Firing loadUserProfile");
    try {
      const response = await apiService.getUserProfile();
      if (response.success && response.profile) {
        setUserProfile(response.profile);
        console.log("AuthContext: User profile loaded:", response.profile);
        return response.profile;
      }
      // If the profile is empty or request fails, set it to a default state
      setUserProfile({ profileCompleted: false });
      return null;
    } catch (error) {
      console.error("AuthContext: Error loading user profile:", error);
      // Set a default state on error to avoid blocking rendering
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
    signup,
    login,
    logout,
    getIdToken,
    markProfileCompleted,
    isProfileCompleted,
    loadUserProfile,
    error,
    setError,
    loading,
    isAdmin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
