// Chat cache utility for browser-side chat history caching
// Uses localStorage for simplicity and performance

const CHAT_CACHE_PREFIX = 'chatCache_';

export const chatCache = {
  // Get messages for a session from cache
  getSessionMessages(sessionId) {
    if (!sessionId) return null;
    try {
      const data = localStorage.getItem(`${CHAT_CACHE_PREFIX}${sessionId}`);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('chatCache: Failed to get session messages', e);
      return null;
    }
  },

  // Set messages for a session in cache
  setSessionMessages(sessionId, messages) {
    if (!sessionId) return;
    try {
      localStorage.setItem(`${CHAT_CACHE_PREFIX}${sessionId}`, JSON.stringify(messages));
    } catch (e) {
      console.error('chatCache: Failed to set session messages', e);
    }
  },

  // Remove messages for a session from cache
  clearSessionMessages(sessionId) {
    if (!sessionId) return;
    try {
      localStorage.removeItem(`${CHAT_CACHE_PREFIX}${sessionId}`);
    } catch (e) {
      console.error('chatCache: Failed to clear session messages', e);
    }
  },

  // Clear all chat cache (e.g., on logout)
  clearAll() {
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(CHAT_CACHE_PREFIX))
        .forEach(key => localStorage.removeItem(key));
    } catch (e) {
      console.error('chatCache: Failed to clear all chat cache', e);
    }
  }
}; 