import React, { useState, useEffect } from "react";
import {
  User,
  Info,
  FlaskConical,
  Star,
  MessageCircle,
  Send,
  AlertCircle,
} from "lucide-react";
import { apiService } from "../services/api"; // Assuming you have this service

const ProfessorDetails = ({ professorId, onBack }) => {
  const [professor, setProfessor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Placeholder for future review functionality
  const [reviews, setReviews] = useState([]); 
  const [newComment, setNewComment] = useState("");
  const [newRating, setNewRating] = useState(0);

  useEffect(() => {
    const fetchProfessorDetails = async () => {
      if (!professorId) return;
      try {
        setLoading(true);
        setError(null);
        // Use the new API endpoint for a single faculty member
        const response = await apiService.getSingleFaculty(professorId);
        if (response.success) {
          setProfessor(response.professor);
        } else {
          setError(response.error || "Professor not found");
        }
      } catch (err) {
        setError(err.message);
        console.error("Error fetching professor details:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfessorDetails();
  }, [professorId]);

  const renderStars = (rating, size = 5) => (
    <div className="flex">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`w-${size} h-${size} ${
            i < rating ? "text-yellow-400 fill-current" : "text-gray-300"
          }`}
        />
      ))}
    </div>
  );

  if (loading) return <div className="h-full flex items-center justify-center text-gray-600">Loading professor details...</div>;
  if (error) return <div className="h-full flex items-center justify-center text-red-600">Error: {error}</div>;
  if (!professor) return <div className="h-full flex items-center justify-center text-gray-600">Professor not found.</div>;

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-orange-50 to-red-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 lg:p-8 mb-8">
            <button
              onClick={onBack}
              className="mb-6 px-4 py-2 bg-gradient-to-r from-gray-200 to-gray-300 text-gray-800 rounded-xl font-medium hover:from-gray-300 hover:to-gray-400 transition-all shadow-sm hover:shadow-md"
            >
              Back to Explorer
            </button>
            <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 bg-gradient-to-br from-orange-600 to-red-600 rounded-xl shadow-lg">
                <User className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{professor.name}</h1>
                <p className="text-gray-600">{professor.department || "School of Business"}</p>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-3 flex items-center space-x-2">
                  <Info className="w-5 h-5 text-orange-600" />
                  <span>General Information</span>
                </h2>
                <p className="text-gray-700 leading-relaxed">{professor.general_info}</p>
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-3 flex items-center space-x-2">
                  <FlaskConical className="w-5 h-5 text-red-600" />
                  <span>Research Information</span>
                </h2>
                <p className="text-gray-700 leading-relaxed">{professor.research_info}</p>
              </div>
            </div>
          </div>
          
          {/* Placeholder for future review section */}
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 lg:p-8">
             <h2 className="text-xl font-semibold mb-6 flex items-center space-x-2">
              <MessageCircle className="w-5 h-5 text-orange-600" />
              <span>Student Reviews (Coming Soon)</span>
            </h2>
            <div className="text-center py-8 text-gray-500">
              Review functionality for professors will be available soon.
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ProfessorDetails;
