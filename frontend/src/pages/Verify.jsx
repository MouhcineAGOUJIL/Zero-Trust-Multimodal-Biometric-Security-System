import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { verifyUser } from '../api';
import { ShieldCheck, Fingerprint, Lock, Unlock, Camera, AlertTriangle } from 'lucide-react';

const Verify = () => {
    const webcamRef = useRef(null);
    const [username, setUsername] = useState('');
    const [imgSrc, setImgSrc] = useState(null);
    const [fingerFile, setFingerFile] = useState(null);
    const [result, setResult] = useState(null); // API Response
    const [loading, setLoading] = useState(false);

    const [uploadMode, setUploadMode] = useState(false);

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
        setResult(null);

        try {
            const faceBlob = dataURLtoBlob(imgSrc);
            const faceFile = new File([faceBlob], "face.jpg", { type: "image/jpeg" });
            const res = await verifyUser(username, faceFile, fingerFile);
            setResult(res);
        } catch (err) {
            setResult({ authenticated: false, message: err.detail || "Verification Error" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="card">
                <div className="header">
                    <ShieldCheck className="icon-cyan" size={32} />
                    <h1>ZERO TRUST VERIFY</h1>
                </div>

                <form onSubmit={handleSubmit} className="form-stack">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter Username"
                        />
                    </div>

                    <div className="form-group">
                        <div className="flex justify-between items-center mb-2">
                            <label>Live Face Check</label>
                            <button
                                type="button"
                                onClick={() => { setUploadMode(!uploadMode); setImgSrc(null); }}
                                className="text-xs text-cyan-400 hover:text-cyan-300 underline bg-transparent border-none p-0 w-auto"
                            >
                                {uploadMode ? "Switch to Webcam" : "Switch to Upload"}
                            </button>
                        </div>

                        <div className="webcam-wrapper">
                            {imgSrc ? (
                                <img src={imgSrc} alt="Captured" />
                            ) : (
                                uploadMode ? (
                                    <div className="flex items-center justify-center h-48 bg-gray-900">
                                        <label className="cursor-pointer text-center p-4">
                                            <Camera className="mx-auto mb-2 text-gray-500" size={32} />
                                            <span className="text-sm text-gray-400">Click to Upload Face Image</span>
                                            <input type="file" accept="image/*" className="hidden" onChange={handleFaceFileUpload} />
                                        </label>
                                    </div>
                                ) : (
                                    <Webcam
                                        audio={false}
                                        ref={webcamRef}
                                        screenshotFormat="image/jpeg"
                                    />
                                )
                            )}
                        </div>

                        {!uploadMode && (
                            <button
                                type="button"
                                onClick={imgSrc ? () => setImgSrc(null) : capture}
                                className="btn-secondary"
                            >
                                <Camera size={18} />
                                {imgSrc ? "Retake Photo" : "Capture Photo"}
                            </button>
                        )}

                        {uploadMode && imgSrc && (
                            <button
                                type="button"
                                onClick={() => setImgSrc(null)}
                                className="btn-secondary"
                            >
                                <Camera size={18} />
                                Choose Different File
                            </button>
                        )}
                    </div>

                    <div className="form-group">
                        <label>Fingerprint (Optional)</label>
                        <label className="file-upload">
                            <Fingerprint size={18} className="icon-purple" />
                            <span>{fingerFile ? fingerFile.name : "Upload Fingerprint Image"}</span>
                            <input type="file" onChange={(e) => setFingerFile(e.target.files[0])} />
                        </label>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !username || !imgSrc}
                        className="btn-primary"
                    >
                        {loading ? "Verifying..." : "AUTHENTICATE"}
                    </button>
                </form>

                {result && (
                    <div className={`status-message ${result.authenticated ? 'success' : 'error'}`}>
                        <div className="result-header">
                            {result.authenticated ? <Unlock size={32} /> : <Lock size={32} />}
                            <h2>{result.authenticated ? "ACCESS GRANTED" : "ACCESS DENIED"}</h2>
                        </div>
                        <p>{result.message}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Verify;
