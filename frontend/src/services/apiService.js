import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiService = {
  /**
   * Generate LinkedIn post from inputs
   */
  async generatePost({ text, pdf, images, url }) {
    try {
      const formData = new FormData();

      if (text) {
        formData.append('text_input', text);
      }

      if (pdf) {
        formData.append('pdf_file', pdf);
      }

      if (images && images.length > 0) {
        images.forEach(image => {
          formData.append('image_files', image);
        });
      }

      if (url) {
        formData.append('url_input', url);
      }

      console.log('Sending request with:', {
        hasText: !!text,
        hasPdf: !!pdf,
        imageCount: images?.length || 0,
        hasUrl: !!url
      });

      const response = await axios.post(
        `${API_BASE_URL}/api/generate`,
        formData,
        {
          timeout: 60000, // 60 second timeout
        }
      );

      return response.data;
    } catch (error) {
      console.error('Generate post error:', error);
      throw new Error(
        error.response?.data?.detail ||
        'Failed to generate post. Please check your connection and try again.'
      );
    }
  },

  /**
   * Refine existing post based on feedback
   */
  async refinePost({ postText, feedback }) {
    try {
      const formData = new FormData();
      formData.append('post_text', postText);
      formData.append('feedback', feedback);

      const response = await axios.post(
        `${API_BASE_URL}/api/refine`,
        formData,
        {
          timeout: 60000,
        }
      );

      return response.data;
    } catch (error) {
      console.error('Refine post error:', error);
      throw new Error(
        error.response?.data?.detail ||
        'Failed to refine post. Please try again.'
      );
    }
  },

  /**
   * Check API health
   */
  async checkHealth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      return { status: 'error', message: error.message };
    }
  },
};

export default apiService;
