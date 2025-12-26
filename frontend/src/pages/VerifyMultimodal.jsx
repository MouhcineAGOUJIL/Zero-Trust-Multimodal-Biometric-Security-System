import React, { useState } from 'react';
import axios from 'axios';
import { ShieldCheck, User, Fingerprint, Hand, CheckCircle, XCircle, Loader, Upload } from 'lucide-react';

function VerifyMultimodal() {
    const [username, setUsername] = useState('');
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState('');

    // Files
    const [faceFile, setFaceFile] = useState(null);
    const [fingerFile, setFingerFile] = useState(null);
    const [palmFile, setPalmFile] = useState(null);

    const verify = async () => {
        if (!username) { setStatus('error'); setMessage('Please enter username'); return; }
        if (!faceFile) { setStatus('error'); setMessage('Face is required for Multimodal Auth'); return; }

        setStatus('loading'); setMessage('Processing Biometrics (Fusion)...');

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('file', faceFile);
            if (fingerFile) formData.append('file_finger', fingerFile);
            if (palmFile) formData.append('file_palm', palmFile);

            const res = await axios.post('http://127.0.0.1:8000/auth/verify/multimodal', formData);

            if (res.data.authenticated) {
                setStatus('success');
                setMessage(res.data.message);
            } else {
                setStatus('error');
                setMessage(res.data.message);
            }
        } catch (e) {
            setStatus('error');
            setMessage(e.response?.data?.detail || 'Verification Failed');
        }
    };

    return (
        <div className="page-container">
            <div className="card" style={{ maxWidth: '600px' }}>
                <div className="header">
                    <ShieldCheck size={32} color="#10b981" />
                    <h1>Zero Trust Multimodal Auth</h1>
                    <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                        High-Security Fusion: Face + Fingerprint + Palm
                    </p>
                </div>

                <div className="form-stack">
                    <div className="form-group">
                        <label>Identity Claim</label>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            placeholder="Enter username"
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                        {/* Face Upload */}
                        <div className="form-group">
                            <label style={{ fontSize: '0.8rem' }}>Face (Required)</label>
                            <label className={`file-upload mini ${faceFile ? 'active' : ''}`}>
                                <User size={20} className="icon-purple" />
                                <span className="filename">{faceFile ? "Selected" : "Upload"}</span>
                                <input type="file" onChange={e => setFaceFile(e.target.files[0])} accept="image/*" />
                            </label>
                        </div>

                        {/* Finger Upload */}
                        <div className="form-group">
                            <label style={{ fontSize: '0.8rem' }}>Finger (Optional)</label>
                            <label className={`file-upload mini ${fingerFile ? 'active' : ''}`}>
                                <Fingerprint size={20} className="icon-blue" />
                                <span className="filename">{fingerFile ? "Selected" : "Upload"}</span>
                                <input type="file" onChange={e => setFingerFile(e.target.files[0])} accept="image/*" />
                            </label>
                        </div>

                        {/* Palm Upload */}
                        <div className="form-group">
                            <label style={{ fontSize: '0.8rem' }}>Palm (Optional)</label>
                            <label className={`file-upload mini ${palmFile ? 'active' : ''}`}>
                                <Hand size={20} className="icon-pink" />
                                <span className="filename">{palmFile ? "Selected" : "Upload"}</span>
                                <input type="file" onChange={e => setPalmFile(e.target.files[0])} accept="image/*" />
                            </label>
                        </div>
                    </div>

                    <button
                        className="btn-primary"
                        onClick={verify}
                        disabled={status === 'loading'}
                        style={{ marginTop: '1rem', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                    >
                        {status === 'loading' ? <Loader className="spin" /> : 'Authenticate (Fusion)'}
                    </button>

                    {status && (
                        <div className={`status-message ${status === 'success' ? 'success' : 'error'}`}>
                            <div className="result-header">
                                {status === 'success' ? <CheckCircle /> : <XCircle />}
                                <h2>{status === 'success' ? 'Verified' : 'Rejected'}</h2>
                            </div>
                            <p>{message}</p>
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
                .file-upload.mini {
                    height: 80px;
                    flex-direction: column;
                    justify-content: center;
                    padding: 0.5rem;
                }
                .file-upload.active {
                    border-color: #10b981;
                    background: rgba(16, 185, 129, 0.05);
                }
                .filename {
                    font-size: 0.75rem;
                    margin-top: 0.25rem;
                    color: #64748b;
                }
            `}</style>
        </div>
    );
}

export default VerifyMultimodal;
