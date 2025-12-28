import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Enroll from './pages/Enroll';
import VerifyPalm from './pages/VerifyPalm';
import VerifyIris from './pages/VerifyIris';
import VerifyMultimodal from './pages/VerifyMultimodal';
import VerifyZeroTrust from './pages/VerifyZeroTrust';
import AttackSimulation from './pages/AttackSimulation';
import { Shield } from 'lucide-react';

function App() {
  return (
    <Router>
      <div className="app-navbar">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div className="logo">
            <Shield size={28} className="icon-cyan" />
            <span>BiomZERO</span>
          </div>
        </Link>
        <nav>
          <Link to="/">Hub</Link>
          <Link to="/enroll">Enrollment</Link>
        </nav>
      </div>

      <div className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/enroll" element={<Enroll />} />
          <Route path="/verify/palm" element={<VerifyPalm />} />
          <Route path="/verify/iris" element={<VerifyIris />} />
          <Route path="/verify/multimodal" element={<VerifyMultimodal />} />
          <Route path="/verify/zerotrust" element={<VerifyZeroTrust />} />
          <Route path="/attack-simulation" element={<AttackSimulation />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
