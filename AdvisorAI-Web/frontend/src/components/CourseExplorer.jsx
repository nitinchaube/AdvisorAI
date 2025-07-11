import React, { useState } from "react";
import { BookOpen, Search, Filter, Clock, Users, Star, Calendar, MapPin } from "lucide-react";

const CourseExplorer = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('all');

  const courses = [
    {
      id: 1,
      code: "CS 584",
      title: "Natural Language Processing",
      description: "Advanced concepts in natural language processing, including machine learning approaches to text analysis, language modeling, and computational linguistics.",
      department: "Computer Science",
      credits: 3,
      duration: "16 weeks",
      instructor: "Dr. Michael Chen",
      rating: 4.6,
      reviews: 89,
      difficulty: "Advanced",
      prerequisites: ["CS 201", "MATH 301"],
      schedule: "Mon, Wed 2:00 PM - 3:30 PM",
      location: "Engineering Building 201",
      capacity: 45,
      enrolled: 38
    },
    {
      id: 2,
      code: "MATH 401",
      title: "Advanced Calculus",
      description: "In-depth study of calculus concepts including multivariable calculus, vector analysis, and applications to physics and engineering.",
      department: "Mathematics",
      credits: 4,
      duration: "16 weeks",
      instructor: "Dr. Emily Rodriguez",
      rating: 4.9,
      reviews: 203,
      difficulty: "Advanced",
      prerequisites: ["MATH 301"],
      schedule: "Tue, Thu 10:00 AM - 11:30 AM",
      location: "Science Center 305",
      capacity: 35,
      enrolled: 32
    },
    {
      id: 3,
      code: "PHYS 101",
      title: "Introduction to Physics",
      description: "Fundamental principles of physics including mechanics, thermodynamics, and wave phenomena with laboratory work.",
      department: "Physics",
      credits: 4,
      duration: "16 weeks",
      instructor: "Dr. James Wilson",
      rating: 4.4,
      reviews: 156,
      difficulty: "Intermediate",
      prerequisites: ["MATH 201"],
      schedule: "Mon, Wed, Fri 9:00 AM - 10:00 AM",
      location: "Physics Lab 102",
      capacity: 60,
      enrolled: 45
    },
    {
      id: 4,
      code: "ENG 201",
      title: "Technical Writing",
      description: "Advanced technical writing skills for engineering and scientific communication, including report writing and documentation.",
      department: "English",
      credits: 3,
      duration: "16 weeks",
      instructor: "Dr. Sarah Johnson",
      rating: 4.7,
      reviews: 127,
      difficulty: "Intermediate",
      prerequisites: ["ENG 101"],
      schedule: "Tue, Thu 1:00 PM - 2:30 PM",
      location: "Humanities Building 405",
      capacity: 30,
      enrolled: 28
    },
    {
      id: 5,
      code: "CS 201",
      title: "Data Structures & Algorithms",
      description: "Comprehensive study of fundamental data structures and algorithmic techniques for efficient problem solving.",
      department: "Computer Science",
      credits: 4,
      duration: "16 weeks",
      instructor: "Dr. Sarah Johnson",
      rating: 4.8,
      reviews: 145,
      difficulty: "Intermediate",
      prerequisites: ["CS 101"],
      schedule: "Mon, Wed, Fri 11:00 AM - 12:00 PM",
      location: "Engineering Building 105",
      capacity: 50,
      enrolled: 42
    },
    {
      id: 6,
      code: "MATH 301",
      title: "Linear Algebra",
      description: "Study of vector spaces, linear transformations, matrices, and their applications in various fields.",
      department: "Mathematics",
      credits: 3,
      duration: "16 weeks",
      instructor: "Dr. Emily Rodriguez",
      rating: 4.5,
      reviews: 134,
      difficulty: "Intermediate",
      prerequisites: ["MATH 201"],
      schedule: "Tue, Thu 2:00 PM - 3:30 PM",
      location: "Science Center 201",
      capacity: 40,
      enrolled: 35
    }
  ];

  const departments = [
    { id: 'all', name: 'All Departments' },
    { id: 'cs', name: 'Computer Science' },
    { id: 'math', name: 'Mathematics' },
    { id: 'physics', name: 'Physics' },
    { id: 'english', name: 'English' }
  ];

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${
          i < Math.floor(rating) 
            ? 'text-yellow-400 fill-current' 
            : i < rating 
              ? 'text-yellow-400 fill-current opacity-50' 
              : 'text-gray-300'
        }`}
      />
    ));
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty.toLowerCase()) {
      case 'beginner': return 'bg-green-100 text-green-700';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700';
      case 'advanced': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                <BookOpen className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Course Explorer
                </h2>
                <p className="text-gray-600 font-medium">Discover and explore available courses</p>
              </div>
            </div>
          </div>

          <div className="mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search courses, topics, or instructors..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white/80 backdrop-blur-sm transition-all duration-200 shadow-sm"
                />
              </div>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-700 font-semibold py-4 px-6 rounded-2xl transition-all duration-200 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>{dept.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6 pb-8">
            {courses
              .filter(course => 
                (selectedDepartment === 'all' || course.department.toLowerCase().includes(selectedDepartment)) &&
                (course.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                 course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                 course.instructor.toLowerCase().includes(searchTerm.toLowerCase()))
              )
              .map((course) => (
              <div key={course.id} className="bg-white/90 backdrop-blur-sm p-6 rounded-2xl border border-gray-200/50 hover:shadow-xl transition-all duration-300 group">
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
                    <h4 className="font-semibold text-gray-800 text-lg mb-2">{course.title}</h4>
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">{course.description}</p>
                  </div>
                  <div className="flex items-center space-x-1">
                    {renderStars(course.rating)}
                    <span className="text-sm font-semibold text-gray-900">{course.rating}</span>
                  </div>
                </div>
                
                <div className="space-y-3 mb-4">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Users className="w-4 h-4" />
                    <span>Instructor: {course.instructor}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>{course.schedule}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <MapPin className="w-4 h-4" />
                    <span>{course.location}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-4">
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getDifficultyColor(course.difficulty)}`}>
                    {course.difficulty}
                  </span>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Users className="w-4 h-4" />
                    <span>{course.enrolled}/{course.capacity} enrolled</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>{course.duration}</span>
                  </div>
                  <button className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl">
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseExplorer;