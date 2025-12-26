import React, { useState } from 'react';
import axios from 'axios';
import { Fingerprint, CheckCircle, XCircle, Loader, Upload } from 'lucide-react';

function VerifyFinger() {
    const [username, setUsername] = useState('');
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState('');

    const verify = async () => {
        if (!username || !file) {
            setStatus('error'); setMessage('Please enter username and upload fingerprint'); return;
        }

        setStatus('loading'); setMessage('Processing Fingerprint...');

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('file_finger', file);

            const res = await axios.post('http://127.0.0.1:8000/auth/verify/finger', formData);

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
            <div className="card">
                <div className="header">
                    <Fingerprint size={24} color="#06b6d4" />
                    <h1>Fingerprint Auth</h1>
                </div>

                <div className="form-stack">
                    <div className="form-group">
                        <label>Identity Claim (Username)</label>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            placeholder="Enter username"
                        />
                    </div>

                    <div className="form-group">
                        <label>Fingerprint Scan</label>
                        <label className={`file-upload ${file ? 'border-green-500' : ''}`}>
                            <Upload size={20} className="icon-cyan" />
                            <span style={{ flex: 1 }}>{file ? file.name : "Upload Fingerprint Image (.png, .tif)"}</span>
                            <input type="file" onChange={e => setFile(e.target.files[0])} accept="image/*" />
                        </label>
                    </div>

                    <button
                        className="btn-primary"
                        onClick={verify}
                        disabled={status === 'loading'}
                        style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)' }}
                    >
                        {status === 'loading' ? <Loader className="spin" /> : 'Authenticate'}
                    </button>

                    {status && (
                        <div className={`status-message ${status === 'success' ? 'success' : 'error'}`}>
                            <div className="result-header">
                                {status === 'success' ? <CheckCircle /> : <XCircle />}
                                <h2>{status === 'success' ? 'Access Granted' : 'Access Denied'}</h2>
                            </div>
                            <p>{message}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default VerifyFinger;
