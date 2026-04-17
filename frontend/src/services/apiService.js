import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Auth token injector — set by AuthProvider after each token change
let _getToken = () => null;
export const setTokenProvider = (fn) => {
  _getToken = fn;
};

/**
 * 90 s client-side timeout — 3-variant generation with Sonnet 4.6 can take 60–80 s.
 * Story 1.4 AC5 originally specified 35 s (written for single-variant). Amended to 90 s
 * when Story 2.1 introduced multi-variant generation (IG-1 resolution).
 */
export const GENERATION_TIMEOUT_MS = 90000;

const apiClient = axios.create({ baseURL: API_BASE_URL });

/**
 * Centralised Axios response-error handler (AC2, AC3, AC5 — Story 1.4).
 * Exported so it can be unit-tested in isolation.
 */
export const handleApiError = (error) => {
  // AC5: client-side timeout
  if (error.code === 'ECONNABORTED') {
    return Promise.reject(
      new Error('Generation is taking longer than expected. Please try again.')
    );
  }

  // AC3: network / connection refused — no HTTP response at all
  if (!error.response) {
    return Promise.reject(
      new Error(
        'Unable to connect to the server. Please check your connection and try again.'
      )
    );
  }

  // AC2: structured error format from Story 1.2 backend
  const message =
    error.response?.data?.error?.message ||
    error.response?.data?.detail ||
    `Request failed with status ${error.response.status}`;

  return Promise.reject(new Error(message));
};

apiClient.interceptors.response.use((response) => response, handleApiError);

// Attach JWT to every outgoing request
apiClient.interceptors.request.use((config) => {
  const token = _getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---------------------------------------------------------------------------

const apiService = {
  /**
   * Generate LinkedIn post from inputs.
   */
  async generatePost({ text, pdf, images, url }) {
    const formData = new FormData();

    if (text) formData.append('text_input', text);
    if (pdf) formData.append('pdf_file', pdf);
    if (images && images.length > 0) {
      images.forEach((image) => formData.append('image_files', image));
    }
    if (url) formData.append('url_input', url);

    const response = await apiClient.post('/api/generate', formData, {
      timeout: GENERATION_TIMEOUT_MS,
    });
    return response.data;
  },

  /**
   * Refine existing post based on feedback.
   * Pass variantId + personality for variant-aware refinement (Story 2.1 AC3).
   */
  async refinePost({ postText, feedback, variantId, personality, label }) {
    const formData = new FormData();
    formData.append('post_text', postText);
    formData.append('feedback', feedback);
    if (variantId) formData.append('variant_id', variantId);
    if (personality) formData.append('personality', personality);
    if (label) formData.append('label', label);

    const response = await apiClient.post('/api/refine', formData, {
      timeout: GENERATION_TIMEOUT_MS,
    });
    return response.data;
  },

  /**
   * Exchange a Google id_token for an application JWT.
   */
  async loginWithGoogle(googleToken) {
    const response = await apiClient.post('/api/auth/google', { token: googleToken });
    return response.data;
  },

  /**
   * Check API health — returns an error object rather than throwing.
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/api/health');
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      return { status: 'error', message: error.message };
    }
  },
};

export default apiService;
