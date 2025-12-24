import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Enroll from './pages/Enroll';
import Verify from './pages/Verify';
import { Shield } from 'lucide-react';

function App() {
  return (
    <Router>
      <div className="app-navbar">
        <div className="logo">
          <Shield size={28} className="icon-cyan" />
          <span>BiomZERO</span>
        </div>
        <nav>
          <Link to="/">Enrollment</Link>
          <Link to="/verify">Verification</Link>
        </nav>
      </div>

      <div className="main-content">
        <Routes>
          <Route path="/" element={<Enroll />} />
          <Route path="/verify" element={<Verify />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
