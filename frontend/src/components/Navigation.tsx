import React from 'react';
import { BarChart3, Phone } from 'lucide-react';

interface NavigationProps {
  currentPage: 'dashboard' | 'call';
  onPageChange: (page: 'dashboard' | 'call') => void;
}

function Navigation({ currentPage, onPageChange }: NavigationProps) {
  return (
    <nav className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
      <div className="bg-white/90 backdrop-blur-sm rounded-full shadow-lg border border-gray-200 p-1">
        <div className="flex space-x-1">
          <button
            onClick={() => onPageChange('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all ${
              currentPage === 'dashboard'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-medium">Dashboard</span>
          </button>
          <button
            onClick={() => onPageChange('call')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all ${
              currentPage === 'call'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
            }`}
          >
            <Phone className="w-4 h-4" />
            <span className="text-sm font-medium">Call Interface</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;