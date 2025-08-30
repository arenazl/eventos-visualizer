import React from 'react';

const TopBar: React.FC = () => {
  return (
    <div className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-center h-14">
          
          {/* Logo/Brand Section - Simple */}
          <div className="flex items-center">
            <h1 className="text-lg font-semibold text-gray-900">Eventos</h1>
          </div>

          {/* Right Button */}
          <button className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white px-4 py-1.5 rounded-md text-sm font-medium">
            Microcentro
          </button>
        </div>
      </div>
    </div>
  );
};

export default TopBar;