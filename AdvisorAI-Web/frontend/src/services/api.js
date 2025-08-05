const API_BASE_URL = "http://localhost:5002/api";

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper method to get auth headers
  getAuthHeaders() {
    const token = localStorage.getItem("backendToken");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Helper method to make API calls
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const defaultOptions = {
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    const config = { ...defaultOptions, ...options };

    try {
      console.log(` Making request to: ${url}`);
      console.log("📤 Request config:", {
        method: config.method || "GET",
        headers: config.headers,
        body: config.body ? JSON.parse(config.body) : undefined,
      });

      const response = await fetch(url, config);
      console.log(" Response status:", response.status);

      const data = await response.json();
      console.log("📥 Response data:", data);

      if (!response.ok) {
        const errorMessage =
          data.error ||
          data.message ||
          `HTTP ${response.status}: ${response.statusText}`;
        console.error("❌ API Error Response:", errorMessage);
        throw new Error(errorMessage);
      }

      return data;
    } catch (error) {
      console.error("❌ API Error:", error);
      console.error("Error details:", {
        message: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }

  // File upload method with auth
  async uploadFile(endpoint, formData) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem("backendToken");

    try {
      console.log(` Uploading file to: ${url}`);
      console.log("🔑 Token present:", !!token);

      const headers = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers: headers,
        body: formData, // Don't set Content-Type for FormData
      });

      console.log(" Response status:", response.status);

      const data = await response.json();
      console.log("📥 Response data:", data);

      if (!response.ok) {
        const errorMessage =
          data.error ||
          data.message ||
          `HTTP ${response.status}: ${response.statusText}`;
        console.error("❌ Upload Error Response:", errorMessage);
        throw new Error(errorMessage);
      }

      return data;
    } catch (error) {
      console.error("❌ Upload Error:", error);
      throw error;
    }
  }

  // Authentication methods
  async signinWithBackend(idToken) {
    console.log("🔑 Signing in with backend, idToken length:", idToken.length);
    return this.makeRequest("/auth/signin-with-token", {
      method: "POST",
      body: JSON.stringify({ idToken }),
    });
  }

  // Resume upload and parsing
  async uploadAndParseResume(formData) {
    const response = await this.uploadFile(
      "/resume/upload-and-parse",
      formData
    );
    console.log("📥 Raw API response:", response);

    // Ensure we return the correct data structure
    if (response.success && response.data) {
      console.log("✅ Parsed data received:", response.data);
      return {
        success: true,
        data: response.data,
        originalText: response.originalText,
        llmProvider: response.llmProvider,
        message: response.message,
      };
    } else {
      console.error("❌ Unexpected response structure:", response);
      throw new Error(response.error || "Failed to parse resume");
    }
  }

  // Save user profile
  async saveUserProfile(profileData) {
    return this.makeRequest("/user/profile", {
      method: "PUT",
      body: JSON.stringify(profileData),
    });
  }

  // Get user profile
  async getUserProfile() {
    return this.makeRequest("/user/profile");
  }

  // Health check
  async healthCheck() {
    return this.makeRequest("/health");
  }

  // LLM status
  async getLLMStatus() {
    return this.makeRequest("/llm/status");
  }

  async debugTextExtraction(formData) {
    return this.uploadFile("/resume/debug-extraction", formData);
  }

  // Chat methods
  async sendChatMessage(query, chatHistory = [], sessionId = null) {
    return this.makeRequest("/chat/query", {
      method: "POST",
      body: JSON.stringify({
        query,
        chat_history: chatHistory,
        session_id: sessionId,
      }),
    });
  }

  async getChatHistory(limit = 50) {
    return this.makeRequest(`/chat/history?limit=${limit}`);
  }

  // Chat session methods
  async getChatSessions() {
    return this.makeRequest("/chat/sessions");
  }

  async createChatSession(title = "New Chat") {
    return this.makeRequest("/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  }

  async getChatSessionMessages(sessionId) {
    return this.makeRequest(`/chat/sessions/${sessionId}`);
  }

  async updateChatSession(sessionId, title) {
    return this.makeRequest(`/chat/sessions/${sessionId}`, {
      method: "PUT",
      body: JSON.stringify({ title }),
    });
  }

  async deleteChatSession(sessionId) {
    return this.makeRequest(`/chat/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  async getUserChatHistory() {
    return this.makeRequest("/chat/user-history");
  }

  async getRAGStats() {
    return this.makeRequest("/rag/stats");
  }

  async getCollections() {
    return this.makeRequest("/admin/collections");
  }

  async addEntry(collection_name, content, metadata) {
    return this.makeRequest("/admin/courses", {
      method: "POST",
      body: JSON.stringify({ collection_name, content, metadata }),
    });
  }

  async updateEntry(collection_name, id, content, metadata) {
    return this.makeRequest(`/admin/courses/${collection_name}/${id}`, {
      method: "PUT",
      body: JSON.stringify({ content, metadata }),
    });
  }

  async deleteEntry(collection_name, id) {
    return this.makeRequest(`/admin/courses/${collection_name}/${id}`, {
      method: "DELETE",
    });
  }

  // Update getCourses to accept collection_name
  async getEntries(collection_name = "AllCourseRelatedData") {
    return this.makeRequest(`/courses?collection_name=${collection_name}`);
  }

  async getEntry(collection_name, id) {
    return this.makeRequest(
      `/courses/${id}?collection_name=${collection_name}`
    );
  }

  async getCourses() {
    return this.makeRequest("/courses");
  }

  async getCourse(id) {
    return this.makeRequest(`/courses/${id}`);
  }

  async getAllCourses() {
    return this.makeRequest("/admin/courses");
  }

  async addCourse(data) {
    return this.makeRequest("/admin/courses", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateCourse(id, data) {
    return this.makeRequest(`/admin/courses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteCourse(id) {
    return this.makeRequest(`/admin/courses/${id}`, {
      method: "DELETE",
    });
  }

  async getCourse(id) {
    return this.makeRequest(`/admin/courses/${id}`);
  }

  async getAllCourseReviews() {
    return this.makeRequest("/reviews/courses");
  }

  //get faculty data
  async getFaculty() {
    return this.makeRequest("/faculty");
  }

  async getSingleFaculty(id) {
    return this.makeRequest(`/faculty/${id}`);
  }

  async getAllFaculty() {
    return this.makeRequest("/admin/faculty");
  }

  async addFaculty(data) {
    return this.makeRequest("/admin/faculty", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateFaculty(id, data) {
    return this.makeRequest(`/admin/faculty/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteFaculty(id) {
    return this.makeRequest(`/admin/faculty/${id}`, {
      method: "DELETE",
    });
  }

  async getAllProfessorReviews() {
    return this.makeRequest("/reviews/professors");
  }

  // Admin methods
  async addCourse(content, metadata) {
    return this.makeRequest("/admin/courses", {
      method: "POST",
      body: JSON.stringify({ content, metadata }),
    });
  }

  async updateCourse(id, content, metadata) {
    return this.makeRequest(`/admin/courses/${id}`, {
      method: "PUT",
      body: JSON.stringify({ content, metadata }),
    });
  }

  async deleteCourse(id) {
    return this.makeRequest(`/admin/courses/${id}`, {
      method: "DELETE",
    });
  }

  // Streaming chat method
  async streamChatMessage(query, chatHistory = [], onToken) {
    const url = `${this.baseURL}/chat/stream`;
    const token = localStorage.getItem("backendToken");

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          query,
          chat_history: chatHistory,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.token && onToken) {
                onToken(parsed.token);
              }
            } catch (e) {
              console.error("Error parsing stream data:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
      throw error;
    }
  }

  // Submit feedback for a message
  async submitFeedback(messageId, feedback) {
    return this.makeRequest("/chat/feedback", {
      method: "POST",
      body: JSON.stringify({
        message_id: messageId,
        feedback: feedback, // 'positive' or 'negative'
        timestamp: new Date().toISOString(),
      }),
    });
  }

  // Get public profile for portfolio
  async getPublicProfile(userId) {
    return this.makeRequest(`/public-profile/${userId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
  }
}

const apiService = new ApiService();

apiService.getCourseReviews = async function (courseId) {
  const res = await fetch(`${this.baseURL}/courses/${courseId}/reviews`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("backendToken") || ""}`,
    },
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch reviews");
  return await res.json();
};

apiService.postCourseReview = async function (courseId, data, token) {
  const res = await fetch(`${this.baseURL}/courses/${courseId}/reviews`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${
        token || localStorage.getItem("backendToken") || ""
      }`,
    },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to post review");
  return await res.json();
};

apiService.getProfessorReviews = async function (professorId) {
  const res = await fetch(`${this.baseURL}/faculty/${professorId}/reviews`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("backendToken") || ""}`,
    },
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch professor reviews");
  return await res.json();
};

apiService.postProfessorReview = async function (professorId, data, token) {
  const res = await fetch(`${this.baseURL}/faculty/${professorId}/reviews`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${
        token || localStorage.getItem("backendToken") || ""
      }`,
    },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to post professor review");
  return await res.json();
};

// Admin API methods
export const adminAPI = {
  // Courses Admin API
  async getAllCourses() {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/courses`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to fetch courses");
    return await response.json();
  },

  async getCourse(id) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/courses/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to fetch course");
    return await response.json();
  },

  async addCourse(courseData) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/courses`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(courseData),
    });
    if (!response.ok) throw new Error("Failed to add course");
    return await response.json();
  },

  async updateCourse(id, courseData) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/courses/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(courseData),
    });
    if (!response.ok) throw new Error("Failed to update course");
    return await response.json();
  },

  async deleteCourse(id) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/courses/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to delete course");
    return await response.json();
  },

  // Faculty Admin API
  async getAllFaculty() {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/faculty`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to fetch faculty");
    return await response.json();
  },

  async getFaculty(id) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/faculty/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to fetch faculty member");
    return await response.json();
  },

  async addFaculty(facultyData) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/faculty`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(facultyData),
    });
    if (!response.ok) throw new Error("Failed to add faculty member");
    return await response.json();
  },

  async updateFaculty(id, facultyData) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/faculty/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(facultyData),
    });
    if (!response.ok) throw new Error("Failed to update faculty member");
    return await response.json();
  },

  async deleteFaculty(id) {
    const token = localStorage.getItem("backendToken");
    const response = await fetch(`${API_BASE_URL}/admin/faculty/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error("Failed to delete faculty member");
    return await response.json();
  },
};

export { apiService };
