import * as React from 'react';
import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import ChatBot from './components/chat/ChatBot';
import LoginPage from './pages/LoginPage';
import AdminLayout from './components/admin/AdminLayout';
import DashboardPage from './pages/admin/DashboardPage';
import DocumentsPage from './pages/admin/DocumentsPage';
import ModelsPage from './pages/admin/ModelsPage';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Redirect legacy routes */}
          <Route path="/app/*" element={<Navigate to="/" replace />} />
          
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute requireAdmin>
              <AdminLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="models" element={<ModelsPage />} />
          </Route>
          
          {/* Unauthorized Page */}
          <Route path="/unauthorized" element={
            <div className="flex items-center justify-center h-screen bg-gray-100">
              <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Access Denied</h1>
                <p className="text-gray-600 mb-4">You don't have permission to access this page.</p>
                <Link
                  to="/"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors"
                >
                  Return Home
                </Link>
              </div>
            </div>
          } />
          
          {/* Main Homepage */}
          <Route path="/" element={
            <div className="relative min-h-screen w-full bg-gray-50 font-poppins">
              {/* Header with admin link */}
              <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex justify-between items-center">
                  <div className="flex items-center">
                    {/* MUJ Logo - Now clickable */}
                    <Link to="/">
                      <img 
                        src="/muj-logo.png" 
                        alt="Manipal University Jaipur" 
                        className="h-12"
                      />
                    </Link>
                  </div>
                  <div className="group relative">
                    <Link
                      to="/login"
                      className="p-2 rounded-full hover:bg-orange-500 transition-colors group-hover:bg-orange-500 flex items-center"
                      title="Admin Access"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-700 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="hidden group-hover:block absolute right-full mr-2 whitespace-nowrap bg-orange-500 text-white py-1 px-2 rounded text-sm transition-all origin-right">
                        Admin Login
                      </span>
                    </Link>
                  </div>
                </div>
              </header>
              
              {/* Main content with NIRF Rankings banner */}
              <div className="flex flex-col items-center justify-center p-4 mt-8">
                <h1 className="text-3xl font-bold text-center text-orange-600 mb-8">Welcome to Manipal University Jaipur</h1>
                
                {/* NIRF Rankings Banner */}
                <div className="w-full max-w-5xl mx-auto">
                  <img 
                    src="/nirf-rankings.png" 
                    alt="NIRF Rankings 2024" 
                    className="w-full rounded-lg shadow-lg"
                  />
                </div>

                <p className="text-center mt-8 text-gray-600 max-w-2xl">
                  Welcome to our website. Our chat assistant is here to help you with any questions about the university.
                </p>
              </div>

              {/* Chatbot component */}
              <ChatBot
                isOpen={isOpen}
                isHovered={isHovered}
                toggleChat={toggleChat}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
              />
            </div>
          } />
          
          {/* Fallback route - redirects any non-matching path to home page */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App; 