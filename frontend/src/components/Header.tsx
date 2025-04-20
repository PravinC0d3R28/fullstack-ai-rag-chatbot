import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link to="/">
          <img 
            src="/muj-logo.png" 
            alt="Manipal University Jaipur" 
            className="h-12 w-auto"
          />
        </Link>
        
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
  );
};

export default Header; 