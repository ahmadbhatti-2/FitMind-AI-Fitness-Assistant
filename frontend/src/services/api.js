import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    let session;
    try {
        session = JSON.parse(localStorage.getItem('fitmind.session') || 'null');
    } catch {
        localStorage.removeItem('fitmind.session');
    }
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const isAuthRequest = /\/auth\/(login|register)$/.test(error.config?.url || '');
        if (error.response?.status === 401 && !isAuthRequest) {
            localStorage.removeItem('fitmind.session');
            window.dispatchEvent(new Event('fitmind:session-expired'));
        }
        return Promise.reject(error);
    },
);

// All API endpoints in one place for easy management
export const apiEndpoints = {
    agentChat: '/agent/chat',
    getUserProfile: (userId) => `/users/profile/${userId}`,
    updateUserProfile: (userId) => `/users/profile/${userId}`,
    getWorkoutHistory: (userId) => `/workouts/history/${userId}`,
    getWorkoutRec: (userId) => `/workouts/recommend/${userId}`,
    getMealHistory: (userId) => `/nutrition/history/${userId}`,
    getMealRec: (userId, mealType) => `/nutrition/recommend/${userId}/${mealType}`,
    getFoodReplacement: (foodId) => `/nutrition/replacement/${foodId}`,
    getUserProgress: (userId) => `/progress/${userId}`,
    updateProgress: (userId) => `/progress/update/${userId}`,
    saveFeedback: (userId) => `/feedback/save/${userId}`,
    getFeedbackSummary: (userId) => `/feedback/summary/${userId}`,
};

export default api;
