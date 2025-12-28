import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { Shield, Eye, Hand, CheckCircle, XCircle, Loader, Upload, Globe, MapPin, Clock, Camera } from 'lucide-react';

function VerifyZeroTrust() {
    const [username, setUsername] = useState('');
    const [palmFile, setPalmFile] = useState(null);
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState('');

    // Simulation State
    const [simNetwork, setSimNetwork] = useState('');
    const [simTime, setSimTime] = useState('');
    const [simLocation, setSimLocation] = useState('');

    // Iris Image (Webcam or File)
    const [irisImgSrc, setIrisImgSrc] = useState(null);
    const [irisFile, setIrisFile] = useState(null);
    const [uploadMode, setUploadMode] = useState(false);

    const webcamRef = useRef(null);

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setIrisImgSrc(imageSrc);
    }, [webcamRef]);

    const verify = async () => {
        if (!username) { setStatus('error'); setMessage('Please enter username'); return; }
        if (!irisImgSrc && !irisFile && !palmFile) {
            setStatus('error'); setMessage('Provide at least one biometric (Iris or Palm)'); return;
        }

        setStatus('loading'); setMessage('Analyzing Biometrics + Context...');

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('strict_context', 'true');

            // Context Overrides
            if (simNetwork) formData.append('mock_ip', simNetwork);
            if (simTime) formData.append('mock_hour', simTime);
            if (simLocation) formData.append('region', simLocation);

            if (palmFile) formData.append('file_palm', palmFile);

            if (irisFile) {
                formData.append('file_iris', irisFile);
            } else if (irisImgSrc) {
                const blob = await (await fetch(irisImgSrc)).blob();
                formData.append('file_iris', blob, 'iris.jpg');
            }

            const res = await axios.post('http://127.0.0.1:8000/auth/verify/zerotrust', formData);

            if (res.data.authenticated) {
                setStatus('success');
                setMessage(res.data.message);
            } else {
                setStatus('error');
                setMessage(res.data.message);
            }
        } catch (e) {
            setStatus('error');
            setMessage(e.response?.data?.detail || 'Zero Trust Denied Access');
        }
    };

    return (
        <div className="page-container">
            <div className="card" style={{ maxWidth: '900px', display: 'grid', gridTemplateColumns: 'minmax(280px, 1fr) 2fr', gap: '2rem', alignItems: 'start' }}>

                {/* Sidebar: Context Info */}
                <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: '700' }}>
                        <Shield /> <span>Zero Trust Engine</span>
                    </div>

                    <div className="context-control">
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                            <Globe size={18} color="#64748b" />
                            <span style={{ fontSize: '0.8rem', fontWeight: '600' }}>Network Origin</span>
                        </div>
                        <select
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                            value={simNetwork}
                            onChange={(e) => setSimNetwork(e.target.value)}
                        >
                            <option value="">(Real) 127.0.0.1 (Local)</option>
                            <option value="192.168.1.1">Trusted LAN (192.168.1.1)</option>
                            <option value="45.33.22.11">Malicious VPN (45.33.x.x)</option>
                        </select>
                    </div>

                    <div className="context-control">
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                            <Clock size={18} color="#64748b" />
                            <span style={{ fontSize: '0.8rem', fontWeight: '600' }}>Time Window</span>
                        </div>
                        <select
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                            value={simTime}
                            onChange={(e) => setSimTime(e.target.value)}
                        >
                            <option value="">(Real) Current Time</option>
                            <option value="14">Business Hours (14:00)</option>
                            <option value="3">Graveyard Shift (03:00)</option>
                        </select>
                    </div>

                    <div className="context-control">
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                            <MapPin size={18} color="#64748b" />
                            <span style={{ fontSize: '0.8rem', fontWeight: '600' }}>Geo-Location</span>
                        </div>
                        <select
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                            value={simLocation}
                            onChange={(e) => setSimLocation(e.target.value)}
                        >
                            <option value="">(Real) Office HQ</option>
                            <option value="UNKNOWN_REGION">Unknown Region (Spoofed)</option>
                        </select>
                    </div>

                    <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: '#94a3b8', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                        * Simulation Mode: Overrides are sent to the Zero Trust engine for testing.
                    </div>
                </div>

                {/* Main Area */}
                <div className="form-stack">
                    <div className="header">
                        <Shield size={24} color="#10b981" />
                        <h1>Context Verification</h1>
                    </div>

                    <div className="form-group">
                        <label>Identity</label>
                        <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
                    </div>

                    {/* Biometric Inputs */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                        {/* Iris Controls */}
                        <div className="form-group">
                            <div className="flex justify-between items-center mb-1">
                                <label style={{ fontSize: '0.85rem' }}>Iris Source</label>
                                <button
                                    className="text-xs text-cyan-600 underline"
                                    onClick={() => { setUploadMode(!uploadMode); setIrisImgSrc(null); setIrisFile(null); }}
                                    style={{ fontSize: '0.75rem', background: 'none', border: 'none', cursor: 'pointer', color: '#0891b2' }}
                                >
                                    {uploadMode ? "Use Camera" : "Upload File"}
                                </button>
                            </div>

                            {uploadMode && (
                                <label className="file-upload" style={{ padding: '0.5rem' }}>
                                    <Eye size={16} />
                                    <span style={{ fontSize: '0.8rem', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{irisFile ? irisFile.name : "Upload Iris"}</span>
                                    <input type="file" onChange={e => setIrisFile(e.target.files[0])} accept="image/*" />
                                </label>
                            )}
                        </div>

                        {/* Palm Upload */}
                        <div className="form-group">
                            <label style={{ fontSize: '0.85rem' }}>Palm Source</label>
                            <label className="file-upload" style={{ padding: '0.5rem' }}>
                                <Hand size={16} />
                                <span style={{ fontSize: '0.8rem', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{palmFile ? palmFile.name : "Upload Palm"}</span>
                                <input type="file" onChange={e => setPalmFile(e.target.files[0])} accept="image/*" />
                            </label>
                        </div>
                    </div>

                    {/* Webcam Preview if Camera Mode */}
                    {!uploadMode && (
                        <div className="webcam-wrapper" style={{ height: '240px', marginBottom: '1rem', position: 'relative' }}>
                            {irisImgSrc ? (
                                <img src={irisImgSrc} alt="captured" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            ) : (
                                <Webcam
                                    audio={false}
                                    ref={webcamRef}
                                    screenshotFormat="image/jpeg"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                            )}

                            {!irisImgSrc && (
                                <button
                                    onClick={capture}
                                    className="btn-primary"
                                    style={{ position: 'absolute', bottom: '10px', left: '50%', transform: 'translateX(-50%)', width: 'auto', padding: '0.4rem 1rem', fontSize: '0.9rem' }}
                                >
                                    <Camera size={16} style={{ marginRight: '5px' }} /> Capture Iris
                                </button>
                            )}
                            {irisImgSrc && (
                                <button
                                    onClick={() => setIrisImgSrc(null)}
                                    className="btn-secondary"
                                    style={{ position: 'absolute', bottom: '10px', left: '50%', transform: 'translateX(-50%)', width: 'auto', padding: '0.4rem 1rem', fontSize: '0.9rem' }}
                                >
                                    Retake
                                </button>
                            )}
                        </div>
                    )}

                    <button
                        className="btn-primary"
                        onClick={verify}
                        disabled={status === 'loading'}
                        style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                    >
                        {status === 'loading' ? <Loader className="spin" /> : 'Validate Access (Zero Trust)'}
                    </button>

                    {status && (
                        <div className={`status-message ${status === 'success' ? 'success' : 'error'}`}>
                            <div className="result-header">
                                {status === 'success' ? <CheckCircle /> : <XCircle />}
                                <h2>{status === 'success' ? 'Authorized' : 'Unauthorized'}</h2>
                            </div>
                            <p style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{message}</p>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}

export default VerifyZeroTrust;
