import React from 'react';
import TopBar from './components/TopBar';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <TopBar />
      
      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Descubre eventos increíbles
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Encuentra los mejores eventos cerca de ti
          </p>
          
          {/* Placeholder for future content */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Event cards will go here */}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;