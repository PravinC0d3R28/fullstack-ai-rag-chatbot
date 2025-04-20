import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="container mx-auto py-4">
      <div className="flex items-center mb-6">
        <div className="w-1.5 h-8 bg-gradient-to-b from-orange-500 to-orange-600 rounded-full mr-3"></div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard Overview</h1>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8 transition-all duration-300 hover:shadow-md">
        <div className="flex items-start">
          <div className="mr-4 p-3 bg-orange-50 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Welcome, {user?.username}!</h2>
            <p className="text-gray-600 leading-relaxed">
              This is the admin dashboard for Manipal University Jaipur's RAG Chatbot. From here, you can
              manage the knowledge base and configure the language model settings.
            </p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Document Management Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all duration-300 hover:shadow-md hover:border-orange-100 group">
          <div className="flex items-start mb-4">
            <div className="mr-4 p-3 bg-orange-50 rounded-lg group-hover:bg-orange-100 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Document Management</h2>
              <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                Upload, view, and delete documents in the knowledge base. Support for PDF, DOCX, and HTML files.
              </p>
            </div>
          </div>
          <Link
            to="/admin/documents"
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg shadow-sm hover:from-orange-600 hover:to-orange-700 transition-all duration-200 transform hover:translate-y-[-2px] group"
          >
            <span>Manage Documents</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
        
        {/* Model Selection Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all duration-300 hover:shadow-md hover:border-orange-100 group">
          <div className="flex items-start mb-4">
            <div className="mr-4 p-3 bg-orange-50 rounded-lg group-hover:bg-orange-100 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-1">Model Selection</h2>
              <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                Choose the default language model for the chatbot. Available options include Mixtral, Mistral, and GPT models.
              </p>
            </div>
          </div>
          <Link
            to="/admin/models"
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg shadow-sm hover:from-orange-600 hover:to-orange-700 transition-all duration-200 transform hover:translate-y-[-2px] group"
          >
            <span>Select Model</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </Link>
        </div>
      </div>
      
      {/* System Status Card */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6 transition-all duration-300 hover:shadow-md">
        <div className="flex items-start mb-4">
          <div className="mr-4 p-3 bg-green-50 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-800">System Status</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pl-[52px]">
          <div className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-green-50 transition-colors">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-3 shadow-sm shadow-green-300"></div>
            <div>
              <span className="font-medium text-gray-700 block">Backend API</span>
              <span className="text-xs text-green-600">Running</span>
            </div>
          </div>
          <div className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-green-50 transition-colors">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-3 shadow-sm shadow-green-300"></div>
            <div>
              <span className="font-medium text-gray-700 block">Database</span>
              <span className="text-xs text-green-600">Connected</span>
            </div>
          </div>
          <div className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-green-50 transition-colors">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-3 shadow-sm shadow-green-300"></div>
            <div>
              <span className="font-medium text-gray-700 block">Vector Database</span>
              <span className="text-xs text-green-600">Operational</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; 