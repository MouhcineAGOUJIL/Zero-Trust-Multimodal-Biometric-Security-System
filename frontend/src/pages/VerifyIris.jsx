
import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { Eye, CheckCircle, XCircle, Camera, Loader, Upload } from 'lucide-react';

function VerifyIris() {
    const [username, setUsername] = useState('');
    const [status, setStatus] = useState(null); // 'loading', 'success', 'error'
    const [message, setMessage] = useState('');
    const webcamRef = useRef(null);

    const [uploadMode, setUploadMode] = useState(true); // Default to Upload
    const [file, setFile] = useState(null);
    const [imgSrc, setImgSrc] = useState(null);

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImgSrc(imageSrc);
    }, [webcamRef]);

    const verify = async () => {
        if (!username) { setStatus('error'); setMessage('Please enter username'); return; }
        if (!imgSrc && !file) { setStatus('error'); setMessage('Please capture or upload iris image'); return; }

        setStatus('loading'); setMessage('Processing Iris...');

        try {
            const formData = new FormData();
            formData.append('username', username);

            if (file) {
                formData.append('file_iris', file);
            } else {
                const blob = await (await fetch(imgSrc)).blob();
                formData.append('file_iris', blob, 'iris.jpg');
            }

            const res = await axios.post('http://127.0.0.1:8000/auth/verify/iris', formData);

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
                    <Eye size={24} color="#8b5cf6" />
                    <h1>Iris Verification</h1>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <label>Iris Capture</label>
                            <button
                                className="btn-secondary"
                                style={{ width: 'auto', padding: '0.2rem 0.6rem', fontSize: '0.8rem' }}
                                onClick={() => {
                                    setUploadMode(!uploadMode);
                                    setImgSrc(null);
                                    setFile(null);
                                }}
                            >
                                {uploadMode ? 'Switch to Webcam' : 'Switch to Upload'}
                            </button>
                        </div>

                        {uploadMode ? (
                            <label className={`file-upload ${file ? 'border-purple-500' : ''}`}>
                                <Upload size={20} className="icon-purple" />
                                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{file ? file.name : "Upload Iris Image"}</span>
                                <input type="file" onChange={e => {
                                    setFile(e.target.files[0]);
                                    setImgSrc(URL.createObjectURL(e.target.files[0]));
                                }} accept="image/*" />
                            </label>
                        ) : (
                            <div className="webcam-wrapper" style={{ height: '320px', position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '2px solid #e2e8f0' }}>
                                {imgSrc ? (
                                    <img src={imgSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="captured" />
                                ) : (
                                    <Webcam
                                        audio={false}
                                        ref={webcamRef}
                                        screenshotFormat="image/jpeg"
                                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    />
                                )}
                                {!imgSrc && (
                                    <button
                                        onClick={capture}
                                        className="btn-primary"
                                        style={{ position: 'absolute', bottom: '1rem', left: '50%', transform: 'translateX(-50%)', width: 'auto', padding: '0.5rem 1.5rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.5)' }}
                                    >
                                        <Camera size={16} style={{ marginRight: '0.5rem' }} /> Capture
                                    </button>
                                )}
                                {imgSrc && (
                                    <button
                                        onClick={() => setImgSrc(null)}
                                        className="btn-secondary"
                                        style={{ position: 'absolute', bottom: '1rem', left: '50%', transform: 'translateX(-50%)', width: 'auto', padding: '0.5rem 1.5rem' }}
                                    >
                                        Retake
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    <button
                        className="btn-primary"
                        onClick={verify}
                        disabled={status === 'loading'}
                        style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' }}
                    >
                        {status === 'loading' ? <Loader className="spin" /> : 'Verify Iris'}
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

export default VerifyIris;
