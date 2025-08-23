import React, { useState, useEffect } from "react";
import PageLayout from "./PageLayout";
import ChatInterface from "./ChatInterface";
import ChatSessionManager from "./ChatSessionManager";
import { apiService } from "../services/api";

const ChatPage = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentSessionTitle, setCurrentSessionTitle] = useState("New Chat");
  const [chatHistoryOpen, setChatHistoryOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleChatHistoryToggle = () => {
    setChatHistoryOpen(!chatHistoryOpen);
  };

  const handleNewChat = async (sessionId) => {
    if (isCreatingSession) return; // Prevent multiple simultaneous session creation
    
    console.log("📱 ChatPage: handleNewChat called with sessionId:", sessionId);
    
    try {
      setIsCreatingSession(true);
      
      if (sessionId) {
        // Use provided session ID
        console.log("📱 ChatPage: Using provided session ID:", sessionId);
        setCurrentSessionId(sessionId);
        await loadSessionTitle(sessionId);
        console.log("📱 Using provided session ID:", sessionId);
      } else {
        // Create new session
        console.log("📱 ChatPage: Creating new chat session");
        const response = await apiService.createChatSession("New Chat");
        if (response.success) {
          const newSessionId = response.session_id;
          console.log("📱 ChatPage: New session created:", newSessionId);
          setCurrentSessionId(newSessionId);
          setCurrentSessionTitle("New Chat");
          localStorage.setItem("currentChatSessionId", newSessionId);
          console.log("📱 Created new chat session:", newSessionId);
        } else {
          throw new Error(response.error || "Failed to create session");
        }
      }
      
      setChatHistoryOpen(false);
    } catch (error) {
      console.error("Error in handleNewChat:", error);
      // Show error to user (you could add a toast notification here)
    } finally {
      setIsCreatingSession(false);
    }
  };

  const handleSessionSelect = async (sessionId) => {
    if (sessionId === currentSessionId) return; // No need to reload same session
    
    try {
      setCurrentSessionId(sessionId);
      localStorage.setItem("currentChatSessionId", sessionId);
      await loadSessionTitle(sessionId);
      setChatHistoryOpen(false);
      console.log("📱 Selected chat session:", sessionId);
    } catch (error) {
      console.error("Error selecting session:", error);
    }
  };

  const handleSessionUpdate = (sessionId, newTitle) => {
    console.log("📱 ChatPage: handleSessionUpdate called with:", { sessionId, newTitle });
    if (sessionId === currentSessionId) {
      console.log("📱 ChatPage: Updating current session title from", currentSessionTitle, "to", newTitle);
      setCurrentSessionTitle(newTitle);
      console.log("📱 Updated session title:", newTitle);
    } else {
      console.log("📱 ChatPage: Session update for different session:", sessionId, "current:", currentSessionId);
    }
  };

  const loadSessionTitle = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await apiService.getChatSessionMessages(sessionId);
      if (response.success && response.session) {
        const title = response.session.title || "New Chat";
        setCurrentSessionTitle(title);
        console.log("📱 Loaded session title:", title);
      }
    } catch (error) {
      console.error("Error loading session title:", error);
      setCurrentSessionTitle("New Chat");
    }
  };

  useEffect(() => {
    const initializeSession = async () => {
      if (sessionInitialized) return;

      try {
        const storedSessionId = localStorage.getItem("currentChatSessionId");

        if (storedSessionId) {
          try {
            const response = await apiService.getChatSessionMessages(storedSessionId);
            if (response.success) {
              setCurrentSessionId(storedSessionId);
              setCurrentSessionTitle(response.session.title || "New Chat");
              console.log("📱 Restored previous chat session:", storedSessionId);
              setSessionInitialized(true);
              return;
            } else {
              console.log("📱 Stored session not found, removing from localStorage");
              localStorage.removeItem("currentChatSessionId");
            }
          } catch (error) {
            console.log("📱 Could not restore previous session, removed from localStorage:", error);
            localStorage.removeItem("currentChatSessionId");
          }
        }

        // No session to restore, create a new one
        console.log("📱 No session restored, creating new chat session");
        await handleNewChat(null);
        setSessionInitialized(true);
      } catch (error) {
        console.error("Error initializing session:", error);
        setSessionInitialized(true);
      }
    };

    initializeSession();
  }, [sessionInitialized]);

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      <div className="h-full flex flex-col md:flex-row relative">
        {/* Chat Interface - Takes full width on mobile, left side on desktop */}
        <div className="flex-1 min-w-0 h-full">
          <ChatInterface
            onToggleHistory={handleChatHistoryToggle}
            currentSessionId={currentSessionId}
            onSessionUpdate={handleSessionUpdate}
            sessionTitle={currentSessionTitle}
            onNewChat={() => handleNewChat(null)}
          />
        </div>

        {/* Chat Session Manager - Right sidebar on mobile, always visible on desktop */}
        <div
          className={`
          ${chatHistoryOpen ? "block" : "hidden"} 
          md:block 
          absolute md:relative 
          top-0 right-0 
          w-full md:w-80 
          h-full 
          z-30 
          border-l border-white/20 
          backdrop-blur-sm 
          bg-white/10 
          flex-shrink-0
          md:bg-gradient-to-br md:from-slate-900/95 md:via-purple-900/90 md:to-indigo-900/95
        `}
        >
          <ChatSessionManager
            onSessionSelect={handleSessionSelect}
            onNewChat={handleNewChat}
            onClose={() => setChatHistoryOpen(false)}
            currentSessionId={currentSessionId}
            onSessionUpdate={handleSessionUpdate}
          />
        </div>
      </div>
    </PageLayout>
  );
};

export default ChatPage;
