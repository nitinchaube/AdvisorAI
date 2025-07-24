import React, { useState, useEffect } from "react";
import {
  doc,
  getDoc,
  collection,
  getDocs,
  addDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "../config/firebase";
import {
  Star,
  Users,
  Clock,
  Calendar,
  MapPin,
  MessageCircle,
  Send,
  BookOpen,
  Globe,
  ToggleLeft,
  ToggleRight,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const CourseDetails = ({ courseId, onBack }) => {
  const [course, setCourse] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [newRating, setNewRating] = useState(0);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { currentUser } = useAuth();

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

  const averageRating =
    reviews.length > 0
      ? (
          reviews.reduce((sum, r) => sum + (r.rating || 0), 0) / reviews.length
        ).toFixed(1)
      : "N/A";

  useEffect(() => {
    const fetchCourseAndReviews = async () => {
      try {
        setLoading(true);
        // Fetch course
        const courseRef = doc(db, "courses", courseId);
        const courseSnap = await getDoc(courseRef);
        if (courseSnap.exists()) {
          setCourse({ id: courseSnap.id, ...courseSnap.data() });
        } else {
          setError("Course not found");
          return;
        }

        // Fetch reviews
        const reviewsRef = collection(db, "courses", courseId, "reviews");
        const reviewsSnap = await getDocs(reviewsRef);
        const reviewsData = reviewsSnap.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }));
        setReviews(
          reviewsData.sort(
            (a, b) => (b.createdAt?.seconds || 0) - (a.createdAt?.seconds || 0)
          )
        );
      } catch (err) {
        setError(err.message);
        console.error("Error fetching course details:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCourseAndReviews();
  }, [courseId]);

  const handleSubmitComment = async () => {
    if (!currentUser) {
      setError("Please login to add a review.");
      return;
    }
    if (!newComment.trim() || newRating === 0) {
      setError("Please provide a rating and review text.");
      return;
    }
    try {
      await addDoc(collection(db, "courses", courseId, "reviews"), {
        text: newComment,
        rating: newRating,
        createdAt: serverTimestamp(),
        userId: currentUser.uid,
        userName: isAnonymous
          ? "Anonymous"
          : currentUser.displayName || currentUser.email.split("@")[0],
      });
      setNewComment("");
      setNewRating(0);
      setIsAnonymous(false);
      setError(null);
      // Refresh reviews
      const reviewsSnap = await getDocs(
        collection(db, "courses", courseId, "reviews")
      );
      const reviewsData = reviewsSnap.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      }));
      setReviews(
        reviewsData.sort(
          (a, b) => (b.createdAt?.seconds || 0) - (a.createdAt?.seconds || 0)
        )
      );
    } catch (err) {
      setError("Failed to submit review. Please try again.");
      console.error("Error adding comment:", err);
    }
  };

  if (loading)
    return (
      <div className="h-full flex items-center justify-center text-gray-600">
        Loading...
      </div>
    );
  if (error && !course)
    return (
      <div className="h-full flex items-center justify-center text-red-600">
        Error: {error}
      </div>
    );
  if (!course)
    return (
      <div className="h-full flex items-center justify-center text-gray-600">
        Course not found
      </div>
    );

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 lg:p-8 mb-8">
            <button
              onClick={onBack}
              className="mb-6 px-4 py-2 bg-gradient-to-r from-gray-200 to-gray-300 text-gray-800 rounded-xl font-medium hover:from-gray-300 hover:to-gray-400 transition-all shadow-sm hover:shadow-md"
            >
              Back to Courses
            </button>
            <div className="flex flex-col lg:flex-row items-start justify-between mb-8 gap-6">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl shadow-lg">
                    <BookOpen className="w-6 h-6 text-white" />
                  </div>
                  <h1 className="text-3xl font-bold text-gray-900">
                    {course["Course Code"]} - {course["Course Title"]}
                  </h1>
                </div>
                <p className="text-gray-600 leading-relaxed">
                  {course["Course Description"]}
                </p>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-4 rounded-xl shadow-inner w-full lg:w-auto">
                <p className="font-semibold text-gray-800 mb-2">
                  Credits: {course.Credits}
                </p>
                <p className="text-gray-700">
                  Professor: {course["Course Professor"]}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <span>Details</span>
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-gray-500 flex-shrink-0" />
                    <span className="text-gray-700">
                      {course["Offered Semester"] || "Not specified"}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Users className="w-5 h-5 text-gray-500 flex-shrink-0" />
                    <span className="text-gray-700">
                      Prerequisite: {course["Course Prerequisite"] || "None"}
                    </span>
                  </div>
                  {course["Course URL"] && (
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-gray-500 flex-shrink-0" />
                      <a
                        href={course["Course URL"]}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Course Website
                      </a>
                    </div>
                  )}
                </div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <span>Ratings & Reviews</span>
                </h2>
                <div className="flex items-center space-x-3 mb-4">
                  {averageRating !== "N/A" &&
                    renderStars(Math.floor(parseFloat(averageRating)), 6)}
                  <span className="text-2xl font-bold text-gray-900">
                    {averageRating}
                  </span>
                  <span className="text-gray-500">
                    (Based on {reviews.length} reviews)
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 lg:p-8">
            <h2 className="text-xl font-semibold mb-6 flex items-center space-x-2">
              <MessageCircle className="w-5 h-5 text-blue-600" />
              <span>Student Reviews</span>
            </h2>
            <div className="space-y-6 mb-8 max-h-96 overflow-y-auto pr-4">
              {reviews.length > 0 ? (
                reviews.map((review) => (
                  <div
                    key={review.id}
                    className="border-b pb-6 last:border-b-0"
                  >
                    <div className="flex items-center space-x-2 mb-2">
                      {renderStars(review.rating || 0, 4)}
                    </div>
                    <p className="font-semibold text-gray-800 mb-1">
                      {review.userName || "Anonymous"}
                    </p>
                    <p className="text-gray-700 mb-2">{review.text}</p>
                    <p className="text-sm text-gray-500">
                      {review.createdAt?.toDate().toLocaleString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No reviews yet. Be the first to share your experience!
                </p>
              )}
            </div>

            <div className="bg-gradient-to-br from-gray-50 to-blue-50 p-4 rounded-xl">
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
                    className={`w-6 h-6 cursor-pointer transition-colors ${
                      i < newRating
                        ? "text-yellow-400 fill-current"
                        : "text-gray-300 hover:text-gray-400"
                    }`}
                  />
                ))}
              </div>
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Share your thoughts about this course..."
                rows={4}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-3"
              />
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsAnonymous(!isAnonymous)}
                    className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 transition-colors"
                  >
                    {isAnonymous ? (
                      <ToggleRight className="w-6 h-6 text-blue-600" />
                    ) : (
                      <ToggleLeft className="w-6 h-6 text-gray-400" />
                    )}
                    <span>Post anonymously</span>
                  </button>
                </div>
                <span className="text-sm text-gray-500">
                  {newComment.length}/500
                </span>
              </div>
              <button
                onClick={handleSubmitComment}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg flex items-center justify-center space-x-2"
              >
                <Send className="w-5 h-5" />
                <span>Submit Review</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseDetails;
