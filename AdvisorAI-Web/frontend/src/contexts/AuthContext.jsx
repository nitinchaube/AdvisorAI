import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';
import { auth } from '../config/firebase';
import { apiService } from '../services/api';
import { chatCache } from '../utils/chatCache';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState(null);

  // Sign up function
  async function signup(email, password, displayName) {
    try {
      setError('');
      const result = await createUserWithEmailAndPassword(auth, email, password);
      
      // Update profile with display name
      if (displayName) {
        await updateProfile(result.user, { displayName });
      }
      
      // Set profile completion status to false for new users
      localStorage.setItem('profileCompleted', 'false');
      
      return result;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  }

  // Login function
  async function login(email, password) {
    try {
      setError('');
      console.log('AuthContext: Attempting Firebase login...');
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log('AuthContext: Firebase login successful');
      return result;
    } catch (error) {
      console.error('AuthContext: Firebase login error:', error);
      setError(error.message);
      throw error;
    }
  }

  // Logout function
  async function logout() {
    try {
      // Clear profile completion status on logout
      localStorage.removeItem('profileCompleted');
      // Clear backend token
      localStorage.removeItem('backendToken');
      // Clear chat cache
      chatCache.clearAll();
      // Sign out from Firebase
      await signOut(auth);
      console.log('AuthContext: Logout successful');
    } catch (error) {
      console.error('AuthContext: Logout error:', error);
      throw error;
    }
  }

  // Mark profile as completed
  function markProfileCompleted() {
    localStorage.setItem('profileCompleted', 'true');
    // Update current user state if available
    if (currentUser) {
      setCurrentUser(prev => ({
        ...prev,
        profileCompleted: true
      }));
    }
    // Update userProfile state if available
    if (userProfile) {
      setUserProfile(prev => ({
        ...prev,
        profileCompleted: true
      }));
    }
    console.log('AuthContext: Profile marked as completed');
  }

  // Check if profile is completed
  function isProfileCompleted() {
    const localStorageStatus = localStorage.getItem('profileCompleted') === 'true';
    const userStatus = currentUser?.profileCompleted;
    const userProfileStatus = userProfile?.profileCompleted === true;
    
    // If any source indicates completion, return true
    const isCompleted = localStorageStatus || userStatus || userProfileStatus;
    
    console.log('AuthContext: Profile completion check - localStorage:', localStorageStatus, 
                'userState:', userStatus, 'userProfile:', userProfileStatus, 'final:', isCompleted);
    
    return isCompleted;
  }

  // Check profile completion status from backend
  async function checkProfileCompletionFromBackend() {
    if (!currentUser) return false;
    
    try {
      const response = await apiService.getUserProfile();
      if (response.success && response.profile && Object.keys(response.profile).length > 0) {
        markProfileCompleted();
        return true;
      }
      return false;
    } catch (error) {
      console.error('AuthContext: Error checking profile completion from backend:', error);
      return false;
    }
  }

  // Get current user's ID token
  async function getIdToken() {
    if (currentUser) {
      return await currentUser.getIdToken();
    }
    return null;
  }

  function isAdmin() {
    return userProfile?.role === 'admin';
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
        setCurrentUser(null);
        setUserProfile(null);
        localStorage.removeItem('profileCompleted');
        localStorage.removeItem('backendToken');
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    userProfile,
    signup,
    login,
    logout,
    getIdToken,
    markProfileCompleted,
    isProfileCompleted,
    error,
    setError,
    loading,
    isAdmin
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
} 