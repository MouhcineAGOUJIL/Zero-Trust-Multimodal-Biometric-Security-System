import React, { useState, useEffect, useRef } from 'react';
import {
    ArrowLeft, ShieldAlert, Lock, Globe,
    Play, CheckCircle2, XCircle, Activity, Server, Database,
    Terminal, ShieldCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './AttackSimulation.css';

const AttackSimulation = () => {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [selectedAttack, setSelectedAttack] = useState('all');
    const [logsList, setLogsList] = useState([]);
    const logsEndRef = useRef(null);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logsList]);

    const runSimulation = async () => {
        setLoading(true);
        setResults(null);
        setLogsList([]);

        setLogsList(prev => [{ text: "Establishing secure connection to core...", type: 'system', timestamp: new Date().toLocaleTimeString() }]);
        await new Promise(r => setTimeout(r, 600));

        try {
            const formData = new FormData();
            formData.append('attack_type', selectedAttack);

            const response = await axios.post('http://127.0.0.1:8000/auth/simulate-attack', formData);
            setResults(response.data);

            const apiLogs = response.data.logs;
            for (const log of apiLogs) {
                setLogsList(prev => [...prev, {
                    text: log.details,
                    title: log.type,
                    type: log.status === 'BLOCKED' ? 'success' : log.status === 'SUCCESS' ? 'neutral' : 'danger',
                    status: log.status,
                    score: log.score,
                    timestamp: new Date().toLocaleTimeString()
                }]);
                await new Promise(r => setTimeout(r, 800));
            }

        } catch (error) {
            console.error("Simulation failed", error);
            setLogsList(prev => [...prev, { text: "Connection refused by server.", type: 'danger', timestamp: new Date().toLocaleTimeString() }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="attack-sim-container">

            <Link to="/" className="back-btn">
                <ArrowLeft size={24} />
            </Link>

            <div className="sim-header">
                <h1 className="sim-title">Security Audit V4</h1>
                <p className="sim-subtitle">Adversarial Simulation & Compliance Environment</p>
            </div>

            <div className="sim-grid">

                {/* Left Panel */}
                <div className="glass-panel-light">
                    <div className="control-header">
                        <Activity size={20} />
                        <span>ATTACK VECTORS</span>
                    </div>

                    <div className="control-options">
                        {[
                            { id: 'all', label: 'Full System Audit', icon: Database },
                            { id: 'replay', label: 'Replay Attack', icon: Server },
                            { id: 'context_spoof', label: 'Context Spoofing', icon: Globe },
                            { id: 'stolen_token', label: 'Token Theft', icon: Lock },
                        ].map(opt => (
                            <div
                                key={opt.id}
                                className={`attack-btn ${selectedAttack === opt.id ? 'active' : ''}`}
                                onClick={() => setSelectedAttack(opt.id)}
                            >
                                <div className="attack-icon"><opt.icon size={20} /></div>
                                <span>{opt.label}</span>
                            </div>
                        ))}
                    </div>

                    <div className="run-btn-wrapper">
                        <button
                            className="run-btn"
                            onClick={runSimulation}
                            disabled={loading}
                        >
                            {loading ? 'Executing...' : 'Initiate Simulation'}
                        </button>
                    </div>

                    {results && (
                        <div className="stats-grid glass-panel-light" style={{ margin: '1.5rem', marginTop: 0, padding: '1rem', background: 'rgba(0,0,0,0.2)' }}>
                            <div className="stat-card">
                                <div className="stat-val" style={{ color: '#10b981' }}>{results.stats.blocked}</div>
                                <div className="stat-label">Blocked</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-val" style={{ color: results.stats.breached > 0 ? '#ef4444' : '#94a3b8' }}>{results.stats.breached}</div>
                                <div className="stat-label">Breaches</div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Panel */}
                <div className="glass-panel terminal-window">
                    <div className="terminal-header">
                        <div className="terminal-dots">
                            <div className="dot red"></div>
                            <div className="dot yellow"></div>
                            <div className="dot green"></div>
                        </div>
                        <div style={{ opacity: 0.5, fontSize: '0.8rem' }}>LIVE STREAM</div>
                    </div>

                    <div className="terminal-body">
                        {logsList.length === 0 && !loading && (
                            <div style={{ textAlign: 'center', opacity: 0.3, marginTop: '100px' }}>
                                <Terminal size={48} style={{ margin: '0 auto', marginBottom: '1rem' }} />
                                <p>System Ready. Waiting for command.</p>
                            </div>
                        )}

                        {logsList.map((log, idx) => (
                            <div key={idx} className={`log-item ${log.type}`}>
                                <div style={{ marginTop: '4px', opacity: 0.8 }}>
                                    {log.type === 'success' ? <ShieldCheck size={18} color="#10b981" /> :
                                        log.type === 'danger' ? <XCircle size={18} color="#ef4444" /> :
                                            <Terminal size={18} color="#94a3b8" />}
                                </div>
                                <div className="log-content" style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <h4>{log.title || 'SYSTEM'}</h4>
                                        <span className="log-timestamp">{log.timestamp}</span>
                                    </div>
                                    <p>{log.text}</p>

                                    {log.score !== undefined && (
                                        <div className="mt-4 bg-slate-50 rounded-xl p-3 flex items-center border border-slate-100">
                                            <span className="text-xs font-bold text-slate-500 mr-4 uppercase tracking-wider">Trust Score</span>
                                            <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden mr-4">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-1000 ${log.status !== 'BLOCKED' && log.score > 0.7 ? 'bg-gradient-to-r from-emerald-400 to-emerald-600' : 'bg-gradient-to-r from-red-500 to-red-600'}`}
                                                    style={{ width: `${typeof log.score === 'number' ? log.score * 100 : 0}%` }}
                                                ></div>
                                            </div>
                                            <span className={`text-sm font-mono font-bold ${log.status !== 'BLOCKED' && log.score > 0.7 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                {typeof log.score === 'number' ? log.score.toFixed(2) : log.score}
                                            </span>
                                        </div>
                                    )}                           </div>
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default AttackSimulation;
