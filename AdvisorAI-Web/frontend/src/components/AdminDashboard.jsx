import React, { useState, useEffect } from "react";
import { apiService } from "../services/api";
import { Pencil, Trash2, Plus, X, Save, ArrowLeft, LogOut } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate, Link } from "react-router-dom";

const AdminDashboard = () => {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [formData, setFormData] = useState({ content: "", metadata: {} });
  const [activeTab, setActiveTab] = useState("collections");
  const [courses, setCourses] = useState([]);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCollections();
  }, []);

  useEffect(() => {
    if (selectedCollection) {
      fetchEntries(selectedCollection);
    }
  }, [selectedCollection]);

  useEffect(() => {
    if (activeTab === "courses") {
      fetchCourses();
    }
  }, [activeTab]);

  const fetchCollections = async () => {
    setLoading(true);
    try {
      const response = await apiService.getCollections();
      if (response.success) {
        setCollections(response.collections);
        setSelectedCollection(response.collections[0]);
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const fetchEntries = async (collection_name) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getEntries(collection_name);
      if (response.success) {
        setEntries(response.courses); // Assuming same structure
      } else {
        setError("Failed to fetch entries");
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getAllCourses();
      if (response.success) {
        setCourses(response.courses);
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const openModal = (entry = null) => {
    setSelectedEntry(entry);
    setFormData(
      entry
        ? { content: entry.content, metadata: { ...entry.metadata } }
        : { content: "", metadata: {} }
    );
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedEntry(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedEntry) {
        await apiService.updateEntry(
          selectedCollection,
          selectedEntry.id,
          formData.content,
          formData.metadata
        );
      } else {
        await apiService.addEntry(
          selectedCollection,
          formData.content,
          formData.metadata
        );
      }
      closeModal();
      fetchEntries(selectedCollection);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this entry?")) {
      try {
        await apiService.deleteEntry(selectedCollection, id);
        fetchEntries(selectedCollection);
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith("metadata.")) {
      const key = name.slice(9);
      setFormData((prev) => ({
        ...prev,
        metadata: { ...prev.metadata, [key]: value },
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="admin-dashboard flex min-h-screen bg-gray-100">
      <aside className="w-64 bg-white shadow-md p-4">
        <h2 className="text-xl font-bold mb-4">Collections</h2>
        <ul>
          {collections.map((col) => (
            <li key={col}>
              <button
                className={`w-full text-left p-2 rounded ${
                  selectedCollection === col ? "bg-blue-100" : ""
                }`}
                onClick={() => setSelectedCollection(col)}
              >
                {col}
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-auto">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded"
          >
            <ArrowLeft size={20} /> Back to Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded text-red-500"
          >
            <LogOut size={20} /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800">
              Manage {selectedCollection}
            </h1>
            <button
              onClick={() => openModal()}
              className="bg-blue-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-600"
            >
              <Plus size={20} /> Add New Entry
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-left">Title</th>
                  <th className="p-3 text-left">ID</th>
                  <th className="p-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      {entry.metadata.title || "Untitled"}
                    </td>
                    <td className="p-3 text-gray-500">
                      {entry.id.slice(0, 8)}...
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => openModal(entry)}
                        className="text-blue-500 hover:text-blue-700 mr-4"
                      >
                        <Pencil size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {showModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg max-w-2xl w-full m-4">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold">
                    {selectedEntry ? "Edit Entry" : "Add New Entry"}
                  </h2>
                  <button onClick={closeModal}>
                    <X size={24} />
                  </button>
                </div>
                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">
                      Title (Metadata)
                    </label>
                    <input
                      name="metadata.title"
                      value={formData.metadata.title || ""}
                      onChange={handleInputChange}
                      className="w-full p-2 border rounded"
                      placeholder="Entry Title"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">
                      Content
                    </label>
                    <textarea
                      name="content"
                      value={formData.content}
                      onChange={handleInputChange}
                      rows={10}
                      className="w-full p-2 border rounded"
                      placeholder="Entry content..."
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">
                      Additional Metadata (JSON)
                    </label>
                    <textarea
                      value={JSON.stringify(formData.metadata, null, 2)}
                      onChange={(e) => {
                        try {
                          setFormData((prev) => ({
                            ...prev,
                            metadata: JSON.parse(e.target.value),
                          }));
                        } catch {}
                      }}
                      rows={5}
                      className="w-full p-2 border rounded font-mono text-sm"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={closeModal}
                      className="px-4 py-2 border rounded hover:bg-gray-100"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-2"
                    >
                      <Save size={18} /> Save
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
