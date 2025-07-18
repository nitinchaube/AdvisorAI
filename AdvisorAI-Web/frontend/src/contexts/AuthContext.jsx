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

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
    console.log('AuthContext: Profile marked as completed');
  }

  // Check if profile is completed
  function isProfileCompleted() {
    const localStorageStatus = localStorage.getItem('profileCompleted') === 'true';
    const userStatus = currentUser?.profileCompleted;
    
    // If either localStorage or user state indicates completion, return true
    const isCompleted = localStorageStatus || userStatus;
    console.log('AuthContext: Profile completion check - localStorage:', localStorageStatus, 'userState:', userStatus, 'final:', isCompleted);
    
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

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('AuthContext: Auth state changed:', user ? user.uid : 'No user');
      
      if (user) {
        try {
          // First, try to authenticate with backend
          const idToken = await user.getIdToken();
          console.log('AuthContext: Got ID token, authenticating with backend...');
          const backendResponse = await apiService.signinWithBackend(idToken);
          console.log('AuthContext: Backend authentication successful');
          
          // Store the backend JWT token
          if (backendResponse.access_token) {
            localStorage.setItem('backendToken', backendResponse.access_token);
            console.log('AuthContext: Backend token stored');
            // Small delay to ensure token is saved
            await new Promise(resolve => setTimeout(resolve, 100));
          }
          
          // Check if user has profile data in backend
          let profileCompleted = false;
          try {
            console.log('AuthContext: Checking for profile data in backend...');
            const profileResponse = await apiService.getUserProfile();
            console.log('AuthContext: Profile response:', profileResponse);
            
            if (profileResponse.success && profileResponse.profile && Object.keys(profileResponse.profile).length > 0) {
              profileCompleted = true;
              console.log('AuthContext: Profile data found, marking as completed');
              // Update localStorage to reflect the actual status
              localStorage.setItem('profileCompleted', 'true');
            } else {
              console.log('AuthContext: No profile data found in backend');
              // Check localStorage as fallback
              const localStorageStatus = localStorage.getItem('profileCompleted');
              if (localStorageStatus === 'true') {
                profileCompleted = true;
                console.log('AuthContext: Using localStorage status (true)');
              } else {
                profileCompleted = false;
                localStorage.setItem('profileCompleted', 'false');
              }
            }
          } catch (profileError) {
            console.log('AuthContext: Error checking profile data:', profileError);
            // Check localStorage as fallback
            const localStorageStatus = localStorage.getItem('profileCompleted');
            if (localStorageStatus === 'true') {
              profileCompleted = true;
              console.log('AuthContext: Using localStorage fallback (true)');
            } else {
              profileCompleted = false;
              localStorage.setItem('profileCompleted', 'false');
            }
          }
          
          console.log('AuthContext: Final profile completion status:', profileCompleted);
          setCurrentUser({
            ...user,
            profileCompleted
          });
        } catch (error) {
          console.error('AuthContext: Backend authentication failed:', error);
          // Fallback to localStorage check
          const profileCompleted = localStorage.getItem('profileCompleted') === 'true';
          console.log('AuthContext: Using localStorage fallback, profile completed:', profileCompleted);
          setCurrentUser({
            ...user,
            profileCompleted
          });
        }
      } else {
        setCurrentUser(null);
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    signup,
    login,
    logout,
    getIdToken,
    markProfileCompleted,
    isProfileCompleted,
    error,
    setError,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
} 