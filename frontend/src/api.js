import axios from 'axios';

const API_URL = 'http://localhost:8000/auth';

export const enrollUser = async (username, faceImage, fingerFile) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('file', faceImage);
    if (fingerFile) {
        formData.append('file_finger', fingerFile);
    }

    try {
        const response = await axios.post(`${API_URL}/enroll`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const verifyUser = async (username, faceImage, fingerFile) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('file', faceImage);
    if (fingerFile) {
        formData.append('file_finger', fingerFile);
    }

    try {
        const response = await axios.post(`${API_URL}/verify`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};
