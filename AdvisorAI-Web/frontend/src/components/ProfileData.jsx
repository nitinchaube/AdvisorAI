import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  MapPin,
  FileText,
  Briefcase,
  GraduationCap,
  Star,
  Award,
  Target,
  Loader2,
  AlertCircle,
  CheckCircle,
  Edit,
  Home,
  Copy,
  Github,
  Linkedin,
} from "lucide-react";

const ProfileData = () => {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [showCopyMsg, setShowCopyMsg] = useState(false);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      setError("");

      console.log("Loading profile data...");
      const response = await apiService.getUserProfile();
      console.log("Profile data response:", response);

      if (
        response.success &&
        response.profile &&
        Object.keys(response.profile).length > 0
      ) {
        setProfileData(response.profile);
      } else {
        setError("No profile data found. Please complete your profile first.");
      }
    } catch (error) {
      console.error("Failed to load profile data:", error);
      setError("Failed to load profile data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Helper function to format field names
  const formatFieldName = (fieldName) => {
    return fieldName
      .replace(/([A-Z])/g, " $1")
      .replace(/^./, (str) => str.toUpperCase())
      .trim();
  };

  // Helper function to get field icon
  const getFieldIcon = (fieldName) => {
    const iconMap = {
      fullName: <User />,
      email: <Mail />,
      phone: <Phone />,
      location: <MapPin />,
      summary: <FileText />,
      experience: <Briefcase />,
      education: <GraduationCap />,
      skills: <Star />,
      certifications: <Award />,
      projects: <Target />,
    };
    return iconMap[fieldName] || <FileText />;
  };

  // Helper function to render field value
  const renderFieldValue = (fieldName, value) => {
    if (fieldName === "projects" && Array.isArray(value)) {
      return (
        <div style={{ marginLeft: "1rem" }}>
          {value.map((item, index) => (
            <div
              key={index}
              style={{
                marginBottom: "0.5rem",
                padding: "0.5rem",
                backgroundColor: "rgba(255,255,255,0.1)",
                borderRadius: "4px",
              }}
            >
              <div>
                <strong>{item.name}</strong>
              </div>
              <div>{item.description}</div>
              {item.github && (
                <div style={{ marginTop: 4 }}>
                  <a
                    href={item.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: "#06b6d4",
                      textDecoration: "underline",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <Github style={{ width: 18, height: 18 }} /> GitHub
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (Array.isArray(value)) {
      return (
        <div style={{ marginLeft: "1rem" }}>
          {value.map((item, index) => (
            <div
              key={index}
              style={{
                marginBottom: "0.5rem",
                padding: "0.5rem",
                backgroundColor: "rgba(255,255,255,0.1)",
                borderRadius: "4px",
              }}
            >
              {typeof item === "object" && item !== null ? (
                <div>
                  {Object.entries(item).map(([key, val]) => (
                    <div key={key} style={{ marginBottom: "0.25rem" }}>
                      <strong>{formatFieldName(key)}:</strong>{" "}
                      {String(val || "Not specified")}
                    </div>
                  ))}
                </div>
              ) : (
                <span>{String(item || "Not specified")}</span>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === "object" && value !== null) {
      return (
        <div style={{ marginLeft: "1rem" }}>
          {Object.entries(value).map(([key, val]) => (
            <div key={key} style={{ marginBottom: "0.25rem" }}>
              <strong>{formatFieldName(key)}:</strong>{" "}
              {String(val || "Not specified")}
            </div>
          ))}
        </div>
      );
    }

    return <span>{String(value || "Not specified")}</span>;
  };

  // Share Portfolio handler
  const handleSharePortfolio = () => {
    if (!currentUser || !currentUser.uid) return;
    const shareUrl = `${window.location.origin}/portfolio/${currentUser.uid}`;
    navigator.clipboard.writeText(shareUrl);
    setShowCopyMsg(true);
    setTimeout(() => setShowCopyMsg(false), 2000);
  };

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          padding: "2rem",
        }}
      >
        <Loader2
          style={{
            width: "3rem",
            height: "3rem",
            animation: "spin 1s linear infinite",
          }}
        />
        <p>Loading your profile data...</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          padding: "2rem",
        }}
      >
        <AlertCircle
          style={{
            width: "4rem",
            height: "4rem",
            color: "#ef4444",
            marginBottom: "1rem",
          }}
        />
        <h2>Error Loading Profile</h2>
        <p>{error}</p>
        <div style={{ display: "flex", gap: "1rem", marginTop: "2rem" }}>
          <button
            style={{
              padding: "0.75rem 1.5rem",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
            onClick={loadProfileData}
          >
            <Loader2 style={{ width: "1.2rem", height: "1.2rem" }} />
            Retry
          </button>
          <button
            style={{
              padding: "0.75rem 1.5rem",
              background: "rgba(255, 255, 255, 0.1)",
              color: "white",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
            onClick={() => navigate("/dashboard")}
          >
            <ArrowLeft style={{ width: "1.2rem", height: "1.2rem" }} />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: "2rem",
        color: "white",
        overflow: "auto", // Make the profile section scrollable
        maxHeight: "calc(100vh - 5rem)", // Leave space for header
        boxSizing: "border-box",
      }}
    >
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "1.5rem",
              marginBottom: "1.5rem",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "4rem",
                height: "4rem",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                borderRadius: "50%",
                boxShadow: "0 8px 32px rgba(102, 126, 234, 0.4)",
              }}
            >
              <User
                style={{ width: "2.5rem", height: "2.5rem", color: "white" }}
              />
            </div>
            <div>
              <h1
                style={{
                  fontSize: "3rem",
                  fontWeight: "700",
                  margin: "0",
                  textShadow: "0 4px 8px rgba(0, 0, 0, 0.3)",
                }}
              >
                Profile Data
              </h1>
              <div
                style={{
                  display: "flex",
                  gap: "1rem",
                  marginTop: 8,
                  justifyContent: "center",
                }}
              >
                {profileData?.github && (
                  <a
                    href={profileData.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="GitHub"
                    style={{
                      color: "#fff",
                      background: "#23272f",
                      borderRadius: "50%",
                      padding: 6,
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Github style={{ width: 22, height: 22 }} />
                  </a>
                )}
                {profileData?.linkedin && (
                  <a
                    href={profileData.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="LinkedIn"
                    style={{
                      color: "#fff",
                      background: "#0a66c2",
                      borderRadius: "50%",
                      padding: 6,
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Linkedin style={{ width: 22, height: 22 }} />
                  </a>
                )}
              </div>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  background: "rgba(255, 255, 255, 0.1)",
                  border: "1px solid rgba(255, 255, 255, 0.2)",
                  borderRadius: "20px",
                  padding: "0.5rem 1rem",
                  marginTop: "0.5rem",
                }}
              >
                <CheckCircle
                  style={{ width: "1rem", height: "1rem", color: "white" }}
                />
                <span
                  style={{
                    fontSize: "0.9rem",
                    color: "white",
                    fontWeight: "500",
                  }}
                >
                  Your Stored Information
                </span>
              </div>
            </div>
          </div>
          <p
            style={{
              fontSize: "1.2rem",
              color: "rgba(255, 255, 255, 0.9)",
              margin: "0",
            }}
          >
            View all your profile information stored in our database
          </p>
        </div>

        {/* Navigation */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "2rem",
            gap: "1rem",
          }}
        >
          <button
            style={{
              padding: "0.75rem 1.5rem",
              background: "rgba(255, 255, 255, 0.1)",
              color: "white",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
            onClick={() => navigate("/dashboard")}
          >
            <ArrowLeft style={{ width: "1.2rem", height: "1.2rem" }} />
            Back to Dashboard
          </button>

          <button
            style={{
              padding: "0.75rem 1.5rem",
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
            onClick={() => navigate("/profile-completion")}
          >
            <Edit style={{ width: "1.2rem", height: "1.2rem" }} />
            Edit Profile
          </button>
          <button
            style={{
              padding: "0.75rem 1.5rem",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
            onClick={handleSharePortfolio}
          >
            <Copy style={{ width: "1.2rem", height: "1.2rem" }} />
            Share Portfolio
          </button>
        </div>

        {/* Profile Data Display */}
        <div>
          {profileData && Object.keys(profileData).length > 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1.5rem",
              }}
            >
              {Object.entries(profileData).map(([fieldName, fieldValue]) => (
                <div
                  key={fieldName}
                  style={{
                    background: "rgba(255, 255, 255, 0.1)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "16px",
                    padding: "1.5rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "1rem",
                      marginBottom: "1rem",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "2.5rem",
                        height: "2.5rem",
                        background:
                          "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        borderRadius: "8px",
                        color: "white",
                      }}
                    >
                      {getFieldIcon(fieldName)}
                    </div>
                    <h3
                      style={{
                        fontSize: "1.2rem",
                        fontWeight: "600",
                        margin: "0",
                      }}
                    >
                      {formatFieldName(fieldName)}
                    </h3>
                  </div>

                  <div
                    style={{
                      marginLeft: "3.5rem",
                      color: "rgba(255, 255, 255, 0.9)",
                      lineHeight: "1.6",
                    }}
                  >
                    {renderFieldValue(fieldName, fieldValue)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                textAlign: "center",
                padding: "4rem 2rem",
                background: "rgba(255, 255, 255, 0.1)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: "24px",
              }}
            >
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "5rem",
                  height: "5rem",
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  borderRadius: "50%",
                  marginBottom: "1.5rem",
                  boxShadow: "0 8px 16px rgba(102, 126, 234, 0.3)",
                }}
              >
                <User
                  style={{ width: "2.5rem", height: "2.5rem", color: "white" }}
                />
              </div>
              <h3
                style={{
                  fontSize: "1.8rem",
                  fontWeight: "600",
                  margin: "0 0 1rem 0",
                }}
              >
                No Profile Data Found
              </h3>
              <p
                style={{
                  fontSize: "1.1rem",
                  color: "rgba(255, 255, 255, 0.8)",
                  margin: "0 0 2rem 0",
                  lineHeight: "1.6",
                }}
              >
                It looks like you haven't completed your profile yet. Please
                complete your profile to see your data here.
              </p>
              <button
                style={{
                  padding: "1rem 2rem",
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  color: "white",
                  border: "none",
                  borderRadius: "12px",
                  fontSize: "1rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
                onClick={() => navigate("/profile-completion")}
              >
                <Edit style={{ width: "1.2rem", height: "1.2rem" }} />
                Complete Profile
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Button */}
      <button
        style={{
          position: "fixed",
          bottom: "2rem",
          right: "2rem",
          width: "3.5rem",
          height: "3.5rem",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          border: "none",
          borderRadius: "50%",
          color: "white",
          cursor: "pointer",
          boxShadow: "0 8px 24px rgba(102, 126, 234, 0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}
        onClick={() => navigate("/dashboard")}
        title="Go to Dashboard"
      >
        <Home />
      </button>

      {/* Snackbar/Toast for copy confirmation */}
      {showCopyMsg && (
        <div
          style={{
            position: "fixed",
            bottom: "2rem",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(34,197,94,0.95)",
            color: "white",
            padding: "1rem 2rem",
            borderRadius: "8px",
            boxShadow: "0 4px 16px rgba(34,197,94,0.2)",
            zIndex: 2000,
            fontWeight: 600,
            fontSize: "1.1rem",
            animation: "fadeInOut 2s",
          }}
        >
          Link copied to clipboard!
          <style>{`
            @keyframes fadeInOut {
              0% { opacity: 0; }
              10% { opacity: 1; }
              90% { opacity: 1; }
              100% { opacity: 0; }
            }
          `}</style>
        </div>
      )}
    </div>
  );
};

export default ProfileData;
