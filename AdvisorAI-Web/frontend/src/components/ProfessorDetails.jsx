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
    <div className="h-full w-full bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header Section */}
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-8 mb-8 border border-white/20">
            <button
              onClick={onBack}
              className="mb-8 px-6 py-3 bg-gradient-to-r from-slate-200 to-slate-300 text-slate-800 rounded-2xl font-semibold hover:from-slate-300 hover:to-slate-400 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              ← Back to Explorer
            </button>
            
            {/* Professor Header */}
            <div className="flex flex-col lg:flex-row items-start lg:items-center space-y-6 lg:space-y-0 lg:space-x-8">
              <div className="relative">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 rounded-3xl shadow-2xl flex items-center justify-center">
                  <User className="w-12 h-12 text-white" />
                </div>
                {/* <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                  <Star className="w-4 h-4 text-white fill-current" />
                </div> */}
              </div>
              
              <div className="flex-1">
                <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent mb-3">
                  {professor.name}
                </h1>
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <span className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-2xl shadow-lg">
                    {professor.title || "Professor"}
                  </span>
                  {professor.department && (
                    <span className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-semibold rounded-2xl shadow-lg">
                      {professor.department}
                    </span>
                  )}
                </div>
                
                {/* Quick Stats */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-slate-600">
                  {/* <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Active Faculty</span>
                  </div> */}
                  {professor.courses && professor.courses.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>{professor.courses.length} Courses</span>
                    </div>
                  )}
                  {professor.education && professor.education.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>{professor.education.length} Degrees</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid lg:grid-cols-3 gap-8 mb-8">
            {/* Left Column - Main Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* General Information */}
              {professor.generalInfo && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-xl font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
                      <Info className="w-5 h-5 text-white" />
                    </div>
                    <span>General Information</span>
                  </h2>
                  <p className="text-slate-700 leading-relaxed text-lg">{professor.generalInfo}</p>
                </div>
              )}
              
              {/* Research Information */}
              {professor.researchInfo && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-xl font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-red-500 to-pink-600 rounded-xl">
                      <FlaskConical className="w-5 h-5 text-white" />
                    </div>
                    <span>Research Focus</span>
                  </h2>
                  <p className="text-slate-700 leading-relaxed text-lg">{professor.researchInfo}</p>
                </div>
              )}

              {/* Education */}
              {professor.education && professor.education.length > 0 && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-xl font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl">
                      <User className="w-5 h-5 text-white" />
                    </div>
                    <span>Education</span>
                  </h2>
                  <div className="space-y-4">
                    {professor.education.map((edu, index) => (
                      <div key={index} className="bg-gradient-to-r from-slate-50 to-blue-50 p-4 rounded-2xl border border-slate-200/50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-bold text-slate-800 text-lg">{edu.degree}</div>
                            {edu.institution && <div className="text-slate-600 font-medium">{edu.institution}</div>}
                            {edu.field && <div className="text-slate-500">{edu.field}</div>}
                          </div>
                          {edu.year && (
                            <span className="px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-full">
                              {edu.year}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Publications */}
              {professor.publications && Object.keys(professor.publications).length > 0 && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-xl font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl">
                      <FlaskConical className="w-5 h-5 text-white" />
                    </div>
                    <span>Publications</span>
                  </h2>
                  <div className="space-y-6">
                    {professor.publications.journalArticles && professor.publications.journalArticles.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-slate-800 mb-3 text-lg">Journal Articles</h3>
                        <div className="space-y-3">
                          {professor.publications.journalArticles.slice(0, 5).map((pub, index) => (
                            <div key={index} className="flex items-start space-x-3 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl">
                              <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                              <div className="flex-1">
                                <div className="text-slate-700 font-medium">{pub.title}</div>
                                {pub.year && <span className="text-slate-500 text-sm">({pub.year})</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {professor.publications.books && professor.publications.books.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-slate-800 mb-3 text-lg">Books</h3>
                        <div className="space-y-3">
                          {professor.publications.books.slice(0, 5).map((book, index) => (
                            <div key={index} className="flex items-start space-x-3 p-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl">
                              <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                              <div className="flex-1">
                                <div className="text-slate-700 font-medium">{book.title}</div>
                                {book.year && <span className="text-slate-500 text-sm">({book.year})</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Sidebar */}
            <div className="space-y-6">
              {/* Courses Taught */}
              {professor.courses && professor.courses.length > 0 && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-lg font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl">
                      <FlaskConical className="w-4 h-4 text-white" />
                    </div>
                    <span>Courses Taught</span>
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {professor.courses.map((course, index) => (
                      <span key={index} className="px-3 py-2 bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-xl text-sm font-medium border border-green-200/50">
                        {course}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Honors & Awards */}
              {professor.honorsAndAwards && professor.honorsAndAwards.length > 0 && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-lg font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-xl">
                      <Star className="w-4 h-4 text-white fill-current" />
                    </div>
                    <span>Honors & Awards</span>
                  </h2>
                  <div className="space-y-3">
                    {professor.honorsAndAwards.map((award, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl border border-yellow-200/50">
                        <span className="text-slate-700 font-medium text-sm">{award.award}</span>
                        {award.year && (
                          <span className="px-2 py-1 bg-gradient-to-r from-yellow-500 to-orange-600 text-white text-xs font-bold rounded-full">
                            {award.year}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {professor.experience && professor.experience.length > 0 && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-lg font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <span>Experience</span>
                  </h2>
                  <div className="space-y-3">
                    {professor.experience.map((exp, index) => (
                      <div key={index} className="p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-200/50">
                        <div className="font-semibold text-slate-800 text-sm">{exp.title}</div>
                        {exp.organization && <div className="text-slate-600 text-xs">{exp.organization}</div>}
                        {exp.duration && <div className="text-slate-500 text-xs">{exp.duration}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Contact Information */}
              {(professor.phone || professor.address || professor.website) && (
                <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-6 border border-white/20">
                  <h2 className="text-lg font-bold mb-4 flex items-center space-x-3 text-slate-800">
                    <div className="p-2 bg-gradient-to-r from-slate-500 to-gray-600 rounded-xl">
                      <Info className="w-4 h-4 text-white" />
                    </div>
                    <span>Contact</span>
                  </h2>
                  <div className="space-y-3">
                    {professor.phone && (
                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm">🤙🏻</span>  {/*📞*/}
                        </div>
                        <span className="text-slate-700 font-medium">{professor.phone}</span>
                      </div>
                    )}
                    {professor.address && (
                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl">
                        <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm">📍</span>
                        </div>
                        <span className="text-slate-700 font-medium text-sm">{professor.address}</span>
                      </div>
                    )}
                    {professor.website && (
                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm">🌐</span>
                        </div>
                        <a 
                          href={professor.website} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-blue-600 hover:text-blue-800 font-medium text-sm hover:underline transition-colors"
                        >
                          Visit Website
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Ratings Section */}
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-8 mb-8 border border-white/20">
            <h2 className="text-2xl font-bold mb-6 flex items-center space-x-3 text-slate-800">
              <div className="p-3 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-2xl">
                <Star className="w-6 h-6 text-white fill-current" />
              </div>
              <span>Student Ratings & Reviews</span>
            </h2>
            
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mb-8">
              <div className="flex items-center space-x-6 mb-6 lg:mb-0">
                {averageRating !== "N/A" && (
                  <div className="flex items-center space-x-4">
                    <div className="text-6xl font-bold bg-gradient-to-r from-yellow-500 to-orange-600 bg-clip-text text-transparent">
                      {averageRating}
                    </div>
                    <div className="flex flex-col">
                      {renderStars(Math.floor(parseFloat(averageRating)), 8)}
                      <span className="text-slate-600 mt-2">
                        Based on {reviews.length} reviews
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Reviews Section */}
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-8 border border-white/20">
            <h2 className="text-2xl font-bold mb-6 flex items-center space-x-3 text-slate-800">
              <div className="p-3 bg-gradient-to-r from-orange-500 to-red-600 rounded-2xl">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <span>Student Reviews</span>
            </h2>
            
            <div className="space-y-6 mb-8 max-h-96 overflow-y-auto pr-4">
              {reviews.length > 0 ? (
                reviews.map((review) => (
                  <div key={review.id} className="border-b border-slate-200 pb-6 last:border-b-0">
                    <div className="flex items-center space-x-3 mb-3">
                      {renderStars(review.rating, 5)}
                      <span className="text-slate-500 text-sm">
                        {new Date(review.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="font-semibold text-slate-800 mb-2">
                      {review.userName || "Anonymous"}
                    </p>
                    <p className="text-slate-700 leading-relaxed">{review.text}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageCircle className="w-8 h-8 text-slate-500" />
                  </div>
                  <p className="text-slate-500 text-lg">No reviews yet</p>
                  <p className="text-slate-400">Be the first to share your thoughts!</p>
                </div>
              )}
            </div>

            {/* Add Review Form */}
            <div className="bg-gradient-to-br from-slate-50 to-blue-50 p-6 rounded-2xl border border-slate-200/50">
              <h3 className="text-lg font-semibold mb-4 text-slate-800">Add Your Review</h3>
              
              {error && (
                <div className="flex items-center space-x-2 text-red-600 mb-4 p-3 bg-red-50 rounded-xl border border-red-200">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              )}
              
              <div className="flex items-center space-x-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    onClick={() => setNewRating(i + 1)}
                    className={`w-8 h-8 cursor-pointer transition-all duration-200 transform hover:scale-110 ${
                      i < newRating 
                        ? "text-yellow-400 fill-current" 
                        : "text-slate-300 hover:text-yellow-300"
                    }`}
                  />
                ))}
              </div>
              
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Share your experience with this professor..."
                rows={4}
                className="w-full p-4 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none mb-4 text-slate-700"
              />
              
              <div className="flex items-center justify-between mb-4">
                <button 
                  onClick={() => setIsAnonymous(!isAnonymous)} 
                  className="flex items-center space-x-2 text-slate-600 hover:text-blue-600 transition-colors"
                >
                  {isAnonymous ? (
                    <ToggleRight className="w-5 h-5 text-blue-600" />
                  ) : (
                    <ToggleLeft className="w-5 h-5 text-slate-400" />
                  )}
                  <span className="text-sm">Post anonymously</span>
                </button>
                
                <span className="text-sm text-slate-500">
                  {newComment.length}/500
                </span>
              </div>
              
              <button 
                onClick={handleSubmitComment} 
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center justify-center space-x-2" 
                disabled={submitting}
              >
                <Send className="w-5 h-5" />
                <span>{submitting ? "Submitting..." : "Submit Review"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfessorDetails;
