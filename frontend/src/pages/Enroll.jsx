import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { enrollUser } from '../api';
import { Camera, Fingerprint, UserPlus, CheckCircle, AlertTriangle } from 'lucide-react';

const Enroll = () => {
    const webcamRef = useRef(null);
    const [username, setUsername] = useState('');
    const [imgSrc, setImgSrc] = useState(null);
    const [fingerFile, setFingerFile] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImgSrc(imageSrc);
    }, [webcamRef]);

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
            const res = await enrollUser(username, faceFile, fingerFile);
            setStatus({ type: 'success', message: res.message });
        } catch (err) {
            setStatus({ type: 'error', message: err.detail || "Enrollment failed" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="card">
                <div className="header">
                    <UserPlus className="icon-cyan" size={32} />
                    <h1>SECURE ENROLLMENT</h1>
                </div>

                <form onSubmit={handleSubmit} className="form-stack">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter unique ID"
                        />
                    </div>

                    <div className="form-group">
                        <label>Face Capture</label>
                        <div className="webcam-wrapper">
                            {imgSrc ? (
                                <img src={imgSrc} alt="Captured" />
                            ) : (
                                <Webcam
                                    audio={false}
                                    ref={webcamRef}
                                    screenshotFormat="image/jpeg"
                                />
                            )}
                        </div>
                        <button
                            type="button"
                            onClick={imgSrc ? () => setImgSrc(null) : capture}
                            className="btn-secondary"
                        >
                            <Camera size={18} />
                            {imgSrc ? "Retake Photo" : "Capture Photo"}
                        </button>
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
                        {loading ? "Processing..." : "ENROLL USER"}
                    </button>
                </form>

                {status && (
                    <div className={`status-message ${status.type}`}>
                        {status.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                        <p>{status.message}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Enroll;
