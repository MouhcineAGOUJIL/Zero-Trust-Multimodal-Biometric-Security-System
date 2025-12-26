import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { Shield, CheckCircle, XCircle, Loader, Upload, Globe, MapPin, Clock } from 'lucide-react';

function VerifyZeroTrust() {
    const [username, setUsername] = useState('');
    const [fingerFile, setFingerFile] = useState(null);
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState('');
    const webcamRef = useRef(null);

    const verify = async () => {
        if (!username || !fingerFile || !webcamRef.current) {
            setStatus('error'); setMessage('Please complete all fields'); return;
        }

        setStatus('loading'); setMessage('Analyzing Biometrics + Context...');

        try {
            const imageSrc = webcamRef.current.getScreenshot();
            const faceBlob = await (await fetch(imageSrc)).blob();

            const formData = new FormData();
            formData.append('username', username);
            formData.append('file', faceBlob, 'face.jpg');
            formData.append('file_finger', fingerFile);
            formData.append('strict_context', 'true');

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
            <div className="card" style={{ maxWidth: '900px', display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem' }}>

                {/* Sidebar: Context Info (Mock for visuals, static for now) */}
                <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#059669', fontWeight: '700' }}>
                        <Shield /> <span>Zero Trust Engine</span>
                    </div>

                    <div className="context-item">
                        <Globe size={18} color="#64748b" />
                        <div>
                            <div style={{ fontSize: '0.8rem', fontWeight: '600' }}>Network</div>
                            <div style={{ fontSize: '0.9rem' }}>127.0.0.1 (Local)</div>
                        </div>
                    </div>

                    <div className="context-item">
                        <Clock size={18} color="#64748b" />
                        <div>
                            <div style={{ fontSize: '0.8rem', fontWeight: '600' }}>Time Window</div>
                            <div style={{ fontSize: '0.9rem' }}>Business Hours</div>
                        </div>
                    </div>

                    <div className="context-item">
                        <MapPin size={18} color="#64748b" />
                        <div>
                            <div style={{ fontSize: '0.8rem', fontWeight: '600' }}>Location</div>
                            <div style={{ fontSize: '0.9rem' }}>Office HQ</div>
                        </div>
                    </div>

                    <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: '#94a3b8', marginTop: 'auto' }}>
                        * Adaptive Policy Active
                    </div>
                </div>

                {/* Main Area */}
                <div className="form-stack">
                    <div className="header">
                        <Shield size={24} color="#10b981" />
                        <h1>Zero Trust Verification</h1>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group">
                            <label>Identity</label>
                            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
                        </div>

                        <div className="form-group">
                            <label>Fingerprint</label>
                            <label className="file-upload" style={{ padding: '0.5rem' }}>
                                <Upload size={16} />
                                <span style={{ fontSize: '0.8rem', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{fingerFile ? fingerFile.name : "Upload"}</span>
                                <input type="file" onChange={e => setFingerFile(e.target.files[0])} accept="image/*" />
                            </label>
                        </div>
                    </div>

                    <div className="webcam-wrapper" style={{ height: '240px' }}>
                        <Webcam
                            audio={false}
                            ref={webcamRef}
                            screenshotFormat="image/jpeg"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                    </div>

                    <button
                        className="btn-primary"
                        onClick={verify}
                        disabled={status === 'loading'}
                        style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                    >
                        {status === 'loading' ? <Loader className="spin" /> : 'Validate Access'}
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
