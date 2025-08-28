import React, { useState, useEffect, useMemo } from "react";
import {
  BookOpen,
  Search,
  Users,
  Star,
  Calendar,
  Award,
  Info,
  FlaskConical,
} from "lucide-react";
import { apiService } from "../services/api";

// --- Card Components ---
const ProfessorCard = ({ professor, renderStars, onSelectCourse }) => (
  <div className="bg-white/90 backdrop-blur-sm p-6 rounded-2xl border border-gray-200/50 hover:shadow-xl transition-all duration-300 group flex flex-col min-h-[280px]">
    <div className="flex-1 flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-bold text-gray-900 text-lg group-hover:text-blue-600 transition-colors duration-200">
            {professor.name}
          </h3>
          <div className="flex items-center space-x-2 mt-2">
            <span className="px-3 py-1 bg-gradient-to-r from-orange-100 to-red-100 text-orange-700 text-xs font-semibold rounded-full">
              {professor.title || "Professor"}
            </span>
            {professor.department && (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                {professor.department}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1 ml-4">
          {renderStars(professor.rating)}
          <span className="text-sm font-semibold text-gray-900">{professor.rating?.toFixed ? professor.rating.toFixed(1) : (professor.rating || 0)}</span>
        </div>
      </div>
      <div className="flex-1 mt-4 space-y-4 text-sm text-gray-700">
        <div className="flex items-start">
          <Info className="w-4 h-4 mr-3 mt-0.5 flex-shrink-0 text-gray-400" />
          <p className="text-gray-700 leading-relaxed overflow-hidden flex-1" style={{
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical'
          }}>{professor.generalInfo}</p>
        </div>
        <div className="flex items-start">
          <FlaskConical className="w-4 h-4 mr-3 mt-0.5 flex-shrink-0 text-gray-400" />
          <p className="text-gray-700 leading-relaxed overflow-hidden flex-1" style={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical'
          }}>{professor.researchInfo}</p>
        </div>
      </div>
    </div>
    <div className="mt-6 pt-4 border-t border-gray-100 flex justify-end">
      <button
        onClick={() => onSelectCourse(professor.id, 'professor')}
        className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
      >
        View Details
      </button>
    </div>
  </div>
);


const CourseCard = ({ course, renderStars, getDifficultyColor, onSelectCourse }) => (
    <div className="bg-white/90 backdrop-blur-sm p-6 rounded-2xl border border-gray-200/50 hover:shadow-xl transition-all duration-300 group">
    <div className="flex items-start justify-between mb-4">
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-2">
          <h3 className="font-bold text-gray-900 text-xl group-hover:text-blue-600 transition-colors duration-200">
            {course.code}
          </h3>
          <span className="px-2 py-1 bg-gradient-to-r from-blue-100 to-purple-100 text-blue-700 text-xs font-semibold rounded-full">
            {course.credits} credits
          </span>
        </div>
        <h4 className="font-semibold text-gray-800 text-lg mb-2">{course.name}</h4>
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">{course.description}</p>
      </div>
      <div className="flex items-center space-x-1">
        {renderStars(course.rating)}
        <span className="text-sm font-semibold text-gray-900">{course.rating.toFixed(1)}</span>
        <span className="text-xs text-gray-500">({course.reviews})</span>
      </div>
    </div>
    <div className="mb-4">
      <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getDifficultyColor(course.difficulty)}`}>
        {course.difficulty}
      </span>
    </div>
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2 text-sm text-gray-500">
        <Calendar className="w-4 h-4" />
        <span>{course.duration}</span>
      </div>
      <button
        onClick={() => onSelectCourse(course.id, 'course')}
        className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
      >
        View Details
      </button>
    </div>
  </div>
)

// --- Main Explorer Component ---
const CourseExplorer = ({ onSelectCourse }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("all");
  const [allItems, setAllItems] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [courseResponse, facultyResponse, courseReviewsResponse, profReviewsResponse] = await Promise.all([
          apiService.getCourses(),
          apiService.getFaculty(),
          apiService.getAllCourseReviews(),
          apiService.getAllProfessorReviews(),
        ]);
        
        console.log('API Responses:', {
          courseResponse,
          facultyResponse,
          courseReviewsResponse,
          profReviewsResponse
        });

        //--- Process Course Reviews ---
        const courseRatings = {};
        if (courseReviewsResponse.success) {
          courseReviewsResponse.reviews.forEach(review => {
            if (!courseRatings[review.course_id]) {
              courseRatings[review.course_id] = { total: 0, count: 0 };
            }
            courseRatings[review.course_id].total += review.rating;
            courseRatings[review.course_id].count += 1;
          });
        }

        const courses = (courseResponse?.courses || []).map(course => {
          const id = course.id || course["Course Code"];  
          const ratingInfo = courseRatings[id];
          
          // Extract department from course code more intelligently
          const extractDepartment = (courseCode) => {
            if (!courseCode) return "Unknown";
            
            // Common department prefixes at Stevens
            const deptMap = {
              'CS': 'Computer Science',
              'CSIT': 'Computer Science & IT',
              'MGT': 'Management',
              'FIN': 'Finance',
              'MKT': 'Marketing',
              'ECON': 'Economics',
              'MATH': 'Mathematics',
              'PHYS': 'Physics',
              'CHEM': 'Chemistry',
              'BIO': 'Biology',
              'ENG': 'Engineering',
              'ME': 'Mechanical Engineering',
              'EE': 'Electrical Engineering',
              'CE': 'Civil Engineering',
              'CHE': 'Chemical Engineering',
              'BME': 'Biomedical Engineering',
              'ENV': 'Environmental Engineering',
              'AE': 'Aerospace Engineering',
              'HUM': 'Humanities',
              'HIST': 'History',
              'LIT': 'Literature',
              'PHIL': 'Philosophy',
              'PSY': 'Psychology',
              'SOC': 'Sociology',
              'ART': 'Art',
              'MUS': 'Music',
              'THR': 'Theater',
              'BUS': 'Business',
              'LAW': 'Law',
              'MED': 'Medicine',
              'NUR': 'Nursing'
            };
            
            // Extract the department code (usually first part before space)
            const deptCode = courseCode.split(' ')[0];
            return deptMap[deptCode] || deptCode;
          };
          
          const courseObj = {
            id: id,
            name: course["Course Title"] || course["Course Name"] || "",
            code: course["Course Code"] || "",
            description: course["Course Description"] || "",
            department: extractDepartment(course["Course Code"]),
            credits: parseInt(course["Credits"]) || 3,
            duration: course["Offered Semester"] || "Not specified",
            instructor: course["Course Professor"] || "Not available",
            rating: ratingInfo ? ratingInfo.total / ratingInfo.count : 0,
            reviews: ratingInfo ? ratingInfo.count : 0,
            difficulty: course.difficulty || "Intermediate",
            category: 'course',
          };
          
          console.log('Processed course object:', courseObj);
          return courseObj;
        });

        //--- Process Faculty Reviews ---
        const professorRatings = {};
        if (profReviewsResponse.success) {
            profReviewsResponse.reviews.forEach(review => {
                if (!professorRatings[review.faculty_id]) {
                    professorRatings[review.faculty_id] = { total: 0, count: 0 };
                }
                professorRatings[review.faculty_id].total += review.rating;
                professorRatings[review.faculty_id].count += 1;
            });
        }

        const faculty = (facultyResponse?.faculty || []).map(prof => {
          const ratingInfo = professorRatings[prof.id];
          
          // Ensure all required fields exist with fallbacks
          const facultyObj = {
            id: prof.id || `prof_${Math.random()}`, // Ensure ID exists
            name: prof.name || "Unknown Professor",
            title: prof.title || "Professor",
            generalInfo: prof.generalInfo || "No general information available.",
            researchInfo: prof.researchInfo || "No research information available.",
            department: prof.department || null, // Will be null if not extractable
            rating: ratingInfo ? ratingInfo.total / ratingInfo.count : 0,
            reviews: ratingInfo ? ratingInfo.count : 0,
            coursesTaught: prof.courses || [],
            category: 'professor',
            // Additional fields for details view
            education: prof.education || [],
            publications: prof.publications || {},
            honorsAndAwards: prof.honorsAndAwards || [],
            grantsAndContracts: prof.grantsAndContracts || [],
            experience: prof.experience || [],
            institutionalService: prof.institutionalService || [],
            professionalService: prof.professionalService || [],
            professionalSocieties: prof.professionalSocieties || [],
            appointments: prof.appointments || [],
            profileURL: prof.profileURL || "",
            address: prof.address || "",
            phone: prof.phone || "",
            website: prof.profileURL || ""
          };
          
          console.log('Processed faculty object:', facultyObj);
          return facultyObj;
        });

        const combinedItems = [...courses, ...faculty];
        console.log('Combined items:', combinedItems);
        console.log('Courses count:', courses.length);
        console.log('Faculty count:', faculty.length);
        setAllItems(combinedItems);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filters = useMemo(() => [
    { id: 'all', label: 'All', count: allItems.length },
    { id: 'course', label: 'Courses', count: allItems.filter(i => i.category === 'course').length },
    { id: 'professor', label: 'Professors', count: allItems.filter(i => i.category === 'professor').length },
  ], [allItems]);

  const departments = useMemo(() => {
    const uniqueDepts = [...new Set(allItems.map((c) => c.department?.toLowerCase()).filter(Boolean))];
    
    // Sort departments alphabetically and filter out empty/unknown ones
    const sortedDepts = uniqueDepts
      .filter(dept => dept && dept !== 'unknown' && dept !== 'stevens institute of technology')
      .sort();
    
    return [
      { id: "all", name: "All Departments" },
      ...sortedDepts.map((d) => ({ 
        id: d, 
        name: d.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
      })),
    ];
  }, [allItems]);

  // **UPDATED**: More robust filtering logic
  const filteredItems = useMemo(() => {
    const lowercasedSearchTerm = searchTerm.toLowerCase();

    return allItems.filter(item => {
      const categoryMatch = activeCategory === 'all' || item.category === activeCategory;
      
      // Handle null/undefined departments
      let departmentMatch = true;
      if (selectedDepartment !== 'all') {
        if (item.department) {
          departmentMatch = item.department.toLowerCase().includes(selectedDepartment);
        } else {
          // If no department and we're filtering by a specific department, exclude the item
          departmentMatch = false;
        }
      }
      
      if (!categoryMatch || !departmentMatch) {
        return false;
      }

      if (!lowercasedSearchTerm) {
        return true;
      }

      if (item.category === 'course') {
        return (
          item.name.toLowerCase().includes(lowercasedSearchTerm) ||
          item.description.toLowerCase().includes(lowercasedSearchTerm) ||
          (item.code && item.code.toLowerCase().includes(lowercasedSearchTerm))
        );
      }
      
      if (item.category === 'professor') {
        return (
          item.name.toLowerCase().includes(lowercasedSearchTerm) ||
          (item.generalInfo && item.generalInfo.toLowerCase().includes(lowercasedSearchTerm)) ||
          (item.researchInfo && item.researchInfo.toLowerCase().includes(lowercasedSearchTerm))
        );
      }

      return false;
    });
  }, [activeCategory, allItems, selectedDepartment, searchTerm]);

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredItems.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);

  const renderStars = (rating = 0) => {
    const fullStars = Math.floor(rating);
    const hasHalf = rating - fullStars >= 0.5;
    return Array.from({ length: 5 }, (_, i) => (
      <Star key={i} className={`w-4 h-4 ${i < fullStars ? "text-yellow-400 fill-current" : i === fullStars && hasHalf ? "text-yellow-400 fill-current opacity-50" : "text-gray-300"}`} />
    ));
  };

  const getDifficultyColor = (difficulty = "") => {
    switch (difficulty.toLowerCase()) {
      case "beginner": return "bg-green-100 text-green-700";
      case "intermediate": return "bg-yellow-100 text-yellow-700";
      case "advanced": return "bg-red-100 text-red-700";
      default: return "bg-gray-100 text-gray-700";
    }
  };

  const Pagination = () => {
    const pageNumbers = [];
    const maxVisible = 5;
    const half = Math.floor(maxVisible / 2);
    let start = Math.max(currentPage - half, 1);
    let end = Math.min(start + maxVisible - 1, totalPages);
    if (totalPages > maxVisible && end - start + 1 < maxVisible) {
      start = Math.max(end - maxVisible + 1, 1);
    }
    for (let i = start; i <= end; i++) {
      pageNumbers.push(i);
    }
    if (totalPages <= 1) return null;

    return (
      <div className="flex justify-center items-center space-x-2 mt-6 flex-wrap gap-2">
        <button onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg disabled:opacity-50">Previous</button>
        {start > 1 && (<><button onClick={() => setCurrentPage(1)} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg">1</button>{start > 2 && <span className="px-4 py-2 text-gray-500">...</span>}</>)}
        {pageNumbers.map((number) => (<button key={number} onClick={() => setCurrentPage(number)} className={`px-4 py-2 rounded-lg ${currentPage === number ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800"}`}>{number}</button>))}
        {end < totalPages && (<>{end < totalPages - 1 && <span className="px-4 py-2 text-gray-500">...</span>}<button onClick={() => setCurrentPage(totalPages)} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg">{totalPages}</button></>)}
        <button onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg disabled:opacity-50">Next</button>
      </div>
    );
  };

  if (loading) return <div className="h-full flex items-center justify-center">Loading...</div>;
  if (error) return <div className="h-full flex items-center justify-center text-red-600">Error: {error}</div>;
  if (!allItems || allItems.length === 0) return <div className="h-full flex items-center justify-center text-gray-600">No data available.</div>;

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg"><BookOpen className="w-7 h-7 text-white" /></div>
              <div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">Course & Professor Explorer</h2>
                <p className="text-gray-600 font-medium">Discover and explore available courses and faculty</p>
              </div>
            </div>
          </div>
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input type="text" placeholder="Search by name, description, or course code..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white/80 backdrop-blur-sm transition-all duration-200 shadow-sm" />
              </div>
              <select value={selectedDepartment} onChange={(e) => setSelectedDepartment(e.target.value)} className="bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-700 font-semibold py-4 px-6 rounded-2xl transition-all duration-200 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500">
                {departments.map((dept) => <option key={dept.id} value={dept.id}>{dept.name}</option>)}
              </select>
            </div>
          </div>
          <div className="mb-8">
            <div className="flex space-x-2">
              {filters.map((filter) => (<button key={filter.id} onClick={() => { setActiveCategory(filter.id); setCurrentPage(1); }} className={`px-6 py-3 rounded-2xl font-semibold transition-all duration-200 ${activeCategory === filter.id ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' : 'bg-white/80 backdrop-blur-sm text-gray-600 hover:bg-white hover:shadow-md'}`}>{filter.label} ({filter.count})</button>))}
            </div>
          </div>
          {currentItems.length > 0 ? (
            <div className="grid lg:grid-cols-2 gap-6 pb-8">
              {currentItems.map((item) =>
                item.category === 'course' ? (<CourseCard key={item.id} course={item} renderStars={renderStars} getDifficultyColor={getDifficultyColor} onSelectCourse={onSelectCourse} />) : (<ProfessorCard key={item.id} professor={item} renderStars={renderStars} onSelectCourse={onSelectCourse} />)
              )}
            </div>
          ) : (
            <div className="text-center py-16">
              <h3 className="text-xl font-semibold text-gray-700">No Results Found</h3>
              <p className="text-gray-500 mt-2">Try adjusting your search or filter criteria.</p>
            </div>
          )}
          <Pagination />
        </div>
      </div>
    </div>
  );
};

export default CourseExplorer;