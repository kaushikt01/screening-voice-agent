import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import CallInterface from './components/CallInterface';
import Navigation from './components/Navigation';

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'call'>('dashboard');

  return (
    <div className="min-h-screen">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      
      <div className="pt-16">
        {currentPage === 'dashboard' ? <Dashboard /> : <CallInterface />}
      </div>
    </div>
  );
}

export default App;