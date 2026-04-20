import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/**
 * 90 s client-side timeout — 3-variant generation with Sonnet 4.6 can take 60–80 s.
 * Story 1.4 AC5 originally specified 35 s (written for single-variant). Amended to 90 s
 * when Story 2.1 introduced multi-variant generation (IG-1 resolution).
 */
export const GENERATION_TIMEOUT_MS = 90000;

const apiClient = axios.create({ baseURL: API_BASE_URL });

// ---------------------------------------------------------------------------
// Auth token injection
// Token is stored in AuthProvider memory (never localStorage).
// AuthProvider calls setTokenProvider(() => token) whenever token changes.
// ---------------------------------------------------------------------------

let _getToken = () => null;

export const setTokenProvider = (fn) => {
  _getToken = fn;
};

// Attach JWT to every outgoing request when a token is available
apiClient.interceptors.request.use((config) => {
  const token = _getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response error handler
// ---------------------------------------------------------------------------

/**
 * Centralised Axios response-error handler (AC2, AC3, AC5 — Story 1.4).
 * Exported so it can be unit-tested in isolation.
 */
export const handleApiError = (error) => {
  // Client-side timeout
  if (error.code === 'ECONNABORTED') {
    return Promise.reject(
      new Error('Generation is taking longer than expected. Please try again.')
    );
  }

  // Network error — no HTTP response at all
  if (!error.response) {
    return Promise.reject(
      new Error('Unable to connect to the server. Please check your connection and try again.')
    );
  }

  // 401 — session expired, redirect to login
  if (error.response.status === 401) {
    // Clear the token by triggering a page reload to /login
    // AuthProvider's in-memory token is lost on reload, which is intentional
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  // Extract the structured error message from backend _error_response format
  const message =
    error.response?.data?.error?.message ||
    error.response?.data?.detail ||
    `Request failed with status ${error.response.status}`;

  return Promise.reject(new Error(message));
};

apiClient.interceptors.response.use((response) => response, handleApiError);

// ---------------------------------------------------------------------------
// API service methods
// ---------------------------------------------------------------------------

const apiService = {
  /**
   * Exchange a Google id_token for an application JWT.
   * Called by AuthProvider.login().
   */
  async loginWithGoogle(googleToken) {
    const response = await apiClient.post('/api/auth/google', { token: googleToken });
    return response.data;
  },

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
