import React, { useState, useEffect } from "react";
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
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Course Code
          </label>
          <input
            type="text"
            value={formData["Course Code"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, "Course Code": e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., CS 513"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Credits
          </label>
          <input
            type="text"
            value={formData["Credits"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Credits: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., 3"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Course Title
        </label>
        <input
          type="text"
          value={formData["Course Title"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Course Title": e.target.value })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., Data Structures and Algorithms"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Course Description
        </label>
        <textarea
          value={formData["Course Description"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Course Description": e.target.value })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="3"
          placeholder="Course description..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Department
          </label>
          <input
            type="text"
            value={formData["Department"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Department: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Computer Science"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Level
          </label>
          <select
            value={formData["Level"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Level: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Level</option>
            <option value="Undergraduate">Undergraduate</option>
            <option value="Graduate">Graduate</option>
            <option value="PhD">PhD</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Prerequisites
        </label>
        <input
          type="text"
          value={formData["Prerequisites"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, Prerequisites: e.target.value })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., CS 115, CS 284"
        />
      </div>
    </div>
  );

  const renderFacultyForm = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Full Name
          </label>
          <input
            type="text"
            value={formData["Full Name"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, "Full Name": e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Dr. John Smith"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            type="email"
            value={formData["Email"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Email: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="professor@stevens.edu"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Department
          </label>
          <input
            type="text"
            value={formData["Department"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Department: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Computer Science"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            value={formData["Title"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Title: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Professor, Associate Professor"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Office
          </label>
          <input
            type="text"
            value={formData["Office"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Office: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Room 123, Building A"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Phone
          </label>
          <input
            type="text"
            value={formData["Phone"] || ""}
            onChange={(e) =>
              setFormData({ ...formData, Phone: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., (201) 555-0123"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Research Interests
        </label>
        <textarea
          value={formData["Research Interests"] || ""}
          onChange={(e) =>
            setFormData({ ...formData, "Research Interests": e.target.value })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="2"
          placeholder="Research areas and interests..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Bio
        </label>
        <textarea
          value={formData["Bio"] || ""}
          onChange={(e) => setFormData({ ...formData, Bio: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="3"
          placeholder="Faculty biography..."
        />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification */}
      {notification.show && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg ${
            notification.type === "success"
              ? "bg-green-500 text-white"
              : "bg-red-500 text-white"
          }`}
        >
          <div className="flex items-center">
            {notification.type === "success" ? (
              <CheckCircle className="w-5 h-5 mr-2" />
            ) : (
              <AlertTriangle className="w-5 h-5 mr-2" />
            )}
            {notification.message}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              Admin Dashboard
            </h1>
            <p className="mt-2 text-gray-600">
              Manage courses and faculty members
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("courses")}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === "courses"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <BookOpen className="w-5 h-5 mr-2" />
              Courses
              <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                {courses.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab("faculty")}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === "faculty"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Users className="w-5 h-5 mr-2" />
              Faculty
              <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                {faculty.length}
              </span>
            </button>
          </nav>
        </div>

        {/* Search and Add */}
        <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-80"
            />
          </div>
          <button
            onClick={handleAdd}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center whitespace-nowrap"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add {activeTab === "courses" ? "Course" : "Faculty"}
          </button>
        </div>

        {/* Data Table */}
        <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-md">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="inline-block min-w-full align-middle">
                <table className="min-w-full divide-y divide-gray-200 table-fixed">
                  <thead className="bg-gray-50">
                    <tr>
                      {activeTab === "courses" ? (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                            Code
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                            Title
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                            Department
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                            Credits
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                            Level
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                            Actions
                          </th>
                        </>
                      ) : (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                            Name
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40">
                            Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                            Department
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                            Title
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                            Office
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                            Actions
                          </th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedData.map((item, index) => (
                      <tr key={item.id || index} className="hover:bg-gray-50">
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
                          <button
                            onClick={() => handleEdit(item)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {allFilteredData.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-gray-500">No {activeTab} found</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Pagination */}
        {allFilteredData.length > 0 && (
          <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Items per page selector */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">Items per page:</span>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
              <span className="text-sm text-gray-700">
                Showing {startIndex + 1} to {Math.min(endIndex, totalItems)} of{" "}
                {totalItems} results
              </span>
            </div>

            {/* Pagination controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                First
              </button>
              <button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </button>

              {/* Page numbers */}
              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(totalPages, 5) }, (_, index) => {
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
                      className={`px-3 py-1 text-sm border rounded-md ${
                        currentPage === pageNumber
                          ? "bg-blue-600 text-white border-blue-600"
                          : "border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      {pageNumber}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Last
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {modalType === "add" ? "Add" : "Edit"}{" "}
                {activeTab === "courses" ? "Course" : "Faculty Member"}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {activeTab === "courses"
                ? renderCourseForm()
                : renderFacultyForm()}
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
              >
                <Save className="w-4 h-4 mr-2" />
                {modalType === "add" ? "Add" : "Update"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
