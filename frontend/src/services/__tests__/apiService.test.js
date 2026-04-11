/**
 * Tests for apiService — Stories 1.3 + 1.4.
 * Tests the handleApiError interceptor handler and service method behaviour
 * using a mocked axios instance.
 *
 * NOTE: We use `var` for the mock-instance reference so that jest.mock hoisting
 * (which runs before `let`/`const` initialisation) can still assign the value.
 */

// Babel's jest.mock hoisting only allows out-of-scope variables prefixed with
// "mock" (case-insensitive). Using that prefix lets us capture the instance
// before ESM imports are evaluated.
var mockAxiosInstance;

jest.mock('axios', () => {
  mockAxiosInstance = {
    post: jest.fn(),
    get: jest.fn(),
    interceptors: { response: { use: jest.fn() } },
  };
  return { create: jest.fn(() => mockAxiosInstance) };
});

import apiService, { handleApiError, GENERATION_TIMEOUT_MS } from '../apiService';

beforeEach(() => {
  mockAxiosInstance.post.mockReset();
  mockAxiosInstance.get.mockReset();
});

const MOCK_GENERATE_RESPONSE = {
  data: {
    success: true,
    post: 'Generated post text',
    hashtags: ['AI', 'Tech'],
    engagement_score: 8.5,
    hook_strength: 'Strong',
    suggestions: ['Add data'],
    cta: 'Engage!',
    image_alt_text: 'A laptop on a desk.',
  },
};

const MOCK_REFINE_RESPONSE = {
  data: {
    success: true,
    refined_post: 'Punchier post',
    engagement_score: 9.0,
    hook_strength: 'Exceptional',
    hashtags: ['AI'],
    suggestions: ['Great!'],
    cta: 'Reply below',
    changes_made: ['make it punchier'],
  },
};

// ---------------------------------------------------------------------------
// AC2 + AC3 + AC5 — handleApiError (Story 1.4)
// ---------------------------------------------------------------------------

test('AC5: handleApiError — ECONNABORTED → timeout message', async () => {
  await expect(handleApiError({ code: 'ECONNABORTED' })).rejects.toThrow(
    'Generation is taking longer than expected. Please try again.'
  );
});

test('AC3: handleApiError — no response → network message', async () => {
  await expect(handleApiError({ response: undefined })).rejects.toThrow(
    'Unable to connect to the server. Please check your connection and try again.'
  );
});

test('AC2: handleApiError — structured error → data.error.message', async () => {
  await expect(
    handleApiError({
      response: {
        status: 503,
        data: { success: false, error: { code: 'RATE_LIMIT_EXCEEDED', message: 'Rate limit hit.' } },
      },
    })
  ).rejects.toThrow('Rate limit hit.');
});

test('AC2: handleApiError — legacy detail fallback', async () => {
  await expect(
    handleApiError({ response: { status: 400, data: { detail: 'Legacy bad request' } } })
  ).rejects.toThrow('Legacy bad request');
});

test('AC2: handleApiError — no message fields → status code fallback', async () => {
  await expect(
    handleApiError({ response: { status: 500, data: {} } })
  ).rejects.toThrow('Request failed with status 500');
});

// ---------------------------------------------------------------------------
// GENERATION_TIMEOUT_MS export
// ---------------------------------------------------------------------------

test('GENERATION_TIMEOUT_MS is 90000ms', () => {
  expect(GENERATION_TIMEOUT_MS).toBe(90000);
});

// ---------------------------------------------------------------------------
// generatePost
// ---------------------------------------------------------------------------

test('generatePost calls POST /api/generate via apiClient', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_GENERATE_RESPONSE);
  await apiService.generatePost({ text: 'Hello', pdf: null, images: [], url: '' });
  expect(mockAxiosInstance.post).toHaveBeenCalledWith(
    '/api/generate',
    expect.any(FormData),
    expect.objectContaining({ timeout: GENERATION_TIMEOUT_MS })
  );
});

test('generatePost returns response.data', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_GENERATE_RESPONSE);
  const result = await apiService.generatePost({ text: 'Hello', pdf: null, images: [], url: '' });
  expect(result).toEqual(MOCK_GENERATE_RESPONSE.data);
});

test('generatePost includes text_input in FormData', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_GENERATE_RESPONSE);
  await apiService.generatePost({ text: 'My idea', pdf: null, images: [], url: '' });
  const formData = mockAxiosInstance.post.mock.calls[0][1];
  expect(formData.get('text_input')).toBe('My idea');
});

test('generatePost includes url_input in FormData', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_GENERATE_RESPONSE);
  await apiService.generatePost({ text: '', pdf: null, images: [], url: 'https://example.com' });
  const formData = mockAxiosInstance.post.mock.calls[0][1];
  expect(formData.get('url_input')).toBe('https://example.com');
});

test('generatePost omits text_input when text is empty', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_GENERATE_RESPONSE);
  await apiService.generatePost({ text: '', pdf: null, images: [], url: '' });
  const formData = mockAxiosInstance.post.mock.calls[0][1];
  expect(formData.get('text_input')).toBeNull();
});

test('generatePost propagates errors thrown by apiClient', async () => {
  mockAxiosInstance.post.mockRejectedValue(
    new Error('Unable to connect to the server. Please check your connection and try again.')
  );
  await expect(apiService.generatePost({ text: 'test' })).rejects.toThrow(/unable to connect/i);
});

// ---------------------------------------------------------------------------
// refinePost
// ---------------------------------------------------------------------------

test('refinePost calls POST /api/refine via apiClient', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_REFINE_RESPONSE);
  await apiService.refinePost({ postText: 'Original', feedback: 'Make it punchier' });
  expect(mockAxiosInstance.post).toHaveBeenCalledWith(
    '/api/refine',
    expect.any(FormData),
    expect.objectContaining({ timeout: GENERATION_TIMEOUT_MS })
  );
});

test('refinePost returns response.data', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_REFINE_RESPONSE);
  const result = await apiService.refinePost({ postText: 'Original', feedback: 'punchy' });
  expect(result).toEqual(MOCK_REFINE_RESPONSE.data);
});

test('refinePost includes post_text and feedback in FormData', async () => {
  mockAxiosInstance.post.mockResolvedValue(MOCK_REFINE_RESPONSE);
  await apiService.refinePost({ postText: 'My post', feedback: 'be punchy' });
  const formData = mockAxiosInstance.post.mock.calls[0][1];
  expect(formData.get('post_text')).toBe('My post');
  expect(formData.get('feedback')).toBe('be punchy');
});

test('refinePost propagates errors thrown by apiClient', async () => {
  mockAxiosInstance.post.mockRejectedValue(
    new Error('Generation is taking longer than expected. Please try again.')
  );
  await expect(apiService.refinePost({ postText: 'P', feedback: 'f' })).rejects.toThrow(
    /taking longer than expected/i
  );
});

// ---------------------------------------------------------------------------
// checkHealth
// ---------------------------------------------------------------------------

test('checkHealth calls GET /api/health', async () => {
  mockAxiosInstance.get.mockResolvedValue({ data: { status: 'healthy', claude_api: 'connected' } });
  await apiService.checkHealth();
  expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/health');
});

test('checkHealth returns response data on success', async () => {
  mockAxiosInstance.get.mockResolvedValue({ data: { status: 'healthy', claude_api: 'connected' } });
  const result = await apiService.checkHealth();
  expect(result.status).toBe('healthy');
});

test('checkHealth returns error object on failure without throwing', async () => {
  mockAxiosInstance.get.mockRejectedValue(new Error('connection refused'));
  const result = await apiService.checkHealth();
  expect(result.status).toBe('error');
});
