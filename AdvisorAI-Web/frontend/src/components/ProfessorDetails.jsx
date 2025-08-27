import React, { useState, useEffect } from "react";
import {
  User,
  Info,
  FlaskConical,
  Star,
  MessageCircle,
  Send,
  ToggleLeft,
  ToggleRight,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api"; 

const ProfessorDetails = ({ professorId, onBack }) => {
  const [professor, setProfessor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]); 
  const [newComment, setNewComment] = useState("");
  const [newRating, setNewRating] = useState(0);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { currentUser, token } = useAuth();
  const averageRating =
    reviews.length > 0
    ? (
        reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
      ).toFixed(1)
    : "N/A";

  // Function to format pipe-separated data with bullet points
  const formatPipeSeparatedData = (data) => {
    if (!data) return "";
    if (data.includes("|")) {
      return data.split("|")
        .map(part => part.trim())
        .filter(part => part.length > 0)
        .filter(part => !part.includes("@")) // Filter out email addresses
        .map(part => `• ${part}`)
        .join("\n");
    }
    return data;
  };


  useEffect(() => {
    const fetchProfessorDetailsAndReviews = async () => {
      if (!professorId) return;
      try {
        setLoading(true);
        setError(null);
        const [profResponse, reviewRes] = await Promise.all([
          apiService.getSingleFaculty(professorId),
          apiService.getProfessorReviews(professorId)
        ]);
        if (profResponse.success) {
          setProfessor(profResponse.professor);
        } else {
          setError(profResponse.error || "Professor not found");
        }
        setReviews(
          Array.isArray(reviewRes.reviews)
            ? reviewRes.reviews.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            : []
        );
      } catch (err) {
        setError(err.message);
        console.error("Error fetching professor details or reviews:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfessorDetailsAndReviews();
  }, [professorId]);

//   
  const handleSubmitComment = async () => {
  console.log("Submit button clicked. Checking validation...");

  if (!currentUser) {
    console.error("Validation FAILED: User not logged in.", currentUser);
    setError("Please login to add a review.");
    return;
  }

  if (!newComment.trim() || newRating === 0) {
    console.error("Validation FAILED: Rating or comment missing.", { newRating, newComment });
    setError("Please provide a rating and review text.");
    return;
  }

  console.log("Validation PASSED. Preparing to submit...");
  setSubmitting(true);
  setError(null);

  try {
    console.log("Submitting to the API...");
    const response = await apiService.postProfessorReview(
      professorId,
      {
        rating: newRating,
        text: newComment,
        isAnonymous,
      },
      token
    );
    console.log("API call SUCCEEDED. Response:", response);

    setNewComment("");
    setNewRating(0);
    setIsAnonymous(false);

    console.log("Refreshing reviews...");
    const reviewRes = await apiService.getProfessorReviews(professorId);
    setReviews(
      Array.isArray(reviewRes.reviews)
        ? reviewRes.reviews.sort(
            (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
          )
        : []
    );
    console.log("Reviews refreshed.");

  } catch (err) {
    console.error("API call FAILED.", err);
    setError("Failed to submit review. Please try again.");
  } finally {
    console.log("Resetting submitting state.");
    setSubmitting(false);
  }
};

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
                <h1 className="text-3xl font-bold text-gray-900">{professor["Full Name"] || professor.name}</h1>
              </div>
            </div>

            <div className="space-y-6">
              {/* General Information */}
              {professor["Department"] && (
                <div>
                  <h2 className="text-xl font-semibold mb-3 flex items-center space-x-2">
                    <Info className="w-5 h-5 text-orange-600" />
                    <span>General Information</span>
                  </h2>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <pre className="text-gray-700 leading-relaxed whitespace-pre-line font-sans">
                      {formatPipeSeparatedData(professor["Department"])}
                    </pre>
                  </div>
                </div>
              )}

              {/* Research Information */}
              {professor["Research Interests"] && (
                <div>
                  <h2 className="text-xl font-semibold mb-3 flex items-center space-x-2">
                    <FlaskConical className="w-5 h-5 text-red-600" />
                    <span>Research Information</span>
                  </h2>
                  <div className="bg-red-50 rounded-xl p-4 border border-red-100">
                    <div className="space-y-2">
                      {professor["Research Interests"]
                        .split(/(?<=[.!?])\s+/)
                        .map((sentence, index) => sentence.trim())
                        .filter(sentence => sentence.length > 10)
                        .map((sentence, index) => (
                          <div key={index} className="flex items-start">
                            <span className="text-red-500 mr-2 mt-1">•</span>
                            <span className="text-gray-700 leading-relaxed">{sentence}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-8">
               <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <span>Ratings & Reviews</span>
                </h2>
                <div className="flex items-center space-x-3 mb-4">
                  {averageRating !== "N/A" && renderStars(Math.floor(parseFloat(averageRating)), 6)}
                  <span className="text-2xl font-bold text-gray-900">
                    {averageRating}
                  </span>
                  <span className="text-gray-500">
                    (Based on {reviews.length} reviews)
                  </span>
                </div>
            </div>
          </div>
          
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 lg:p-8">
             <h2 className="text-xl font-semibold mb-6 flex items-center space-x-2">
              <MessageCircle className="w-5 h-5 text-orange-600" />
              <span>Student Reviews</span>
            </h2>
            <div className="space-y-6 mb-8 max-h-96 overflow-y-auto pr-4">
              {reviews.length > 0 ? (
                reviews.map((review) => (
                  <div key={review.id} className="border-b pb-6 last:border-b-0">
                    <div className="flex items-center space-x-2 mb-2">
                      {renderStars(review.rating, 4)}
                    </div>
                    <p className="font-semibold text-gray-800 mb-1">
                      {review.userName || "Anonymous"}
                    </p>
                    <p className="text-gray-700 mb-2">{review.text}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(review.createdAt).toLocaleString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No reviews yet. Be the first to share your thoughts!
                </p>
              )}
            </div>

            <div className="bg-gradient-to-br from-gray-50 to-orange-50 p-4 rounded-xl">
              {error && (
                <div className="flex items-center space-x-2 text-red-600 mb-4">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              )}
              <div className="flex items-center space-x-1 mb-3">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    onClick={() => setNewRating(i + 1)}
                    className={`w-6 h-6 cursor-pointer transition-colors ${i < newRating ? "text-yellow-400 fill-current" : "text-gray-300 hover:text-gray-400"}`}
                  />
                ))}
              </div>
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Share your thoughts about this professor..."
                rows={4}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none mb-3"
              />
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                    <button onClick={() => setIsAnonymous(!isAnonymous)} className="flex items-center space-x-2 text-gray-700 hover:text-orange-600 transition-colors">
                        {isAnonymous ? <ToggleRight className="w-6 h-6 text-orange-600" /> : <ToggleLeft className="w-6 h-6 text-gray-400" />}
                        <span>Post anonymously</span>
                    </button>
                </div>
                <span className="text-sm text-gray-500">
                  {newComment.length}/500
                </span>
              </div>
              <button onClick={handleSubmitComment} className="w-full bg-gradient-to-r from-orange-600 to-red-600 text-white py-3 rounded-lg font-medium hover:from-orange-700 hover:to-red-700 transition-all shadow-md hover:shadow-lg flex items-center justify-center space-x-2" disabled={submitting}>
                <Send className="w-5 h-5" />
                <span>{submitting ? "Submitting..." : "Submit Review"}</span>
              </button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ProfessorDetails;
