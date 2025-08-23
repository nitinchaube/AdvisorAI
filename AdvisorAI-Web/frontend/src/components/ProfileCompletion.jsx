import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";
import {
  Upload,
  FileText,
  User,
  X,
  CheckCircle,
  Sparkles,
  Zap,
  ArrowLeft,
  ArrowRight,

  Eye,
  ChevronLeft,
  ChevronRight,
  Home,
  Save,
  Award,
  GraduationCap,
  Briefcase,
  MapPin,
  Mail,
  Phone,
  Star,
  Shield,
  Rocket,
  Target,
  Users,
  Clock,
  CheckSquare,
  Edit,
  Trash2,
  PlusCircle,
  EyeOff,
  ArrowUpRight,
  Check,
  AlertCircle,
  Loader2,
  Linkedin,
  Github,
} from "lucide-react";
import "./ProfileCompletion.css";
import ThemeSelector from "./ThemeSelector";
import StaticHeader from "./StaticHeader";

const ProfileCompletion = () => {
  const [currentView, setCurrentView] = useState(0); // 0: Upload, 1: Profile Form
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);

  const [showFeatures, setShowFeatures] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [formData, setFormData] = useState({});
  const [uploadStep, setUploadStep] = useState(0); // 0: Select, 1: Processing, 2: Complete
  const [loadingExistingProfile, setLoadingExistingProfile] = useState(true); // Start with loading

  const fileInputRef = useRef();
  const containerRef = useRef();
  const { currentUser, userProfile, markProfileCompleted } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Show features after a delay
    const timeoutId = setTimeout(() => setShowFeatures(true), 1000);
    return () => clearTimeout(timeoutId);
  }, []);

  // Effect to load existing profile data or show upload form
  useEffect(() => {
    // Only run this logic if the user profile is loaded and we haven't processed a resume yet
    if (userProfile && !parsedData) {
      if (userProfile.profileCompleted) {
        console.log(
          "ProfileCompletion: Profile is complete, loading existing data..."
        );
        const initialFormData = {
          ...userProfile,
          portfolioName: userProfile.portfolioName || userProfile.fullName?.toLowerCase().replace(/\s+/g, '-') || currentUser.uid,
          portfolioTheme: userProfile.portfolioTheme || "slate",
        };
        setFormData(initialFormData);
        setCurrentView(1); // Go directly to form view for editing
        setSuccess(
          "Profile loaded. You can now edit your information or upload a new resume to update it."
        );
        setTimeout(() => setSuccess(""), 4000);
      } else {
        console.log(
          "ProfileCompletion: Profile not complete, showing upload view."
        );
        // User is new or hasn't completed their profile, show the upload view
        setCurrentView(0);
      }
      setLoadingExistingProfile(false);
    } else if (!userProfile) {
      // Still waiting for profile to load
      setLoadingExistingProfile(true);
    }
  }, [userProfile, parsedData, navigate]);

  // Update form data when parsed data changes
  useEffect(() => {
    if (parsedData && parsedData.data) {
      const parsedFormData = {
        ...parsedData.data,
        portfolioName: parsedData.data.portfolioName || parsedData.data.fullName?.toLowerCase().replace(/\s+/g, '-') || currentUser.uid,
        portfolioTheme: parsedData.data.portfolioTheme || "slate",
      };
      setFormData(parsedFormData);
      // After parsing a resume, always go to the form view
      setCurrentView(1);
    }
  }, [parsedData]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragActive(true);
    }
  };

  const handleDragOut = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (selectedFile) => {
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError("Please select a valid file type (PDF, DOC, or DOCX)");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      // 10MB limit
      setError("File size must be less than 10MB");
      return;
    }

    setFile(selectedFile);
    setError("");
    setUploadStep(0);
  };

  const handleFileInput = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setProgress(0);
      setUploadStep(1);

      const uploadFormData = new FormData();
      uploadFormData.append("resume", file);
      uploadFormData.append("userId", currentUser.uid);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await apiService.uploadAndParseResume(uploadFormData);

      clearInterval(progressInterval);
      setProgress(100);
      setUploadStep(2);

      if (response.success && response.data) {
        console.log("✅ Resume parsed successfully:", response.data);
        setParsedData(response);
        setSuccess(
          "Resume parsed successfully! Review your extracted data below."
        );

        setTimeout(() => {
          setSuccess("");
        }, 2000);
      } else {
        throw new Error(response.error || "Failed to parse resume");
      }
    } catch (error) {
      console.error("❌ Upload error:", error);
      setError(`Upload failed: ${error.message}`);
      setUploadStep(0);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleFormChange = (fieldName, value) => {
    // Special handling for portfolio name
    if (fieldName === "portfolioName") {
      // Sanitize the portfolio name to be URL-friendly
      const sanitizedValue = value
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-') // Only allow letters, numbers, and hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
        .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
      
      setFormData((prev) => ({
        ...prev,
        [fieldName]: sanitizedValue,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [fieldName]: value,
      }));
    }
  };

  // This function handles both saving a new profile and updating an existing one.
  const handleSaveOrUpdateProfile = async () => {
    try {
      setParsing(true);
      setError("");

      const isUpdating = userProfile?.profileCompleted;
      const response = await apiService.saveUserProfile(formData);

      // Refetch profile from backend to update the AuthContext state
      await markProfileCompleted();

      if (isUpdating) {
        setSuccess("Profile updated successfully!");
      } else {
        setSuccess("Profile completed! Redirecting to dashboard...");
        setTimeout(() => {
          navigate("/dashboard");
        }, 2000);
      }

      // Clear success message after a few seconds
      setTimeout(() => setSuccess(""), 3000);
    } catch (error) {
      setError(`Save failed: ${error.message}`);
    } finally {
      setParsing(false);
    }
  };

  

  const features = [
    {
      icon: <Sparkles className="feature-icon" />,
      title: "AI-Powered Extraction",
      description:
        "Advanced LLM technology extracts all your information with 95% accuracy",
    },
    {
      icon: <Zap className="feature-icon" />,
      title: "Lightning Fast",
      description:
        "Process your resume in seconds with our optimized AI pipeline",
    },
    {
      icon: <Shield className="feature-icon" />,
      title: "Secure & Private",
      description: "Your data is encrypted and never shared with third parties",
    },
    {
      icon: <Target className="feature-icon" />,
      title: "Smart Recognition",
      description:
        "Intelligently identifies and categorizes all resume sections",
    },
  ];

  const stats = [
    { number: "10K+", label: "Resumes Processed", icon: <FileText /> },
    { number: "95%", label: "Accuracy Rate", icon: <CheckSquare /> },
    { number: "< 30s", label: "Average Time", icon: <Clock /> },
    { number: "24/7", label: "AI Available", icon: <Users /> },
  ];

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
      portfolioName: <User />,
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
    if (Array.isArray(value)) {
      return (
        <div className="array-field">
          {value.map((item, index) => (
            <div key={index} className="array-item">
              {typeof item === "object" && item !== null ? (
                <div className="object-item">
                  {Object.entries(item).map(([key, val]) => (
                    <div key={key} className="object-field">
                      <span className="field-label">
                        {formatFieldName(key)}:
                      </span>
                      <span className="field-value">
                        {String(val || "Not specified")}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="field-value">
                  {String(item || "Not specified")}
                </span>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === "object" && value !== null) {
      return (
        <div className="object-field">
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="nested-field">
              <span className="field-label">{formatFieldName(key)}:</span>
              <span className="field-value">
                {String(val || "Not specified")}
              </span>
            </div>
          ))}
        </div>
      );
    }

    return (
      <span className="field-value">{String(value || "Not specified")}</span>
    );
  };

  // Modern input/textarea style
  const inputStyle = {
    width: "100%",
    fontSize: "1.08rem",
    padding: "0.7em 1.1em",
    borderRadius: 10,
    border: "1.5px solid #d1d5db",
    background: "#f7fafc",
    color: "#232946",
    marginBottom: 10,
    boxShadow: "0 1px 4px rgba(102,126,234,0.06)",
    outline: "none",
    transition: "border-color 0.18s, box-shadow 0.18s",
  };
  const inputFocusStyle = {
    border: "1.5px solid #38bdf8",
    boxShadow: "0 2px 8px rgba(56,189,248,0.13)",
    background: "#e0f2fe",
  };
  const labelStyle = {
    fontWeight: 600,
    color: "#232946",
    marginBottom: 4,
    fontSize: "1.01rem",
    display: "block",
  };
  // Update projectCardStyle for better elevation and separation
  const projectCardStyle = {
    background: "#f8fafc",
    borderRadius: 16,
    boxShadow: "0 4px 24px rgba(56,189,248,0.13)",
    padding: "1.5rem 1.2rem 1.2rem 1.2rem",
    marginBottom: 24,
    border: "2px solid #bae6fd",
    position: "relative",
    transition: "box-shadow 0.18s, border-color 0.18s",
    minWidth: 0,
    overflow: "hidden",
  };
  const removeBtnStyle = {
    background: "#fff0f0",
    border: "1.5px solid #ef4444",
    color: "#ef4444",
    cursor: "pointer",
    fontSize: 20,
    position: "absolute",
    top: 14,
    right: 14,
    borderRadius: 8,
    padding: 6,
    transition: "background 0.18s, border-color 0.18s, color 0.18s",
    zIndex: 2,
  };
  const addBtnStyle = {
    background: "linear-gradient(90deg, #38bdf8 0%, #06b6d4 100%)",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "0.5rem 1.2rem",
    fontWeight: 600,
    fontSize: "1.01rem",
    cursor: "pointer",
    marginTop: 8,
    display: "flex",
    alignItems: "center",
    gap: 6,
  };

  const renderUploadView = () => (
    <div className="view-container upload-view">
      <div className="content-wrapper">
        
        {/* Stats Section */}
        <div className="stats-section">
          {stats.map((stat, index) => (
            <div key={index} className="stat-card">
              <div className="stat-icon">{stat.icon}</div>
              <div className="stat-number">{stat.number}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>

        <div className="upload-container">
          {/* Upload Card */}
          <div className="upload-card">
            <div className="upload-header">
              <h2 className="upload-title">
                {userProfile?.profileCompleted
                  ? "Update Your Resume"
                  : "Upload Your Resume"}
              </h2>
              <p className="upload-description">
                {userProfile?.profileCompleted
                  ? "Upload a new resume to update your profile information with the latest data"
                  : "Drop your resume and let our advanced AI extract everything automatically"}
              </p>
            </div>

            <div
              className={`upload-area ${dragActive ? "drag-active" : ""} ${
                file ? "has-file" : ""
              } step-${uploadStep}`}
              onDragEnter={handleDragIn}
              onDragLeave={handleDragOut}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {!file ? (
                <div className="upload-prompt">
                  <div className="upload-icon-container">
                    <div className="icon-ring">
                      <Upload className="upload-icon" />
                    </div>
                  </div>
                  <h3>Drop your resume here</h3>
                  <p>or click to browse files</p>
                  <button
                    className="browse-btn"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <FileText className="browse-icon" />
                    Browse Files
                  </button>
                  <div className="supported-formats">
                    <span>Supported: PDF, DOC, DOCX</span>
                  </div>
                </div>
              ) : (
                <div className="file-selected">
                  <div className="file-icon-container">
                    <div className="file-glow">
                      <FileText className="file-icon" />
                    </div>
                  </div>
                  <div className="file-info">
                    <h4>{file.name}</h4>
                    <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button
                    className="remove-file-btn"
                    onClick={() => setFile(null)}
                  >
                    <X />
                  </button>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileInput}
              style={{ display: "none" }}
            />

            {file && (
              <div className="upload-progress">
                <div className="progress-container">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${progress}%` }}
                    />
                    <div className="progress-shimmer" />
                  </div>
                  <span className="progress-text">
                    {uploading
                      ? "Processing your resume..."
                      : "Ready to upload"}
                  </span>
                </div>
              </div>
            )}

            <div className="action-buttons">
              <button
                className="upload-btn primary-btn"
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? (
                  <>
                    <Loader2 className="loading-spinner" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Rocket className="btn-icon" />
                    {userProfile?.profileCompleted
                      ? "Update Resume"
                      : "Parse Resume"}
                  </>
                )}
              </button>


            </div>


          </div>
        </div>

        {/* Features Section */}
        <div className="features-section">
          <h3>Why Choose Our AI-Powered Solution?</h3>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon-container">{feature.icon}</div>
                <h4>{feature.title}</h4>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // In renderProfileForm, update the field rendering for better UI/UX
  const renderProfileForm = () => (
    <div className="view-container profile-form-view">
      <div className="content-wrapper">
        {/* Upload Container */}
        <div className="upload-container">
          <h1 className="page-title">Profile Information</h1>
          <p className="page-subtitle">
            Review and edit the information extracted from your resume by our AI
          </p>
        </div>

        <div className="profile-form-container">
          <div className="form-header">
            <div className="form-info">
              <h2>
                {userProfile?.profileCompleted
                  ? "Edit Profile Information"
                  : "Extracted Information"}
              </h2>
              <p>
                {userProfile?.profileCompleted
                  ? "Update your profile information. All changes will be saved automatically."
                  : "All fields have been automatically filled from your resume using advanced AI. You can edit any field by clicking on it."}
              </p>
            </div>

            <div className="form-actions">
              {userProfile?.profileCompleted ? (
                // If profile is complete, show a button to re-upload
                <button
                  className="back-btn secondary-btn"
                  onClick={() => setCurrentView(0)}
                >
                  <Upload className="btn-icon" />
                  Upload New Resume
                </button>
              ) : (
                // If profile is not complete, show back to upload
                <button
                  className="back-btn secondary-btn"
                  onClick={() => setCurrentView(0)}
                >
                  <ArrowLeft className="btn-icon" />
                  Back to Upload
                </button>
              )}
            </div>
          </div>

          <div className="form-content">
            {/* Theme Selector */}
            <div className="form-field theme-selector-field">
              <ThemeSelector
                selectedTheme={formData.portfolioTheme || "slate"}
                onThemeChange={(theme) =>
                  handleFormChange("portfolioTheme", theme)
                }
              />
            </div>

            {/* --- Portfolio Name Field --- */}
            <div className="form-field profile-card-field">
              <div className="field-header">
                <div className="field-icon">
                  <User />
                </div>
                <h3 className="field-title">Portfolio Name</h3>
                <button
                  className="edit-btn"
                  onClick={() =>
                    setEditingField(editingField === "portfolioName" ? null : "portfolioName")
                  }
                  title="Edit portfolio name"
                >
                  {editingField === "portfolioName" ? <EyeOff /> : <Edit />}
                </button>
              </div>
              <div className="field-content">
                {editingField === "portfolioName" ? (
                  <div className="edit-mode">
                    <input
                      type="text"
                      value={formData.portfolioName || ""}
                      onChange={(e) =>
                        handleFormChange("portfolioName", e.target.value)
                      }
                      placeholder="Enter your portfolio name (e.g., john-doe)"
                      className="field-input"
                    />
                    <div className="field-help">
                      This will be your portfolio URL: <span className="portfolio-url">localhost:3000/portfolio/{formData.portfolioName || 'your-name'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="view-mode">
                    {formData.portfolioName ? (
                      <div>
                        <span className="field-value">{formData.portfolioName}</span>
                        <div className="portfolio-link">
                          <span className="portfolio-url">localhost:3000/portfolio/{formData.portfolioName}</span>
                        </div>
                      </div>
                    ) : (
                      <span className="field-value">Not specified</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* --- GitHub and LinkedIn fields --- */}
            <div className="form-field profile-card-field">
              <div className="field-header">
                <div className="field-icon">
                  <Star />
                </div>
                <h3 className="field-title">GitHub</h3>
                <button
                  className="edit-btn"
                  onClick={() =>
                    setEditingField(editingField === "github" ? null : "github")
                  }
                  title="Edit field"
                >
                  {editingField === "github" ? <EyeOff /> : <Edit />}
                </button>
              </div>
              <div className="field-content">
                {editingField === "github" ? (
                  <div className="edit-mode">
                    <input
                      type="url"
                      value={formData.github || ""}
                      onChange={(e) =>
                        handleFormChange("github", e.target.value)
                      }
                      placeholder="Enter your GitHub profile URL"
                      className="field-input"
                    />
                  </div>
                ) : (
                  <div className="view-mode">
                    {formData.github ? (
                      <a
                        href={formData.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="field-link"
                      >
                        {formData.github}
                      </a>
                    ) : (
                      <span className="field-value">Not specified</span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="form-field profile-card-field">
              <div className="field-header">
                <div className="field-icon">
                  <Linkedin />
                </div>
                <h3 className="field-title">LinkedIn</h3>
                <button
                  className="edit-btn"
                  onClick={() =>
                    setEditingField(
                      editingField === "linkedin" ? null : "linkedin"
                    )
                  }
                  title="Edit field"
                >
                  {editingField === "linkedin" ? <EyeOff /> : <Edit />}
                </button>
              </div>
              <div className="field-content">
                {editingField === "linkedin" ? (
                  <div className="edit-mode">
                    <input
                      type="url"
                      value={formData.linkedin || ""}
                      onChange={(e) =>
                        handleFormChange("linkedin", e.target.value)
                      }
                      placeholder="Enter your LinkedIn profile URL"
                      className="field-input"
                    />
                  </div>
                ) : (
                  <div className="view-mode">
                    {formData.linkedin ? (
                      <a
                        href={formData.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="field-link"
                      >
                        {formData.linkedin}
                      </a>
                    ) : (
                      <span className="field-value">Not specified</span>
                    )}
                  </div>
                )}
              </div>
            </div>
            {/* --- End GitHub/LinkedIn fields --- */}

            {/* --- Other fields (auto-generated, card style) --- */}
            {Object.entries(formData)
              .filter(
                ([fieldName]) =>
                  ![
                    "resumeData",
                    "resumeText",
                    "github",
                    "linkedin",
                    "profileCompleted",
                    "portfolioName",
                  ].includes(fieldName)
              )
              .map(([fieldName, fieldValue]) => (
                <div
                  key={fieldName}
                  className={`form-field profile-card-field ${
                    fieldName === "skills" ? "skills-field" : ""
                  }`}
                  tabIndex={0}
                >
                  <div className="field-header">
                    <div className="field-icon">
                      {getFieldIcon(fieldName)}
                    </div>
                    <h3 className="field-title">
                      {formatFieldName(fieldName)}
                    </h3>
                    <div className="field-actions">
                      <button
                        className="edit-btn"
                        onClick={() =>
                          setEditingField(
                            editingField === fieldName ? null : fieldName
                          )
                        }
                        title="Edit field"
                      >
                        {editingField === fieldName ? <EyeOff /> : <Edit />}
                      </button>
                      {editingField === fieldName && (
                        <button
                          className="delete-btn"
                          onClick={() => {
                            // Clear the field value
                            handleFormChange(fieldName, "");
                            setEditingField(null);
                          }}
                          title="Clear field"
                        >
                          <Trash2 />
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="field-content">
                    {editingField === fieldName ? (
                      <div className="edit-mode" style={{ marginTop: 8 }}>
                        {/* Special handling for projects array */}
                        {fieldName === "projects" &&
                        Array.isArray(fieldValue) ? (
                          <div
                            className="array-edit"
                            style={{
                              background: "transparent",
                              borderRadius: 0,
                              padding: 0,
                              marginBottom: 0,
                            }}
                          >
                            {fieldValue.map((item, index) => (
                              <div
                                key={index}
                                className="array-item-edit"
                                style={{
                                  background: "#38bdf8",
                                  borderRadius: 14,
                                  boxShadow: "0 2px 12px rgba(56,189,248,0.10)",
                                  padding: "2rem 1.5rem 1.5rem 1.5rem",
                                  marginBottom: 32,
                                  border: "2px solid #38bdf8",
                                  position: "relative",
                                  minWidth: 0,
                                  overflow: "hidden",
                                }}
                              >
                                {/* Card header with icon and index */}
                                <div
                                  style={{
                                    display: "flex",
                                    alignItems: "center",
                                    marginBottom: 18,
                                  }}
                                >
                                  <Target
                                    style={{
                                      color: "#38bdf8",
                                      marginRight: 10,
                                      fontSize: 22,
                                    }}
                                  />
                                  <span
                                    style={{
                                      fontWeight: 700,
                                      color: "#232946",
                                      fontSize: "1.13rem",
                                    }}
                                  >
                                    Project {index + 1}
                                  </span>
                                </div>
                                <div
                                  style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 18,
                                  }}
                                >
                                  <div style={{ width: "100%" }}>
                                    <label
                                      style={{
                                        ...labelStyle,
                                        fontWeight: 700,
                                        color: "#232946",
                                        marginBottom: 6,
                                      }}
                                    >
                                      Project Name
                                    </label>
                                    <input
                                      type="text"
                                      value={item.name || ""}
                                      onChange={(e) => {
                                        const newValue = [...fieldValue];
                                        newValue[index] = {
                                          ...item,
                                          name: e.target.value,
                                        };
                                        handleFormChange(fieldName, newValue);
                                      }}
                                      placeholder="Project Name"
                                      style={{
                                        ...inputStyle,
                                        background: "#fff",
                                        color: "#232946",
                                        fontWeight: 500,
                                        fontSize: "1.08rem",
                                        width: "100%",
                                      }}
                                      onFocus={(e) =>
                                        Object.assign(
                                          e.target.style,
                                          inputFocusStyle
                                        )
                                      }
                                      onBlur={(e) =>
                                        Object.assign(
                                          e.target.style,
                                          inputStyle
                                        )
                                      }
                                    />
                                  </div>
                                  <div style={{ width: "100%" }}>
                                    <label
                                      style={{
                                        ...labelStyle,
                                        fontWeight: 700,
                                        color: "#232946",
                                        marginBottom: 6,
                                      }}
                                    >
                                      Description
                                    </label>
                                    <textarea
                                      value={item.description || ""}
                                      onChange={(e) => {
                                        const newValue = [...fieldValue];
                                        newValue[index] = {
                                          ...item,
                                          description: e.target.value,
                                        };
                                        handleFormChange(fieldName, newValue);
                                      }}
                                      placeholder="Project Description"
                                      style={{
                                        ...inputStyle,
                                        minHeight: 80,
                                        resize: "vertical",
                                        fontFamily: "inherit",
                                        background: "#fff",
                                        color: "#232946 !important",
                                        fontWeight: 500,
                                        fontSize: "1.08rem",
                                        width: "100%",
                                      }}
                                      onFocus={(e) =>
                                        Object.assign(e.target.style, {
                                          ...inputFocusStyle,
                                          minHeight: 100,
                                        })
                                      }
                                      onBlur={(e) =>
                                        Object.assign(e.target.style, {
                                          ...inputStyle,
                                          minHeight: 80,
                                        })
                                      }
                                    />
                                  </div>
                                  <div style={{ width: "100%" }}>
                                    <label
                                      style={{
                                        ...labelStyle,
                                        fontWeight: 700,
                                        color: "#232946",
                                        marginBottom: 6,
                                      }}
                                    >
                                      GitHub Link
                                    </label>
                                    <input
                                      type="url"
                                      value={item.github || ""}
                                      onChange={(e) => {
                                        const newValue = [...fieldValue];
                                        newValue[index] = {
                                          ...item,
                                          github: e.target.value,
                                        };
                                        handleFormChange(fieldName, newValue);
                                      }}
                                      placeholder="Project GitHub Link (optional)"
                                      style={{
                                        ...inputStyle,
                                        background: "#fff",
                                        color: "#232946",
                                        fontWeight: 500,
                                        fontSize: "1.08rem",
                                        width: "100%",
                                      }}
                                      onFocus={(e) =>
                                        Object.assign(
                                          e.target.style,
                                          inputFocusStyle
                                        )
                                      }
                                      onBlur={(e) =>
                                        Object.assign(
                                          e.target.style,
                                          inputStyle
                                        )
                                      }
                                    />
                                  </div>
                                </div>
                                <button
                                  className="remove-item-btn"
                                  style={{
                                    ...removeBtnStyle,
                                    top: 18,
                                    right: 18,
                                    background: "#fff",
                                    border: "1.5px solid #ef4444",
                                    color: "#ef4444",
                                    borderRadius: 8,
                                    padding: 6,
                                    zIndex: 2,
                                  }}
                                  onClick={() => {
                                    const newValue = fieldValue.filter(
                                      (_, i) => i !== index
                                    );
                                    handleFormChange(fieldName, newValue);
                                  }}
                                  title="Remove Project"
                                >
                                  <Trash2 />
                                </button>
                              </div>
                            ))}
                            <button
                              className="add-item-btn"
                              style={{
                                ...addBtnStyle,
                                marginTop: 8,
                                boxShadow: "0 2px 8px rgba(56,189,248,0.13)",
                                background: "#d1fae5",
                                color: "#059669",
                                border: "1.5px solid #059669",
                              }}
                              onClick={() => {
                                const newValue = [
                                  ...fieldValue,
                                  { name: "", description: "", github: "" },
                                ];
                                handleFormChange(fieldName, newValue);
                              }}
                            >
                              <PlusCircle /> Add Project
                            </button>
                          </div>
                        ) : Array.isArray(fieldValue) ? (
                          <div className={`array-edit ${
                            fieldName === "skills" ? "skills-array" : ""
                          }`}>
                            {fieldValue.map((item, index) => (
                              <div
                                key={index}
                                className={`array-item-edit ${
                                  fieldName === "skills" ? "skill-item" : ""
                                }`}
                                style={{
                                  background: fieldName === "skills" ? "#ffffff" : "#f3f8fd",
                                  borderRadius: fieldName === "skills" ? 8 : 10,
                                  padding: fieldName === "skills" ? "1rem" : 12,
                                  marginBottom: fieldName === "skills" ? 0 : 10,
                                  border: fieldName === "skills" ? "1px solid #e5e7eb" : "none",
                                  position: fieldName === "skills" ? "relative" : "static",
                                }}
                              >
                                {fieldName === "skills" ? (
                                  <input
                                    type="text"
                                    value={item}
                                    onChange={(e) => {
                                      const newValue = [...fieldValue];
                                      newValue[index] = e.target.value;
                                      handleFormChange(fieldName, newValue);
                                    }}
                                    placeholder="Enter skill"
                                    className="field-input"
                                    style={{
                                      minHeight: 40,
                                      textAlign: "center",
                                      fontSize: "0.875rem",
                                    }}
                                  />
                                ) : (
                                  <>
                                    <label style={labelStyle}>Item</label>
                                    <textarea
                                      value={
                                        typeof item === "object"
                                          ? JSON.stringify(item, null, 2)
                                          : item
                                      }
                                      onChange={(e) => {
                                        const newValue = [...fieldValue];
                                        try {
                                          newValue[index] = JSON.parse(
                                            e.target.value
                                          );
                                        } catch {
                                          newValue[index] = e.target.value;
                                        }
                                        handleFormChange(fieldName, newValue);
                                      }}
                                      placeholder={`Enter ${formatFieldName(
                                        fieldName
                                      ).toLowerCase()}`}
                                      style={{
                                        ...inputStyle,
                                        minHeight: 50,
                                        resize: "vertical",
                                        fontFamily: "inherit",
                                      }}
                                      onFocus={(e) =>
                                        Object.assign(e.target.style, {
                                          ...inputFocusStyle,
                                          minHeight: 70,
                                        })
                                      }
                                      onBlur={(e) =>
                                        Object.assign(e.target.style, {
                                          ...inputStyle,
                                          minHeight: 50,
                                        })
                                      }
                                    />
                                  </>
                                )}
                                {fieldName === "skills" ? (
                                  <button
                                    className="remove-item-btn"
                                    onClick={() => {
                                      const newValue = fieldValue.filter(
                                        (_, i) => i !== index
                                      );
                                      handleFormChange(fieldName, newValue);
                                    }}
                                    title="Remove skill"
                                  >
                                    <Trash2 />
                                  </button>
                                ) : (
                                  <button
                                    className="remove-item-btn"
                                    style={removeBtnStyle}
                                    onClick={() => {
                                      const newValue = fieldValue.filter(
                                        (_, i) => i !== index
                                      );
                                      handleFormChange(fieldName, newValue);
                                    }}
                                  >
                                    <Trash2 />
                                  </button>
                                )}
                              </div>
                            ))}
                            <button
                              className="add-item-btn"
                              style={{
                                ...addBtnStyle,
                                background: fieldName === "skills" ? "#dbeafe" : addBtnStyle.background,
                                color: fieldName === "skills" ? "#1d4ed8" : addBtnStyle.color,
                                border: fieldName === "skills" ? "1.5px solid #1d4ed8" : addBtnStyle.border,
                              }}
                              onClick={() => {
                                const newValue = [...fieldValue, ""];
                                handleFormChange(fieldName, newValue);
                              }}
                            >
                              <PlusCircle /> {fieldName === "skills" ? "Add Skill" : "Add Item"}
                            </button>
                          </div>
                        ) : (
                          <>
                            <label style={labelStyle}>Value</label>
                            <textarea
                              value={
                                typeof fieldValue === "object"
                                  ? JSON.stringify(fieldValue, null, 2)
                                  : fieldValue
                              }
                              onChange={(e) => {
                                try {
                                  const parsed = JSON.parse(e.target.value);
                                  handleFormChange(fieldName, parsed);
                                } catch {
                                  handleFormChange(fieldName, e.target.value);
                                }
                              }}
                              placeholder={`Enter ${formatFieldName(
                                fieldName
                              ).toLowerCase()}`}
                              style={{
                                ...inputStyle,
                                minHeight: 50,
                                resize: "vertical",
                                fontFamily: "inherit",
                              }}
                              onFocus={(e) =>
                                Object.assign(e.target.style, {
                                  ...inputFocusStyle,
                                  minHeight: 70,
                                })
                              }
                              onBlur={(e) =>
                                Object.assign(e.target.style, {
                                  ...inputStyle,
                                  minHeight: 50,
                                })
                              }
                            />
                          </>
                        )}
                      </div>
                    ) : (
                      <div
                        className="view-mode"
                        style={{
                          fontSize: "1.07rem",
                          color: "#232946",
                          fontWeight: 500,
                          marginTop: 2,
                        }}
                      >
                        {/* Special handling for projects array */}
                        {fieldName === "projects" &&
                        Array.isArray(fieldValue) ? (
                          <div className="array-field">
                            {fieldValue.map((item, index) => (
                              <div
                                key={index}
                                className="object-item"
                                style={projectCardStyle}
                              >
                                <div>
                                  <strong>{item.name}</strong>
                                </div>
                                <div>{item.description}</div>
                                {item.github && (
                                  <div>
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
                                      <Github
                                        style={{ width: 18, height: 18 }}
                                      />{" "}
                                      GitHub
                                    </a>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          renderFieldValue(fieldName, fieldValue)
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}


          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="profile-completion-container" ref={containerRef}>
      {/* Toast Notifications */}
      {error && (
        <div className="toast error-toast">
          <AlertCircle className="toast-icon" />
          <span>{error}</span>
          <button onClick={() => setError("")}>×</button>
        </div>
      )}

      {success && (
        <div className="toast success-toast">
          <CheckCircle className="toast-icon" />
          <span>{success}</span>
          <button onClick={() => setSuccess("")}>×</button>
        </div>
      )}

      {/* Header Section - Using StaticHeader */}
      <StaticHeader showSignIn={false} showSignUp={false} />

      {/* Main Content Area */}
      <div className="main-content">
        {loadingExistingProfile ? (
          <div className="view-container">
            <div className="content-wrapper">
              <div className="upload-container">
                <h1 className="page-title">Loading Profile...</h1>
                <p className="page-subtitle">
                  Please wait while we load your profile information...
                </p>
              </div>
              <div className="loading-spinner" />
            </div>
          </div>
        ) : currentView === 0 ? (
          renderUploadView()
        ) : (
          renderProfileForm()
        )}

        {/* Floating Save Button */}
        {currentView === 1 && (
          <div className="floating-save-button">
            <button
              className="save-btn primary-btn floating"
              onClick={handleSaveOrUpdateProfile}
              disabled={parsing}
              title={userProfile?.profileCompleted ? "Update Profile" : "Save & Complete Profile"}
            >
              {parsing ? (
                <>
                  <Loader2 className="loading-spinner" />
                  {userProfile?.profileCompleted
                    ? "Updating..."
                    : "Saving..."}
                </>
              ) : (
                <>
                  <Save className="btn-icon" />
                  {userProfile?.profileCompleted
                    ? "Update Profile"
                    : "Save & Complete Profile"}
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileCompletion;
