import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Shuffle, Hand, Eye, ShieldAlert } from 'lucide-react';
import '../index.css';

const ModuleCard = ({ to, icon: Icon, title, desc, color }) => (
    <Link to={to} style={{ textDecoration: 'none' }}>
        <div className="card module-card" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
            textAlign: 'center',
            borderTop: `4px solid ${color}`,
            height: '100%',
            justifyContent: 'center',
            padding: '2rem',
            width: '320px', // Fixed width for flex items
            flexGrow: 1,    // Allow growing if needed, but width sets base
            maxWidth: '360px'
        }}>
            <div style={{
                padding: '1rem',
                borderRadius: '50%',
                background: `${color}20`,
                color: color
            }}>
                <Icon size={48} />
            </div>
            <h3 style={{ margin: '0.5rem 0 0', fontWeight: '800', color: '#1e293b' }}>{title}</h3>
            <p style={{ margin: 0, color: '#64748b', fontSize: '0.9rem' }}>{desc}</p>
        </div>
    </Link>
);

function Home() {
    return (
        <div className="page-container" style={{ flexDirection: 'column', gap: '3rem' }}>

            <div style={{ textAlign: 'center', maxWidth: '600px' }}>
                <h1 style={{
                    fontSize: '3rem',
                    fontWeight: '900',
                    letterSpacing: '-2px',
                    background: 'var(--brand-gradient)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    marginBottom: '1rem'
                }}>
                    Biometric Nexus
                </h1>
                <p style={{ fontSize: '1.2rem', color: '#64748b' }}>
                    Select your authentication module.
                </p>
            </div>

            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                columnGap: '4rem', // Horizontal spacing
                rowGap: '6rem',    // Vertical spacing (Increased per user request)
                width: '100%',
                maxWidth: '1400px'
            }}>
                <ModuleCard
                    to="/verify/palm"
                    icon={Hand}
                    title="Hand Verification"
                    desc="Palm texture analysis."
                    color="#ec4899"
                />
                <ModuleCard
                    to="/verify/iris"
                    icon={Eye}
                    title="Iris Verification"
                    desc="Cancelable iris recognition."
                    color="#8b5cf6"
                />
                <ModuleCard
                    to="/verify/multimodal"
                    icon={Shuffle}
                    title="Multimodal Fusion"
                    desc="Combined security check."
                    color="#4f46e5"
                />
                <ModuleCard
                    to="/verify/zerotrust"
                    icon={Shield}
                    title="Context Auth"
                    desc="Zero Trust adaptive logic."
                    color="#10b981"
                />
                <ModuleCard
                    to="/attack-simulation"
                    icon={ShieldAlert}
                    title="Security Audit"
                    desc="Run attack simulations."
                    color="#f59e0b"
                />
            </div>

            <div style={{ marginTop: '5rem' }}>
                <Link to="/enroll" className="btn-secondary" style={{ width: 'auto', padding: '0.8rem 2rem' }}>
                    Register New Identity &rarr;
                </Link>
            </div>
        </div>
    );
}

export default Home;
