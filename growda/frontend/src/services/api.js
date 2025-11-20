import axios from 'axios';

// Get the API base URL from environment variables or use default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// API service for centralized API calls
const apiService = {
  // Get training status
  getStatus: async () => {
    try {
      const response = await apiClient.get('/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching training status:', error);
      throw error;
    }
  },

  // Get metrics history
  getMetricsHistory: async () => {
    try {
      const response = await apiClient.get('/metrics/history');
      return response.data?.history ?? [];
    } catch (error) {
      console.error('Error fetching metrics history:', error);
      // Fallback to empty list if endpoint not available
      return [];
    }
  },

  // Trigger a new training round
  triggerTrainingRound: async () => {
    try {
      const response = await apiClient.post('/train_round');
      return response.data;
    } catch (error) {
      console.error('Error triggering training round:', error);
      throw error;
    }
  },

  // Upload image for prediction
  predictImage: async (imageFile) => {
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      
      const response = await axios.post(`${API_BASE_URL}/predict`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Error predicting image:', error);
      throw error;
    }
  }
};

export default apiService;