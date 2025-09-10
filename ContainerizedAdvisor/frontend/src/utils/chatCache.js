// Chat cache utility for browser-side chat history caching
// Uses localStorage for simplicity and performance

const CHAT_CACHE_PREFIX = 'chatCache_';
const SESSION_METADATA_PREFIX = 'sessionMeta_';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

export const chatCache = {
  // Get messages for a session from cache
  getSessionMessages(sessionId) {
    if (!sessionId) return null;
    try {
      const data = localStorage.getItem(`${CHAT_CACHE_PREFIX}${sessionId}`);
      if (!data) return null;
      
      const parsed = JSON.parse(data);
      
      // Check if cache has expired
      if (parsed.timestamp && Date.now() - parsed.timestamp > CACHE_EXPIRY) {
        this.clearSessionMessages(sessionId);
        return null;
      }
      
      return parsed.messages || null;
    } catch (e) {
      console.error('chatCache: Failed to get session messages', e);
      return null;
    }
  },

  // Set messages for a session in cache
  setSessionMessages(sessionId, messages) {
    if (!sessionId) return;
    try {
      const cacheData = {
        messages: messages,
        timestamp: Date.now(),
        sessionId: sessionId
      };
      localStorage.setItem(`${CHAT_CACHE_PREFIX}${sessionId}`, JSON.stringify(cacheData));
    } catch (e) {
      console.error('chatCache: Failed to set session messages', e);
    }
  },

  // Remove messages for a session from cache
  clearSessionMessages(sessionId) {
    if (!sessionId) return;
    try {
      localStorage.removeItem(`${CHAT_CACHE_PREFIX}${sessionId}`);
      localStorage.removeItem(`${SESSION_METADATA_PREFIX}${sessionId}`);
    } catch (e) {
      console.error('chatCache: Failed to clear session messages', e);
    }
  },

  // Get session metadata (title, last updated, etc.)
  getSessionMetadata(sessionId) {
    if (!sessionId) return null;
    try {
      const data = localStorage.getItem(`${SESSION_METADATA_PREFIX}${sessionId}`);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('chatCache: Failed to get session metadata', e);
      return null;
    }
  },

  // Set session metadata
  setSessionMetadata(sessionId, metadata) {
    if (!sessionId) return;
    try {
      const cacheData = {
        ...metadata,
        timestamp: Date.now(),
        sessionId: sessionId
      };
      localStorage.setItem(`${SESSION_METADATA_PREFIX}${sessionId}`, JSON.stringify(cacheData));
    } catch (e) {
      console.error('chatCache: Failed to set session metadata', e);
    }
  },

  // Update session title in cache
  updateSessionTitle(sessionId, newTitle) {
    if (!sessionId) return;
    try {
      const metadata = this.getSessionMetadata(sessionId) || {};
      metadata.title = newTitle;
      metadata.last_updated = new Date().toISOString();
      this.setSessionMetadata(sessionId, metadata);
    } catch (e) {
      console.error('chatCache: Failed to update session title', e);
    }
  },

  // Get all cached session IDs
  getCachedSessionIds() {
    try {
      const keys = Object.keys(localStorage);
      return keys
        .filter(key => key.startsWith(CHAT_CACHE_PREFIX))
        .map(key => key.replace(CHAT_CACHE_PREFIX, ''));
    } catch (e) {
      console.error('chatCache: Failed to get cached session IDs', e);
      return [];
    }
  },

  // Clean up expired cache entries
  cleanupExpiredCache() {
    try {
      const sessionIds = this.getCachedSessionIds();
      const now = Date.now();
      
      sessionIds.forEach(sessionId => {
        const messages = this.getSessionMessages(sessionId);
        if (!messages) {
          // Cache was already cleared or expired
          return;
        }
        
        const metadata = this.getSessionMetadata(sessionId);
        if (metadata && metadata.timestamp && (now - metadata.timestamp > CACHE_EXPIRY)) {
          this.clearSessionMessages(sessionId);
          console.log(`chatCache: Cleaned up expired cache for session ${sessionId}`);
        }
      });
    } catch (e) {
      console.error('chatCache: Failed to cleanup expired cache', e);
    }
  },

  // Clear all chat cache (e.g., on logout)
  clearAll() {
    try {
      const keys = Object.keys(localStorage);
      keys
        .filter(key => key.startsWith(CHAT_CACHE_PREFIX) || key.startsWith(SESSION_METADATA_PREFIX))
        .forEach(key => localStorage.removeItem(key));
      console.log('chatCache: Cleared all chat cache');
    } catch (e) {
      console.error('chatCache: Failed to clear all chat cache', e);
    }
  },

  // Get cache statistics
  getCacheStats() {
    try {
      const sessionIds = this.getCachedSessionIds();
      const totalSessions = sessionIds.length;
      let totalMessages = 0;
      let totalSize = 0;
      
      sessionIds.forEach(sessionId => {
        const messages = this.getSessionMessages(sessionId);
        if (messages) {
          totalMessages += messages.length;
        }
        
        const data = localStorage.getItem(`${CHAT_CACHE_PREFIX}${sessionId}`);
        if (data) {
          totalSize += new Blob([data]).size;
        }
      });
      
      return {
        totalSessions,
        totalMessages,
        totalSizeBytes: totalSize,
        totalSizeKB: Math.round(totalSize / 1024 * 100) / 100
      };
    } catch (e) {
      console.error('chatCache: Failed to get cache stats', e);
      return { totalSessions: 0, totalMessages: 0, totalSizeBytes: 0, totalSizeKB: 0 };
    }
  }
};

// Clean up expired cache entries on module load
chatCache.cleanupExpiredCache();

// Set up periodic cleanup every hour
setInterval(() => {
  chatCache.cleanupExpiredCache();
}, 60 * 60 * 1000); 