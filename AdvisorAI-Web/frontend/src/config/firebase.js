import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Your Firebase configuration
// Replace these values with your actual Firebase project config
const firebaseConfig = {
    apiKey: "AIzaSyDS3ScFH_xgcA3SDon2TO0eqeqS_ncHVp0",
    authDomain: "advisorai-62611.firebaseapp.com",
    databaseURL: "https://advisorai-62611-default-rtdb.firebaseio.com",
    projectId: "advisorai-62611",
    storageBucket: "advisorai-62611.firebasestorage.app",
    messagingSenderId: "1047823455391",
    appId: "1:1047823455391:web:62a96688181a90cc243eaa",
    measurementId: "G-RXYRX9GG2T"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Cloud Firestore and get a reference to the service
export const db = getFirestore(app);

export default app; 