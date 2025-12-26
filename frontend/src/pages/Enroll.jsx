import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { enrollUser } from '../api';
import { Camera, Fingerprint, UserPlus, CheckCircle, AlertTriangle, Hand } from 'lucide-react';

const Enroll = () => {
    const webcamRef = useRef(null);
    const [username, setUsername] = useState('');
    const [imgSrc, setImgSrc] = useState(null);
    const [fingerFile, setFingerFile] = useState(null);
    const [palmFile, setPalmFile] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);

    const [uploadMode, setUploadMode] = useState(false); // Toggle between Camera and Upload

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImgSrc(imageSrc);
    }, [webcamRef]);

    const handleFaceFileUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                setImgSrc(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const dataURLtoBlob = (dataurl) => {
        let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], { type: mime });
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!username || !imgSrc) return;

        setLoading(true);
        setStatus(null);

        try {
            const faceBlob = dataURLtoBlob(imgSrc);
            const faceFile = new File([faceBlob], "face.jpg", { type: "image/jpeg" });
            const res = await enrollUser(username, faceFile, fingerFile, palmFile);
            setStatus({ type: 'success', message: res.message });
        } catch (err) {
            setStatus({ type: 'error', message: err.detail || "Enrollment failed" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="card" style={{ maxWidth: '600px' }}>
                <div className="header" style={{ marginBottom: '2rem' }}>
                    <UserPlus className="icon-cyan" size={32} />
                    <h1 style={{ marginBottom: '0.5rem' }}>SECURE ENROLLMENT</h1>
                    <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Multimodal Registration</p>
                </div>

                <form onSubmit={handleSubmit} className="form-stack" style={{ gap: '2rem' }}>
                    <div className="form-group">
                        <label style={{ marginBottom: '0.5rem', display: 'block' }}>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter unique ID"
                            style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        />
                    </div>

                    <div className="form-group">
                        <div className="flex justify-between items-center mb-2" style={{ marginBottom: '0.5rem' }}>
                            <label>Face Capture (Required)</label>
                            <button
                                type="button"
                                onClick={() => { setUploadMode(!uploadMode); setImgSrc(null); }}
                                className="text-xs text-cyan-400 hover:text-cyan-300 underline bg-transparent border-none p-0 w-auto"
                                style={{ fontSize: '0.8rem', color: '#06b6d4', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                            >
                                {uploadMode ? "Switch to Webcam" : "Switch to Upload"}
                            </button>
                        </div>

                        <div className="webcam-wrapper" style={{ borderRadius: '12px', overflow: 'hidden', border: '2px solid #e2e8f0', minHeight: '240px' }}>
                            {imgSrc ? (
                                <img src={imgSrc} alt="Captured" style={{ width: '100%', display: 'block' }} />
                            ) : (
                                uploadMode ? (
                                    <div className="flex items-center justify-center h-48 bg-gray-900" style={{ height: '240px', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <label className="cursor-pointer text-center p-4">
                                            <Camera className="mx-auto mb-2 text-gray-500" size={32} style={{ margin: '0 auto 0.5rem', color: '#64748b' }} />
                                            <span className="text-sm text-gray-400" style={{ color: '#94a3b8' }}>Click to Upload Face Image</span>
                                            <input type="file" accept="image/*" className="hidden" style={{ display: 'none' }} onChange={handleFaceFileUpload} />
                                        </label>
                                    </div>
                                ) : (
                                    <Webcam
                                        audio={false}
                                        ref={webcamRef}
                                        screenshotFormat="image/jpeg"
                                        style={{ width: '100%' }}
                                    />
                                )
                            )}
                        </div>

                        {!uploadMode && (
                            <button
                                type="button"
                                onClick={imgSrc ? () => setImgSrc(null) : capture}
                                className="btn-secondary"
                                style={{ marginTop: '1rem' }}
                            >
                                <Camera size={18} style={{ marginRight: '0.5rem' }} />
                                {imgSrc ? "Retake Photo" : "Capture Photo"}
                            </button>
                        )}

                        {uploadMode && imgSrc && (
                            <button
                                type="button"
                                onClick={() => setImgSrc(null)}
                                className="btn-secondary"
                                style={{ marginTop: '1rem' }}
                            >
                                <Camera size={18} style={{ marginRight: '0.5rem' }} />
                                Choose Different File
                            </button>
                        )}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                        <div className="form-group">
                            <label style={{ fontSize: '0.9rem', marginBottom: '0.5rem', display: 'block' }}>Fingerprint (Opt)</label>
                            <label className={`file-upload ${fingerFile ? 'active' : ''}`} style={{ padding: '0.8rem', border: '2px dashed #e2e8f0', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', background: fingerFile ? '#f0f9ff' : 'white', borderColor: fingerFile ? '#0ea5e9' : '#e2e8f0' }}>
                                <Fingerprint size={20} className="icon-purple" color="#8b5cf6" />
                                <span style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100px' }}>{fingerFile ? "Selected" : "Upload"}</span>
                                <input type="file" style={{ display: 'none' }} onChange={(e) => setFingerFile(e.target.files[0])} />
                            </label>
                        </div>

                        <div className="form-group">
                            <label style={{ fontSize: '0.9rem', marginBottom: '0.5rem', display: 'block' }}>Palm (Opt)</label>
                            <label className={`file-upload ${palmFile ? 'active' : ''}`} style={{ padding: '0.8rem', border: '2px dashed #e2e8f0', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', background: palmFile ? '#fdf2f8' : 'white', borderColor: palmFile ? '#ec4899' : '#e2e8f0' }}>
                                <Hand size={20} className="icon-pink" color="#ec4899" />
                                <span style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100px' }}>{palmFile ? "Selected" : "Upload"}</span>
                                <input type="file" style={{ display: 'none' }} onChange={(e) => setPalmFile(e.target.files[0])} />
                            </label>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !username || !imgSrc}
                        className="btn-primary"
                        style={{ marginTop: '1rem', padding: '1rem', fontSize: '1.1rem', background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)' }}
                    >
                        {loading ? "Processing..." : "Register Identity"}
                    </button>
                </form>

                {status && (
                    <div className={`status-message ${status.type}`} style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: '8px', background: status.type === 'success' ? '#ecfdf5' : '#fef2f2', color: status.type === 'success' ? '#047857' : '#b91c1c', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                        {status.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                        <p style={{ margin: 0 }}>{status.message}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Enroll;
