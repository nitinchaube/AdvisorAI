import React, { useState, useEffect } from "react";
import PageLayout from "./PageLayout";
import { adminAPI } from "../services/api";
import {
  BookOpen,
  Users,
  Plus,
  Edit2,
  Trash2,
  Search,
  Filter,
  Save,
  X,
  ChevronDown,
  AlertTriangle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Briefcase,
  Clock,
  Zap,
} from "lucide-react";

const AdminDashboard = () => {
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);

  // Admin specific state
  const [activeTab, setActiveTab] = useState("courses");
  const [courses, setCourses] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("add"); // 'add' or 'edit'
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [selectedUserForRole, setSelectedUserForRole] = useState(null);
  const [notification, setNotification] = useState({
    show: false,
    message: "",
    type: "",
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  // Scraper state
  const [scraperStatus, setScraperStatus] = useState(null);
  const [scraperRunning, setScraperRunning] = useState(false);

  // Handler for menu toggle
  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  // Fetch scraper status on mount and every 30s
  useEffect(() => {
    const fetchScraperStatus = async () => {
      try {
        const res = await adminAPI.getScraperStatus();
        setScraperStatus(res.scraper);
      } catch {
        // silently ignore — non-critical
      }
    };
    fetchScraperStatus();
    const interval = setInterval(fetchScraperStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScraper = async () => {
    try {
      setScraperRunning(true);
      await adminAPI.triggerScraper();
      showNotification("Job scraper started! It will run in the background.", "success");
      // Poll status a few times to get the updated result
      setTimeout(async () => {
        try {
          const res = await adminAPI.getScraperStatus();
          setScraperStatus(res.scraper);
        } catch {}
        setScraperRunning(false);
      }, 5000);
    } catch (error) {
      showNotification("Failed to trigger scraper: " + error.message, "error");
      setScraperRunning(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "courses") {
        const response = await adminAPI.getAllCourses();
        setCourses(response.courses || []);
      } else if (activeTab === "faculty") {
        const response = await adminAPI.getAllFaculty();
        setFaculty(response.faculty || []);
      } else if (activeTab === "users") {
        const response = await adminAPI.getAllUsers();
        setUsers(response.users || []);
      }
    } catch (error) {
      showNotification("Failed to load data: " + error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(
      () => setNotification({ show: false, message: "", type: "" }),
      3000
    );
  };

  const handleAdd = () => {
    setModalType("add");
    setSelectedItem(null);
    setFormData(
      activeTab === "courses"
        ? {
            "Course Code": "",
            "Course Title": "",
            "Course Description": "",
            Credits: "",
            Prerequisites: "",
            Department: "",
            Level: "",
          }
        : activeTab === "faculty"
        ? {
            "Full Name": "",
            Email: "",
            Department: "",
            Title: "",
            Office: "",
            Phone: "",
            "Research Interests": "",
            Bio: "",
          }
        : {
            fullName: "",
            email: "",
            role: "user", // Default role for new users
          }
    );
    setShowModal(true);
  };

  const handleEdit = (item) => {
    setModalType("edit");
    setSelectedItem(item);
    setFormData({ ...item });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;

    try {
      if (activeTab === "courses") {
        await adminAPI.deleteCourse(id);
        setCourses(courses.filter((c) => c.id !== id));
      } else if (activeTab === "faculty") {
        await adminAPI.deleteFaculty(id);
        setFaculty(faculty.filter((f) => f.id !== id));
      } else if (activeTab === "users") {
        await adminAPI.deleteUser(id);
        setUsers(users.filter((u) => u.uid !== id));
      }
      showNotification("Item deleted successfully", "success");
    } catch (error) {
      showNotification("Failed to delete item: " + error.message, "error");
    }
  };

  const handleRoleToggle = async (userUid, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const confirmMessage = `Are you sure you want to change this user's role from ${currentRole} to ${newRole}?`;
    
    if (!window.confirm(confirmMessage)) return;

    try {
      await adminAPI.updateUserRole(userUid, newRole);
      await loadData();
      showNotification(`User role updated to ${newRole} successfully`, "success");
    } catch (error) {
      showNotification("Failed to update user role: " + error.message, "error");
    }
  };

  const openRoleModal = (user) => {
    setSelectedUserForRole(user);
    setShowRoleModal(true);
  };

  const handleRoleChange = async () => {
    if (!selectedUserForRole) return;
    
    const newRole = selectedUserForRole.role === 'admin' ? 'user' : 'admin';
    
    try {
      await adminAPI.updateUserRole(selectedUserForRole.uid, newRole);
      await loadData();
      setShowRoleModal(false);
      setSelectedUserForRole(null);
      showNotification(`User role updated to ${newRole} successfully`, "success");
    } catch (error) {
      showNotification("Failed to update user role: " + error.message, "error");
    }
  };

  const handleSave = async () => {
    try {
      if (activeTab === "courses") {
        if (modalType === "add") {
          const response = await adminAPI.addCourse(formData);
          await loadData();
        } else {
          await adminAPI.updateCourse(selectedItem.id, formData);
          await loadData();
        }
      } else if (activeTab === "faculty") {
        if (modalType === "add") {
          const response = await adminAPI.addFaculty(formData);
          await loadData();
        } else {
          await adminAPI.updateFaculty(selectedItem.id, formData);
          await loadData();
        }
      } else if (activeTab === "users") {
        if (modalType === "add") {
          // For users, we can only edit existing users, not create new ones
          showNotification("Cannot create new users from admin panel. Users must register through the application.", "error");
          return;
        } else {
          // Update user information
          const updateData = {
            fullName: formData["Full Name"],
            email: formData["Email"],
            role: formData["Role"]
          };
          await adminAPI.updateUser(selectedItem.uid, updateData);
          await loadData();
        }
      }
      setShowModal(false);
      showNotification(
        `${modalType === "add" ? "Added" : "Updated"} successfully`,
        "success"
      );
    } catch (error) {
      showNotification(`Failed to ${modalType}: ` + error.message, "error");
    }
  };

  // Filter data based on search term (search across ALL records)
  const allFilteredData =
    activeTab === "courses"
      ? courses.filter(
          (course) =>
            (course["Course Code"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (course["Course Title"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (course["Department"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase())
        )
      : activeTab === "faculty"
      ? faculty.filter(
          (member) =>
            (member["Full Name"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (member["Department"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (member["Email"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase())
        )
      : users.filter(
          (user) =>
            (user["fullName"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (user["email"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            (user["role"] || "")
              .toLowerCase()
              .includes(searchTerm.toLowerCase())
        );

  // Calculate pagination
  const totalItems = allFilteredData.length;
  const totalPagesCalculated = Math.ceil(totalItems / itemsPerPage);

  // Update total pages when data changes
  React.useEffect(() => {
    setTotalPages(totalPagesCalculated);
    // Reset to page 1 if current page is beyond total pages
    if (currentPage > totalPagesCalculated && totalPagesCalculated > 0) {
      setCurrentPage(1);
    }
  }, [totalPagesCalculated, currentPage]);

  // Reset current page when switching tabs or changing search
  React.useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, searchTerm]);

  // Get paginated data
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedData = allFilteredData.slice(startIndex, endIndex);

  const renderCourseForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Course Code
          </label>
          <input
            type="text"
            value={formData["Course Code"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, "Course Code": e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., CS 513"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Credits
          </label>
          <input
            type="text"
            value={formData["Credits"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Credits: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., 3"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Course Title
        </label>
        <input
          type="text"
          value={formData["Course Title"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Course Title": e.target.value })
          }
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
          placeholder="e.g., Data Structures and Algorithms"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Course Description
        </label>
        <textarea
          value={formData["Course Description"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Course Description": e.target.value })
          }
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md resize-none"
          rows="4"
          placeholder="Course description..."
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Department
          </label>
          <input
            type="text"
            value={formData["Department"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Department: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., Computer Science"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Level
          </label>
          <select
            value={formData["Level"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Level: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
          >
            <option value="">Select Level</option>
            <option value="Undergraduate">Undergraduate</option>
            <option value="Graduate">Graduate</option>
            <option value="PhD">PhD</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Prerequisites
        </label>
        <input
          type="text"
          value={formData["Prerequisites"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, Prerequisites: e.target.value })
          }
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
          placeholder="e.g., CS 115, CS 284"
        />
      </div>
    </div>
  );

  const renderFacultyForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Full Name
          </label>
          <input
            type="text"
            value={formData["Full Name"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, "Full Name": e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., Dr. John Smith"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Email
          </label>
          <input
            type="email"
            value={formData["Email"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Email: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="professor@stevens.edu"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Department
          </label>
          <input
            type="text"
            value={formData["Department"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Department: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., Computer Science"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Title
          </label>
          <input
            type="text"
            value={formData["Title"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Title: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., Professor, Associate Professor"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Office
          </label>
          <input
            type="text"
            value={formData["Office"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Office: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., Room 123, Building A"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Phone
          </label>
          <input
            type="text"
            value={formData["Phone"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Phone: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., (201) 555-0123"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Research Interests
        </label>
        <textarea
          value={formData["Research Interests"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Research Interests": e.target.value })
          }
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md resize-none"
          rows="3"
          placeholder="Research areas and interests..."
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Bio
        </label>
        <textarea
          value={formData["Bio"] || ""}
          onChange={(e) => setFormData({ ...formData, Bio: e.target.value })}
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md resize-none"
          rows="4"
          placeholder="Faculty biography..."
        />
      </div>
    </div>
  );

  const renderUserForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Full Name
          </label>
          <input
            type="text"
            value={formData["fullName"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, fullName: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="e.g., John Doe"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Email
          </label>
          <input
            type="email"
            value={formData["email"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
            placeholder="user@example.com"
          />
        </div>
      </div>
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Role
        </label>
        <select
          value={formData["role"] || "user"}
          onChange={(e) =>
            setFormData({ ...formData, role: e.target.value })
          }
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300 bg-white shadow-sm hover:shadow-md"
        >
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
    </div>
  );

  // Render admin content similar to Dashboard's renderContent
  const renderAdminContent = () => {
    return (
      <div className="h-full w-full overflow-hidden">
        {/* Admin Content Container */}
        <div className="h-full bg-white/90 backdrop-blur-sm overflow-y-auto">
          {/* Job Scraper Card */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/60 rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="bg-amber-100 p-3 rounded-xl">
                  <Briefcase className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-800 text-sm">Jobs & Internships Scraper</h3>
                  {scraperStatus ? (
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <span className={`inline-block w-2 h-2 rounded-full ${
                          scraperStatus.last_status?.includes("success") ? "bg-green-500" :
                          scraperStatus.last_status?.includes("error") ? "bg-red-500" : "bg-slate-400"
                        }`} />
                        {scraperStatus.last_status || "idle"}
                      </span>
                      {scraperStatus.last_run && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Last: {new Date(scraperStatus.last_run).toLocaleString()}
                        </span>
                      )}
                      <span>Runs: {scraperStatus.runs || 0}</span>
                      <span>Every {scraperStatus.interval_hours || 2}h</span>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 mt-1">Loading status…</p>
                  )}
                  {scraperStatus?.last_error && (
                    <p className="text-xs text-red-500 mt-1 truncate max-w-md">{scraperStatus.last_error}</p>
                  )}
                </div>
              </div>
              <button
                onClick={handleTriggerScraper}
                disabled={scraperRunning}
                className={`flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-sm transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105 ${
                  scraperRunning
                    ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                    : "bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-600 hover:to-orange-600"
                }`}
              >
                {scraperRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Running…
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Run Scraper Now
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
            <div className="bg-gradient-to-r from-slate-800/95 to-slate-700/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-600/20 p-2">
              <nav className="flex space-x-2">
                <button
                  onClick={() => setActiveTab("courses")}
                  className={`flex-1 flex items-center justify-center px-6 py-4 rounded-2xl font-medium text-sm transition-all duration-300 transform hover:scale-105 ${
                    activeTab === "courses"
                      ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg"
                      : "text-slate-300 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <BookOpen className="w-5 h-5 mr-3" />
                  <span className="font-semibold">Courses</span>
                  <span
                    className={`ml-3 py-1 px-3 rounded-full text-xs font-bold ${
                      activeTab === "courses"
                        ? "bg-white/20 text-white"
                        : "bg-slate-600/50 text-slate-300"
                    }`}
                  >
                    {courses.length}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab("faculty")}
                  className={`flex-1 flex items-center justify-center px-6 py-4 rounded-2xl font-medium text-sm transition-all duration-300 transform hover:scale-105 ${
                    activeTab === "faculty"
                      ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg"
                      : "text-slate-300 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Users className="w-5 h-5 mr-3" />
                  <span className="font-semibold">Faculty</span>
                  <span
                    className={`ml-3 py-1 px-3 rounded-full text-xs font-bold ${
                      activeTab === "faculty"
                        ? "bg-white/20 text-white"
                        : "bg-slate-600/50 text-slate-300"
                    }`}
                  >
                    {faculty.length}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab("users")}
                  className={`flex-1 flex items-center justify-center px-6 py-4 rounded-2xl font-medium text-sm transition-all duration-300 transform hover:scale-105 ${
                    activeTab === "users"
                      ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg"
                      : "text-slate-300 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Users className="w-5 h-5 mr-3" />
                  <span className="font-semibold">Users</span>
                  <span
                    className={`ml-3 py-1 px-3 rounded-full text-xs font-bold ${
                      activeTab === "users"
                        ? "bg-white/20 text-white"
                        : "bg-slate-600/50 text-slate-300"
                    }`}
                  >
                    {users.length}
                  </span>
                </button>
              </nav>
            </div>

            {/* Search and Add */}
            <div className="mt-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder={`Search ${activeTab}...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-12 pr-6 py-4 bg-white/90 backdrop-blur-sm border border-slate-200/60 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 w-full sm:w-96 shadow-lg hover:shadow-xl transition-all duration-300 text-slate-700 placeholder-slate-400"
                />
              </div>
              {activeTab === "users" ? (
                <div className="flex items-center space-x-3">
                  <div className="text-sm text-slate-600 bg-slate-100 px-4 py-2 rounded-xl">
                    <span className="font-medium">Total Users:</span> {users.length} | 
                    <span className="font-medium ml-2">Admins:</span> {users.filter(u => u.role === 'admin').length} | 
                    <span className="font-medium ml-2">Regular:</span> {users.filter(u => u.role === 'user').length}
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        setLoading(true);
                        const result = await adminAPI.syncFirebaseClaims();
                        showNotification(`Firebase claims synced: ${result.synced_count} users updated`, "success");
                        await loadData(); // Refresh user data
                      } catch (error) {
                        showNotification("Failed to sync Firebase claims: " + error.message, "error");
                      } finally {
                        setLoading(false);
                      }
                    }}
                    className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-4 rounded-2xl hover:from-green-600 hover:to-emerald-700 flex items-center justify-center whitespace-nowrap font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-green-300/30"
                    title="Sync Firebase custom claims with MongoDB roles"
                  >
                    <CheckCircle className="w-5 h-5 mr-3" />
                    Sync Firebase
                  </button>
                  <button
                    onClick={() => setActiveTab("courses")}
                    className="bg-gradient-to-r from-slate-500 to-slate-600 text-white px-6 py-4 rounded-2xl hover:from-slate-600 hover:to-slate-700 flex items-center justify-center whitespace-nowrap font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-slate-300/30"
                  >
                    <BookOpen className="w-5 h-5 mr-3" />
                    Manage Courses
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleAdd}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-2xl hover:from-blue-600 hover:to-purple-700 flex items-center justify-center whitespace-nowrap font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-blue-300/30"
                >
                  <Plus className="w-5 h-5 mr-3" />
                  Add {activeTab === "courses" ? "Course" : activeTab === "faculty" ? "Faculty" : "User"}
                </button>
              )}
            </div>

            {/* Data Table */}
            <div className="mt-8 bg-white/90 backdrop-blur-sm shadow-2xl overflow-hidden rounded-3xl border border-slate-200/60">
              {activeTab === "users" && (
                <div className="bg-blue-50 border-b border-blue-200 px-6 py-4">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-blue-800">
                      <div className="font-semibold mb-2">Admin Notice:</div>
                      <div className="space-y-1">
                        <div>• User management is a sensitive operation. Be careful when changing user roles or deleting accounts.</div>
                        <div>• Users cannot be created from this panel - they must register through the application.</div>
                        <div>• <strong>Firebase Sync:</strong> When you change user roles, Firebase custom claims are automatically updated for proper authentication.</div>
                        <div>• Use the "Sync Firebase" button to manually sync all users' Firebase claims with their MongoDB roles if needed.</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-600/20 animate-pulse"></div>
                  </div>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <div className="inline-block min-w-full align-middle">
                    <table className="min-w-full divide-y divide-slate-200/50 table-fixed">
                      <thead className="bg-gradient-to-r from-slate-50 to-slate-100/50 backdrop-blur-sm">
                        <tr>
                          {activeTab === "courses" ? (
                            <>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Code
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-48">
                                Title
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-32">
                                Department
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-20">
                                Credits
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Level
                              </th>
                              <th className="px-6 py-4 text-right text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Actions
                              </th>
                            </>
                          ) : activeTab === "faculty" ? (
                            <>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-48">
                                Name
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-40">
                                Email
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-32">
                                Department
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-28">
                                Title
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Office
                              </th>
                              <th className="px-6 py-4 text-right text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Actions
                              </th>
                            </>
                          ) : (
                            <>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-48">
                                Name
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-40">
                                Email
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-32">
                                Role
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-32">
                                Profile
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-40">
                                Last Login
                              </th>
                              <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-32">
                                Firebase
                              </th>
                              <th className="px-6 py-4 text-right text-xs font-bold text-slate-600 uppercase tracking-wider w-24">
                                Actions
                              </th>
                            </>
                          )}
                        </tr>
                      </thead>
                      <tbody className="bg-white/50 divide-y divide-slate-200/30">
                        {paginatedData.map((item, index) => (
                          <tr
                            key={item.id || index}
                            className="hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/30 transition-all duration-300 hover:shadow-sm"
                          >
                            {activeTab === "courses" ? (
                              <>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {item["Course Code"] || "N/A"}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900">
                                  <div
                                    className="max-w-48 truncate"
                                    title={item["Course Title"] || "N/A"}
                                  >
                                    {item["Course Title"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {item["Department"] || "N/A"}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {item["Credits"] || "N/A"}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  <span
                                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                      item["Level"] === "Graduate"
                                        ? "bg-blue-100 text-blue-800"
                                        : item["Level"] === "PhD"
                                        ? "bg-purple-100 text-purple-800"
                                        : "bg-green-100 text-green-800"
                                    }`}
                                  >
                                    {item["Level"] || "N/A"}
                                  </span>
                                </td>
                              </>
                            ) : activeTab === "faculty" ? (
                              <>
                                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                  <div
                                    className="max-w-48 truncate"
                                    title={item["Full Name"] || "N/A"}
                                  >
                                    {item["Full Name"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-40 truncate"
                                    title={item["Email"] || "N/A"}
                                  >
                                    {item["Email"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-32 truncate"
                                    title={item["Department"] || "N/A"}
                                  >
                                    {item["Department"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {item["Title"] || "N/A"}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-24 truncate"
                                    title={item["Office"] || "N/A"}
                                  >
                                    {item["Office"] || "N/A"}
                                  </div>
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                  <div
                                    className="max-w-48 truncate"
                                    title={item["fullName"] || "N/A"}
                                  >
                                    {item["fullName"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-40 truncate"
                                    title={item["email"] || "N/A"}
                                  >
                                    {item["email"] || "N/A"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-32 truncate"
                                    title={item["role"] || "N/A"}
                                  >
                                    <span
                                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                        item.role === 'admin'
                                          ? 'bg-purple-100 text-purple-800'
                                          : 'bg-green-100 text-green-800'
                                      }`}
                                    >
                                      {item["role"] || "N/A"}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-32 truncate"
                                    title={item["profileCompleted"] ? "Profile Complete" : "Profile Incomplete"}
                                  >
                                    <span
                                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                        item.profileCompleted
                                          ? 'bg-green-100 text-green-800'
                                          : 'bg-yellow-100 text-yellow-800'
                                      }`}
                                    >
                                      {item["profileCompleted"] ? "Complete" : "Incomplete"}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-40 truncate"
                                    title={item["lastLoginAt"] ? new Date(item["lastLoginAt"]).toLocaleString() : "Never"}
                                  >
                                    {item["lastLoginAt"] ? new Date(item["lastLoginAt"]).toLocaleDateString() : "Never"}
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                  <div
                                    className="max-w-32 truncate"
                                    title={item["firebaseSynced"] ? "Synced" : "Not Synced"}
                                  >
                                    <span
                                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                        item.firebaseSynced
                                          ? 'bg-green-100 text-green-800'
                                          : 'bg-red-100 text-red-800'
                                      }`}
                                    >
                                      {item.firebaseSynced ? "Synced" : "Not Synced"}
                                    </span>
                                  </div>
                                </td>
                              </>
                            )}
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <div className="flex items-center justify-end space-x-2">
                                {activeTab === "users" && (
                                  <button
                                    onClick={() => openRoleModal(item)}
                                    className={`p-2 rounded-xl transition-all duration-300 transform hover:scale-110 ${
                                      item.role === 'admin' 
                                        ? 'text-purple-600 hover:text-purple-700 hover:bg-purple-50' 
                                        : 'text-blue-600 hover:text-blue-700 hover:bg-blue-50'
                                    }`}
                                    title={`Toggle role (current: ${item.role})`}
                                  >
                                    <Users className="w-4 h-4" />
                                  </button>
                                )}
                                <button
                                  onClick={() => handleEdit(item)}
                                  className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-xl transition-all duration-300 transform hover:scale-110"
                                  title="Edit"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDelete(activeTab === "users" ? item.uid : item.id)}
                                  className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-all duration-300 transform hover:scale-110"
                                  title="Delete"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {allFilteredData.length === 0 && (
                      <div className="text-center py-16">
                        <div className="text-slate-500 text-lg font-medium">
                          No {activeTab} found
                        </div>
                        <p className="text-slate-400 mt-2">
                          Try adjusting your search criteria or add new{" "}
                          {activeTab}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Pagination */}
            {allFilteredData.length > 0 && (
              <div className="mt-8 bg-white/90 backdrop-blur-sm rounded-3xl shadow-lg border border-slate-200/60 p-6 mb-8">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
                  {/* Items per page selector */}
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-slate-700">
                      Items per page:
                    </span>
                    <select
                      value={itemsPerPage}
                      onChange={(e) => {
                        setItemsPerPage(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="border border-slate-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 bg-white shadow-sm transition-all duration-300"
                    >
                      <option value={5}>5</option>
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </select>
                    <span className="text-sm text-slate-600 font-medium">
                      Showing {startIndex + 1} to{" "}
                      {Math.min(endIndex, totalItems)} of {totalItems} results
                    </span>
                  </div>

                  {/* Pagination controls */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="px-4 py-2 text-sm border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all duration-300 hover:shadow-sm"
                    >
                      First
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-4 py-2 text-sm border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center font-medium transition-all duration-300 hover:shadow-sm"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </button>

                    {/* Page numbers */}
                    <div className="flex items-center space-x-1">
                      {Array.from(
                        { length: Math.min(totalPages, 5) },
                        (_, index) => {
                          let pageNumber;
                          if (totalPages <= 5) {
                            pageNumber = index + 1;
                          } else if (currentPage <= 3) {
                            pageNumber = index + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNumber = totalPages - 4 + index;
                          } else {
                            pageNumber = currentPage - 2 + index;
                          }

                          return (
                            <button
                              key={pageNumber}
                              onClick={() => setCurrentPage(pageNumber)}
                              className={`px-4 py-2 text-sm border rounded-xl font-medium transition-all duration-300 ${
                                currentPage === pageNumber
                                  ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white border-blue-500 shadow-lg"
                                  : "border-slate-300 hover:bg-slate-50 hover:shadow-sm"
                              }`}
                            >
                              {pageNumber}
                            </button>
                          );
                        }
                      )}
                    </div>

                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 text-sm border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center font-medium transition-all duration-300 hover:shadow-sm"
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 text-sm border border-slate-300 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all duration-300 hover:shadow-sm"
                    >
                      Last
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      {/* Notification */}
      {notification.show && (
        <div
          className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-lg border ${
            notification.type === "success"
              ? "bg-gradient-to-r from-emerald-500/90 to-teal-500/90 text-white border-emerald-300/30"
              : "bg-gradient-to-r from-red-500/90 to-rose-500/90 text-white border-red-300/30"
          }`}
        >
          <div className="flex items-center">
            {notification.type === "success" ? (
              <CheckCircle className="w-5 h-5 mr-3" />
            ) : (
              <AlertTriangle className="w-5 h-5 mr-3" />
            )}
            <span className="font-medium">{notification.message}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 relative overflow-hidden">
        {renderAdminContent()}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-8 w-11/12 max-w-3xl">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-200/60">
              <div className="flex items-center justify-between p-8 border-b border-slate-200/50">
                <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  {modalType === "add" ? "Add" : "Edit"}{" "}
                  {activeTab === "courses" ? "Course" : activeTab === "faculty" ? "Faculty" : "User"}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all duration-300 transform hover:scale-110"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="max-h-96 overflow-y-auto p-8">
                {activeTab === "courses"
                  ? renderCourseForm()
                  : activeTab === "faculty"
                  ? renderFacultyForm()
                  : renderUserForm()}
              </div>

              <div className="flex justify-end space-x-4 p-8 pt-6 border-t border-slate-200/50">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-6 py-3 border border-slate-300 rounded-2xl text-slate-700 hover:bg-slate-50 font-medium transition-all duration-300 hover:shadow-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl hover:from-blue-600 hover:to-purple-700 flex items-center font-medium shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-blue-300/30"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {modalType === "add" ? "Add" : "Update"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Role Confirmation Modal */}
      {showRoleModal && selectedUserForRole && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-200/60 p-8 max-w-md w-full">
            <div className="flex items-center justify-between mb-6 border-b border-slate-200/50 pb-6">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Confirm Role Change
              </h3>
              <button
                onClick={() => setShowRoleModal(false)}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all duration-300 transform hover:scale-110"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <p className="text-slate-700 mb-6">
              Are you sure you want to change{" "}
              <span className="font-semibold">{selectedUserForRole.fullName || selectedUserForRole.email}</span>{" "}
              from <span className="font-semibold">{selectedUserForRole.role}</span> to{" "}
              <span className="font-semibold">{selectedUserForRole.role === 'admin' ? 'user' : 'admin'}</span>?
            </p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowRoleModal(false)}
                className="px-6 py-3 border border-slate-300 rounded-2xl text-slate-700 hover:bg-slate-50 font-medium transition-all duration-300 hover:shadow-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleRoleChange}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl hover:from-blue-600 hover:to-purple-700 font-medium shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-blue-300/30"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
};

export default AdminDashboard;
