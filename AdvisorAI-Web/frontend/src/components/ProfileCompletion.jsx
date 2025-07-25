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
  Brain,
  Zap,
  ArrowLeft,
  ArrowRight,
  Settings,
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
  Loader2
} from "lucide-react";
import "./ProfileCompletion.css";

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
  const [extractionDebug, setExtractionDebug] = useState(null);
  const [showFeatures, setShowFeatures] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [formData, setFormData] = useState({});
  const [uploadStep, setUploadStep] = useState(0); // 0: Select, 1: Processing, 2: Complete
  const [loadingExistingProfile, setLoadingExistingProfile] = useState(false);
  
  const fileInputRef = useRef();
  const containerRef = useRef();
  const { currentUser, markProfileCompleted, isProfileCompleted } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Show features after a delay
    setTimeout(() => setShowFeatures(true), 1000);
  }, []);

  // Update form data when parsed data changes
  useEffect(() => {
    if (parsedData && parsedData.data) {
      setFormData(parsedData.data);
    }
  }, [parsedData]);

  // Load existing profile data if editing
  useEffect(() => {
    const loadExistingProfile = async () => {
      console.log('ProfileCompletion: Checking profile completion status...');
      console.log('ProfileCompletion: isProfileCompleted():', isProfileCompleted());
      console.log('ProfileCompletion: currentUser.profileCompleted:', currentUser?.profileCompleted);
      console.log('ProfileCompletion: localStorage profileCompleted:', localStorage.getItem('profileCompleted'));
      
      if (isProfileCompleted() && !parsedData) {
        console.log('ProfileCompletion: Profile is completed, loading existing data...');
        try {
          setLoadingExistingProfile(true);
          const response = await apiService.getUserProfile();
          console.log('ProfileCompletion: Profile response:', response);
          
          if (response.success && response.profile && Object.keys(response.profile).length > 0) {
            console.log('ProfileCompletion: Existing profile data found, showing edit mode');
            setFormData(response.profile);
            setCurrentView(1); // Go directly to form view
            setSuccess("Profile loaded successfully! You can now edit your information.");
            setTimeout(() => setSuccess(""), 3000);
          } else {
            // No profile data found, but localStorage says it's completed
            console.log('ProfileCompletion: No profile data found but localStorage says completed, clearing localStorage');
            localStorage.removeItem('profileCompleted');
            setCurrentView(0);
          }
        } catch (error) {
          console.error('ProfileCompletion: Failed to load existing profile:', error);
          // On error, clear localStorage and show upload view
          localStorage.removeItem('profileCompleted');
          setCurrentView(0);
        } finally {
          setLoadingExistingProfile(false);
        }
      } else if (isProfileCompleted()) {
        console.log('ProfileCompletion: Profile is completed, redirecting to dashboard...');
        // If profile is completed and we're not editing, redirect to dashboard
        navigate('/dashboard');
      } else {
        console.log('ProfileCompletion: Profile not completed, showing upload view');
        setCurrentView(0);
      }
    };

    loadExistingProfile();
  }, [isProfileCompleted, parsedData, currentUser, navigate]);

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
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    
    if (!allowedTypes.includes(selectedFile.type)) {
      setError("Please select a valid file type (PDF, DOC, or DOCX)");
      return;
    }
    
    if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
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
      
      const formData = new FormData();
      formData.append('resume', file);
      formData.append('userId', currentUser.uid);
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);
      
      const response = await apiService.uploadAndParseResume(formData);
      
      clearInterval(progressInterval);
      setProgress(100);
      setUploadStep(2);
      
      if (response.success && response.data) {
        console.log("✅ Resume parsed successfully:", response.data);
        setParsedData(response);
        setSuccess("Resume parsed successfully! Moving to profile form...");
        
        setTimeout(() => {
          setCurrentView(1);
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
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSaveProfile = async () => {
    try {
      setParsing(true);
      setError("");
      
      const response = await apiService.saveUserProfile(formData);
      
      // Mark profile as completed
      markProfileCompleted();
      
      setSuccess("Profile completed successfully! Redirecting to dashboard...");
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
      
    } catch (error) {
      setError(`Save failed: ${error.message}`);
    } finally {
      setParsing(false);
    }
  };

  const handleUpdateProfile = async () => {
    try {
      setParsing(true);
      setError("");
      
      const response = await apiService.saveUserProfile(formData);
      
      setSuccess("Profile updated successfully!");
      
      setTimeout(() => {
        setSuccess("");
      }, 3000);
      
    } catch (error) {
      setError(`Update failed: ${error.message}`);
    } finally {
      setParsing(false);
    }
  };

  // Debug function to fix profile completion status
  const handleFixProfileCompletion = async () => {
    try {
      setError("");
      const response = await fetch('/api/admin/fix-profile-completion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('backendToken')}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuccess(`Profile completion status: ${data.message}`);
        // Update localStorage
        localStorage.setItem('profileCompleted', data.profileCompleted ? 'true' : 'false');
        setTimeout(() => {
          setSuccess("");
        }, 3000);
      } else {
        setError(`Fix failed: ${data.error}`);
      }
    } catch (error) {
      setError(`Fix failed: ${error.message}`);
    }
  };

  const debugExtraction = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    try {
      setUploading(true);
      setError("");
      
      const formData = new FormData();
      formData.append('resume', file);
      formData.append('userId', currentUser.uid);
      
      const response = await apiService.debugTextExtraction(formData);
      setExtractionDebug(response);
      
    } catch (error) {
      setError(`Debug failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const features = [
    {
      icon: <Brain className="feature-icon" />,
      title: "AI-Powered Extraction",
      description: "Advanced LLM technology extracts all your information with 95% accuracy"
    },
    {
      icon: <Zap className="feature-icon" />,
      title: "Lightning Fast",
      description: "Process your resume in seconds with our optimized AI pipeline"
    },
    {
      icon: <Shield className="feature-icon" />,
      title: "Secure & Private",
      description: "Your data is encrypted and never shared with third parties"
    },
    {
      icon: <Target className="feature-icon" />,
      title: "Smart Recognition",
      description: "Intelligently identifies and categorizes all resume sections"
    }
  ];

  const stats = [
    { number: "10K+", label: "Resumes Processed", icon: <FileText /> },
    { number: "95%", label: "Accuracy Rate", icon: <CheckSquare /> },
    { number: "< 30s", label: "Average Time", icon: <Clock /> },
    { number: "24/7", label: "AI Available", icon: <Users /> }
  ];

  // Helper function to format field names
  const formatFieldName = (fieldName) => {
    return fieldName
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
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
      projects: <Target />
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
              {typeof item === 'object' && item !== null ? (
                <div className="object-item">
                  {Object.entries(item).map(([key, val]) => (
                    <div key={key} className="object-field">
                      <span className="field-label">{formatFieldName(key)}:</span>
                      <span className="field-value">{String(val || 'Not specified')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="field-value">{String(item || 'Not specified')}</span>
              )}
            </div>
          ))}
        </div>
      );
    }
    
    if (typeof value === 'object' && value !== null) {
      return (
        <div className="object-field">
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="nested-field">
              <span className="field-label">{formatFieldName(key)}:</span>
              <span className="field-value">{String(val || 'Not specified')}</span>
            </div>
          ))}
        </div>
      );
    }
    
    return <span className="field-value">{String(value || 'Not specified')}</span>;
  };

  const renderUploadView = () => (
    <div className="view-container upload-view">
      {/* Enhanced Animated Background */}
      <div className="animated-background">
        <div className="floating-particles">
          {[...Array(30)].map((_, i) => (
            <div key={i} className="particle" style={{
              '--delay': `${Math.random() * 4}s`,
              '--duration': `${3 + Math.random() * 4}s`,
              '--x': `${Math.random() * 100}%`,
              '--y': `${Math.random() * 100}%`,
              '--size': `${2 + Math.random() * 4}px`
            }} />
          ))}
        </div>
        <div className="gradient-overlay" />
      </div>

      <div className="content-wrapper">
        {/* Enhanced Header */}
        <div className="header-section">
          <div className="logo-container">
            <div className="logo-glow">
              <Brain className="logo-icon" />
            </div>
            <div className="logo-text">
              <h1>Advisor<span className="logo-highlight">AI</span></h1>
              <div className="logo-badge">
                <Sparkles className="badge-icon" />
                <span>AI-Powered Resume Parser</span>
              </div>
            </div>
          </div>
          <p className="subtitle">Transform your resume into a comprehensive digital profile with advanced AI</p>
        </div>

        {/* Stats Section */}
        <div className={`stats-section ${showFeatures ? 'show' : ''}`}>
          {stats.map((stat, index) => (
            <div key={index} className="stat-card" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="stat-icon">{stat.icon}</div>
              <div className="stat-number">{stat.number}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>

        <div className="upload-container">
          {/* Enhanced Upload Card */}
          <div className="upload-card">
            <div className="card-header">
              <div className="header-icon">
                <div className="icon-glow">
                  <Sparkles className="sparkle-icon" />
                </div>
              </div>
              <h2>{isProfileCompleted() ? 'Update Your Resume' : 'Upload Your Resume'}</h2>
              <p>
                {isProfileCompleted() 
                  ? 'Upload a new resume to update your profile information with the latest data'
                  : 'Drop your resume and let our advanced AI extract everything automatically'
                }
              </p>
            </div>

            <div 
              className={`upload-area ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''} step-${uploadStep}`}
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
              style={{ display: 'none' }}
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
                    {uploading ? 'Processing your resume with AI...' : 'Ready to upload'}
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
                      Processing with AI...
                    </>
                  ) : (
                    <>
                      <Rocket className="btn-icon" />
                      {isProfileCompleted() ? 'Update Resume with AI' : 'Parse Resume with AI'}
                    </>
                  )}
              </button>

              <button 
                className="debug-btn secondary-btn"
                onClick={debugExtraction}
                disabled={!file || uploading}
              >
                <Settings className="btn-icon" />
                Debug Extraction
              </button>
            </div>

            {extractionDebug && (
              <div className="debug-panel">
                <h4>
                  <Eye className="debug-icon" />
                  Debug Information
                </h4>
                <details>
                  <summary>Extraction Results</summary>
                  <pre>{JSON.stringify(extractionDebug, null, 2)}</pre>
                </details>
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div className={`features-section ${showFeatures ? 'show' : ''}`}>
          <h3>Why Choose Our AI-Powered Solution?</h3>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="feature-icon-container">
                  {feature.icon}
                </div>
                <h4>{feature.title}</h4>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderProfileForm = () => (
    <div className="view-container profile-form-view">
      {/* Enhanced Animated Background */}
      <div className="animated-background">
        <div className="floating-particles">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="particle" style={{
              '--delay': `${Math.random() * 3}s`,
              '--duration': `${2 + Math.random() * 3}s`,
              '--x': `${Math.random() * 100}%`,
              '--y': `${Math.random() * 100}%`,
              '--size': `${2 + Math.random() * 3}px`
            }} />
          ))}
        </div>
        <div className="gradient-overlay" />
      </div>

      <div className="content-wrapper">
        {/* Enhanced Header */}
        <div className="header-section">
          <div className="logo-container">
            <div className="logo-glow">
              <User className="logo-icon" />
            </div>
            <div className="logo-text">
              <h1>Profile Information</h1>
              <div className="logo-badge">
                <CheckSquare className="badge-icon" />
                <span>Review & Edit Your Data</span>
              </div>
            </div>
          </div>
          <p className="subtitle">Review and edit the information extracted from your resume by our AI</p>
        </div>

        <div className="profile-form-container">
          <div className="form-header">
            <div className="form-info">
              <h2>{isProfileCompleted() ? 'Edit Profile Information' : 'Extracted Information'}</h2>
              <p>
                {isProfileCompleted() 
                  ? 'Update your profile information. All changes will be saved automatically.'
                  : 'All fields have been automatically filled from your resume using advanced AI. You can edit any field by clicking on it.'
                }
              </p>
            </div>
            
            <div className="form-actions">
              {!isProfileCompleted() && (
                <button 
                  className="back-btn secondary-btn"
                  onClick={() => setCurrentView(0)}
                >
                  <ArrowLeft className="btn-icon" />
                  Back to Upload
                </button>
              )}
              
              <button 
                className="save-btn primary-btn"
                onClick={isProfileCompleted() ? handleUpdateProfile : handleSaveProfile}
                disabled={parsing}
              >
                {parsing ? (
                  <>
                    <Loader2 className="loading-spinner" />
                    {isProfileCompleted() ? 'Updating...' : 'Saving...'}
                  </>
                ) : (
                  <>
                    <Save className="btn-icon" />
                    {isProfileCompleted() ? 'Update Profile' : 'Save Profile'}
                  </>
                )}
              </button>
              
              {/* Debug button for profile completion status */}
              <button 
                className="debug-btn secondary-btn"
                onClick={handleFixProfileCompletion}
                title="Fix profile completion status"
              >
                <Settings className="btn-icon" />
                Fix Profile Status
              </button>
            </div>
          </div>

          <div className="form-content">
            {Object.entries(formData)
              .filter(([fieldName]) => !['resume-data', 'resume-text'].includes(fieldName))
              .map(([fieldName, fieldValue]) => (
              <div key={fieldName} className="form-field">
                <div className="field-header">
                  <div className="field-icon">
                    {getFieldIcon(fieldName)}
                  </div>
                  <h3 className="field-title">{formatFieldName(fieldName)}</h3>
                  <button 
                    className="edit-btn"
                    onClick={() => setEditingField(editingField === fieldName ? null : fieldName)}
                    title="Edit field"
                  >
                    {editingField === fieldName ? <EyeOff /> : <Edit />}
                  </button>
                </div>
                
                <div className="field-content">
                  {editingField === fieldName ? (
                    <div className="edit-mode">
                      {Array.isArray(fieldValue) ? (
                        <div className="array-edit">
                          {fieldValue.map((item, index) => (
                            <div key={index} className="array-item-edit">
                              <textarea
                                value={typeof item === 'object' ? JSON.stringify(item, null, 2) : item}
                                onChange={(e) => {
                                  const newValue = [...fieldValue];
                                  try {
                                    newValue[index] = JSON.parse(e.target.value);
                                  } catch {
                                    newValue[index] = e.target.value;
                                  }
                                  handleFormChange(fieldName, newValue);
                                }}
                                placeholder={`Enter ${formatFieldName(fieldName).toLowerCase()}`}
                              />
                              <button 
                                className="remove-item-btn"
                                onClick={() => {
                                  const newValue = fieldValue.filter((_, i) => i !== index);
                                  handleFormChange(fieldName, newValue);
                                }}
                              >
                                <Trash2 />
                              </button>
                            </div>
                          ))}
                          <button 
                            className="add-item-btn"
                            onClick={() => {
                              const newValue = [...fieldValue, ''];
                              handleFormChange(fieldName, newValue);
                            }}
                          >
                            <PlusCircle />
                            Add Item
                          </button>
                        </div>
                      ) : (
                        <textarea
                          value={typeof fieldValue === 'object' ? JSON.stringify(fieldValue, null, 2) : fieldValue}
                          onChange={(e) => {
                            try {
                              const parsed = JSON.parse(e.target.value);
                              handleFormChange(fieldName, parsed);
                            } catch {
                              handleFormChange(fieldName, e.target.value);
                            }
                          }}
                          placeholder={`Enter ${formatFieldName(fieldName).toLowerCase()}`}
                        />
                      )}
                    </div>
                  ) : (
                    <div className="view-mode">
                      {renderFieldValue(fieldName, fieldValue)}
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

      {/* Main Content */}
      <div className="main-content">
        {loadingExistingProfile ? (
          // Show loading while fetching existing profile
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading your profile...</p>
          </div>
        ) : currentView === 0 ? (
          renderUploadView()
        ) : (
          renderProfileForm()
        )}
      </div>

      {/* Floating Action Button */}
      <button 
        className="fab"
        onClick={() => navigate('/dashboard')}
        title="Go to Dashboard"
      >
        <Home />
      </button>
    </div>
  );
};

export default ProfileCompletion;