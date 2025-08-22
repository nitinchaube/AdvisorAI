# Routing Structure Documentation

## Overview
The application has been refactored to use proper React Router routing instead of state-based tab switching. Each sidebar section now has its own dedicated route and component.

## New Route Structure

### Main Routes
- `/chat` - Chat with AI interface
- `/chat-history` - Chat history and session management
- `/ratings` - Ratings and reviews page
- `/course-explorer` - Course exploration and management
- `/analytics` - Analytics dashboard
- `/schedule` - Schedule planner
- `/documents` - Document manager

### Legacy Routes (Redirects)
- `/dashboard` - Redirects to `/chat` for backward compatibility

### Other Routes
- `/profile-completion` - Profile editing
- `/profile-data` - Profile data view
- `/admin` - Admin dashboard
- `/portfolio/:userId` - Public portfolio view

## Component Architecture

### Page Components
Each route has its own dedicated page component that uses the `PageLayout` wrapper:

- `ChatPage.jsx` - Main chat interface
- `ChatHistoryPage.jsx` - Chat history view
- `RatingsPageComponent.jsx` - Ratings and reviews
- `CourseExplorerPage.jsx` - Course exploration
- `AnalyticsPage.jsx` - Analytics dashboard
- `SchedulePage.jsx` - Schedule planner
- `DocumentsPage.jsx` - Document manager

### Layout Components
- `PageLayout.jsx` - Reusable layout wrapper with header, sidebar, footer, and background
- `Sidebar.jsx` - Navigation sidebar with React Router integration
- `Header.jsx` - Top navigation header
- `Footer.jsx` - Bottom footer

## Key Changes

### 1. Sidebar Navigation
- Sidebar now uses `useNavigate` and `useLocation` from React Router
- Active tab is determined by the current route path
- Clicking sidebar items navigates to their respective routes

### 2. Component Separation
- Each major feature is now a separate component with its own route
- Components are more focused and maintainable
- Shared layout code is extracted into `PageLayout`

### 3. Routing Benefits
- Browser back/forward buttons work correctly
- URLs are bookmarkable and shareable
- Better SEO and accessibility
- Cleaner component structure

## Usage Examples

### Navigation
```jsx
// Sidebar automatically highlights the active route
// Users can bookmark specific sections
// Browser history works as expected
```

### Component Structure
```jsx
// Each page follows this pattern:
const SomePage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      {/* Page-specific content */}
    </PageLayout>
  );
};
```

## Migration Notes

- Old `Dashboard.jsx` component is no longer used
- All sidebar navigation now uses React Router
- State-based tab switching has been replaced with route-based navigation
- Components maintain the same UI and functionality
- Backward compatibility is maintained through redirects

## Future Enhancements

- Add route guards for specific features
- Implement lazy loading for better performance
- Add breadcrumb navigation
- Consider nested routing for complex features
