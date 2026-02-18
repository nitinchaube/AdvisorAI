import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "./PageLayout";
import ChatHistoryView from "./ChatHistoryView";
import { apiService } from "../services/api";

const ChatHistoryPage = () => {
  const navigate = useNavigate();
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleNewChat = async (sessionId) => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
    }
  };

  const handleSessionSelect = (sessionId) => {
    setCurrentSessionId(sessionId);
    localStorage.setItem("currentChatSessionId", sessionId);
    // Navigate to chat page to continue the conversation
    navigate("/chat");
  };

  const handleSessionUpdate = (sessionId, newTitle) => {
    if (sessionId === currentSessionId) {
      // Handle session update if needed
    }
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      <div className="h-full w-full">
        <ChatHistoryView
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          onSessionUpdate={handleSessionUpdate}
        />
      </div>
    </PageLayout>
  );
};

export default ChatHistoryPage;
