import React, { useState } from "react";
import { Star, Search, Filter, Plus, Users, Award } from "lucide-react";

const RatingPage = () => {
  const [activeFilter, setActiveFilter] = useState('all');

  const ratings = [
    {
      id: 1,
      name: "Dr. Sarah Johnson",
      category: "professor",
      averageRating: 4.8,
      totalReviews: 127,
      description: "Computer Science Department",
      department: "Computer Science",
      courses: ["CS 101", "CS 201", "CS 301"]
    },
    {
      id: 2,
      name: "CS 584 - Natural Language Processing",
      category: "course",
      averageRating: 4.6,
      totalReviews: 89,
      description: "Advanced NLP concepts and applications",
      department: "Computer Science",
      instructor: "Dr. Michael Chen"
    },
    {
      id: 3,
      name: "Dr. Emily Rodriguez",
      category: "professor",
      averageRating: 4.9,
      totalReviews: 203,
      description: "Mathematics Department",
      department: "Mathematics",
      courses: ["MATH 201", "MATH 301", "MATH 401"]
    },
    {
      id: 4,
      name: "PHYS 101 - Introduction to Physics",
      category: "course",
      averageRating: 4.4,
      totalReviews: 156,
      description: "Fundamental physics concepts and laboratory work",
      department: "Physics",
      instructor: "Dr. James Wilson"
    },
    {
      id: 5,
      name: "Dr. Lisa Chen",
      category: "professor",
      averageRating: 4.7,
      totalReviews: 98,
      description: "English Department",
      department: "English",
      courses: ["ENG 101", "ENG 201", "ENG 301"]
    },
    {
      id: 6,
      name: "MATH 301 - Linear Algebra",
      category: "course",
      averageRating: 4.5,
      totalReviews: 134,
      description: "Advanced linear algebra concepts and applications",
      department: "Mathematics",
      instructor: "Dr. Emily Rodriguez"
    }
  ];

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-5 h-5 ${
          i < Math.floor(rating) 
            ? 'text-yellow-400 fill-current' 
            : i < rating 
              ? 'text-yellow-400 fill-current opacity-50' 
              : 'text-gray-300'
        }`}
      />
    ));
  };

  const filters = [
    { id: 'all', label: 'All', count: ratings.length },
    { id: 'professor', label: 'Professors', count: ratings.filter(r => r.category === 'professor').length },
    { id: 'course', label: 'Courses', count: ratings.filter(r => r.category === 'course').length }
  ];

    return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Star className="w-7 h-7 text-white" />
              </div>
        <div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Ratings & Reviews
                </h2>
                <p className="text-gray-600 font-medium">See what students think about courses and professors</p>
              </div>
            </div>
          </div>

          <div className="mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search professors, courses, or departments..."
                  className="w-full pl-12 pr-4 py-4 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white/80 backdrop-blur-sm transition-all duration-200 shadow-sm"
                />
              </div>
              <button className="bg-white/80 backdrop-blur-sm hover:bg-white text-gray-700 font-semibold py-4 px-6 rounded-2xl transition-all duration-200 shadow-sm hover:shadow-md flex items-center space-x-2">
                <Filter className="w-5 h-5" />
                <span>Filter</span>
              </button>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="mb-8">
            <div className="flex space-x-2">
              {filters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setActiveFilter(filter.id)}
                  className={`px-6 py-3 rounded-2xl font-semibold transition-all duration-200 ${
                    activeFilter === filter.id
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                      : 'bg-white/80 backdrop-blur-sm text-gray-600 hover:bg-white hover:shadow-md'
                  }`}
                >
                  {filter.label} ({filter.count})
                </button>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 pb-8">
            {ratings
              .filter(item => activeFilter === 'all' || item.category === activeFilter)
              .map((item) => (
              <div key={item.id} className="bg-white/90 backdrop-blur-sm p-6 rounded-2xl border border-gray-200/50 hover:shadow-xl transition-all duration-300 group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 text-lg mb-1 group-hover:text-blue-600 transition-colors duration-200">
                      {item.name}
                    </h3>
                    <p className="text-gray-600 text-sm mb-2">{item.description}</p>
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="px-3 py-1 bg-gradient-to-r from-blue-100 to-purple-100 text-blue-700 text-xs font-semibold rounded-full">
                        {item.category === 'professor' ? 'Professor' : 'Course'}
                      </span>
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                        {item.department}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {renderStars(item.averageRating)}
                    <span className="text-lg font-bold text-gray-900">{item.averageRating}</span>
                  </div>
                </div>
                
                <div className="space-y-3 mb-4">
                  {item.category === 'professor' && item.courses && (
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <Award className="w-4 h-4" />
                      <span>Teaches: {item.courses.join(', ')}</span>
                    </div>
                  )}
                  {item.category === 'course' && item.instructor && (
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <Users className="w-4 h-4" />
                      <span>Instructor: {item.instructor}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Users className="w-4 h-4" />
                    <span>{item.totalReviews} reviews</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-500 font-medium">Highly Rated</span>
                  </div>
                  <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl flex items-center space-x-2">
                    <Plus className="w-4 h-4" />
                    <span>Rate</span>
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

export default RatingPage;