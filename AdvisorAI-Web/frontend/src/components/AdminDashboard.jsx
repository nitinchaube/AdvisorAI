import React, { useState, useEffect } from "react";
import Header from "./Header";
import Footer from "./Footer";
import Sidebar from "./Sidebar";
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
} from "lucide-react";

const AdminDashboard = () => {
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Admin specific state
  const [activeTab, setActiveTab] = useState("courses");
  const [courses, setCourses] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("add"); // 'add' or 'edit'
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [notification, setNotification] = useState({
    show: false,
    message: "",
    type: "",
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  // Handler for menu toggle
  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "courses") {
        const response = await adminAPI.getAllCourses();
        setCourses(response.courses || []);
      } else {
        const response = await adminAPI.getAllFaculty();
        setFaculty(response.faculty || []);
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
        : {
            "Full Name": "",
            Email: "",
            Department: "",
            Title: "",
            Office: "",
            Phone: "",
            "Research Interests": "",
            Bio: "",
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
      } else {
        await adminAPI.deleteFaculty(id);
        setFaculty(faculty.filter((f) => f.id !== id));
      }
      showNotification("Item deleted successfully", "success");
    } catch (error) {
      showNotification("Failed to delete item: " + error.message, "error");
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
      } else {
        if (modalType === "add") {
          const response = await adminAPI.addFaculty(formData);
          await loadData();
        } else {
          await adminAPI.updateFaculty(selectedItem.id, formData);
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
      : faculty.filter(
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

  // Render admin content similar to Dashboard's renderContent
  const renderAdminContent = () => {
    return (
      <div className="h-full w-full overflow-hidden">
        {/* Admin Content Container */}
        <div className="h-full bg-white/90 backdrop-blur-sm overflow-y-auto">
          {/* Tabs */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
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
              <button
                onClick={handleAdd}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-2xl hover:from-blue-600 hover:to-purple-700 flex items-center justify-center whitespace-nowrap font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 border border-blue-300/30"
              >
                <Plus className="w-5 h-5 mr-3" />
                Add {activeTab === "courses" ? "Course" : "Faculty"}
              </button>
            </div>

            {/* Data Table */}
            <div className="mt-8 bg-white/90 backdrop-blur-sm shadow-2xl overflow-hidden rounded-3xl border border-slate-200/60">
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
                          ) : (
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
                            ) : (
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
                            )}
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <div className="flex items-center justify-end space-x-2">
                                <button
                                  onClick={() => handleEdit(item)}
                                  className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-xl transition-all duration-300 transform hover:scale-110"
                                  title="Edit"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDelete(item.id)}
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative overflow-hidden">
      {/* Enhanced Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-100/30 via-purple-100/20 to-indigo-100/30"></div>

      {/* Animated gradient orbs */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-200/20 via-purple-200/20 to-indigo-200/20 rounded-full blur-3xl animate-pulse"></div>
      <div
        className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-br from-indigo-200/20 via-blue-200/20 to-cyan-200/20 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: "2s" }}
      ></div>
      <div
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-purple-200/15 via-blue-200/15 to-indigo-200/15 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: "4s" }}
      ></div>

      {/* Subtle grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]"></div>

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

      {/* Fixed Header */}
      <div className="flex-shrink-0 z-50 relative">
        <Header onMenuToggle={handleMenuToggle} sidebarOpen={sidebarOpen} />
      </div>

      {/* Main Content Area - Between Header and Footer */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Sidebar - Between header and footer */}
        {sidebarOpen && (
          <div className="flex-shrink-0 z-40 relative">
            <Sidebar activeTab="admin" setActiveTab={() => {}} />
          </div>
        )}

        {/* Content - Takes remaining space */}
        <div className="flex-1 relative overflow-hidden">
          {renderAdminContent()}
        </div>
      </div>

      {/* Fixed Footer */}
      <div className="flex-shrink-0 z-50 relative">
        <Footer />
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-8 w-11/12 max-w-3xl">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-200/60">
              <div className="flex items-center justify-between p-8 border-b border-slate-200/50">
                <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  {modalType === "add" ? "Add" : "Edit"}{" "}
                  {activeTab === "courses" ? "Course" : "Faculty Member"}
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
                  : renderFacultyForm()}
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
    </div>
  );
};

export default AdminDashboard;
