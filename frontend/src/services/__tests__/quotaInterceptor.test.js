/**
 * Tests for the Axios response interceptor that reads quota headers — Story 5.3 AC7
 *
 * Separate file from apiService.test.js because it needs its own axios mock
 * that captures the interceptor success callback at registration time.
 */

// The mock factory captures the success callback when apiService.js calls
// apiClient.interceptors.response.use(successFn, errorFn) during module init.
var capturedSuccessFn;

jest.mock('axios', () => {
  const instance = {
    post: jest.fn(),
    get: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: {
        use: jest.fn((successFn) => {
          capturedSuccessFn = successFn;
        }),
      },
    },
  };
  return { create: jest.fn(() => instance) };
});

import { setQuotaUpdater } from '../apiService';

beforeEach(() => {
  // Reset the quota updater between tests
  setQuotaUpdater(null);
});

// ---------------------------------------------------------------------------
// AC7: quota headers trigger updateQuota callback
// ---------------------------------------------------------------------------

test('calls updateQuota with parsed integers when quota headers are present', () => {
  const mockUpdate = jest.fn();
  setQuotaUpdater(mockUpdate);

  capturedSuccessFn({
    headers: { 'x-quota-remaining': '7', 'x-quota-limit': '10' },
    data: {},
  });

  expect(mockUpdate).toHaveBeenCalledWith(7, 10);
});

test('does not call updateQuota when quota headers are absent', () => {
  const mockUpdate = jest.fn();
  setQuotaUpdater(mockUpdate);

  capturedSuccessFn({ headers: {}, data: {} });

  expect(mockUpdate).not.toHaveBeenCalled();
});

test('returns the response object unchanged', () => {
  setQuotaUpdater(jest.fn());
  const mockResponse = {
    headers: { 'x-quota-remaining': '5', 'x-quota-limit': '10' },
    data: { success: true },
  };

  const result = capturedSuccessFn(mockResponse);

  expect(result).toBe(mockResponse);
});

test('does not throw when updater is null (before AuthProvider mounts)', () => {
  setQuotaUpdater(null);

  expect(() => {
    capturedSuccessFn({
      headers: { 'x-quota-remaining': '5', 'x-quota-limit': '10' },
      data: {},
    });
  }).not.toThrow();
});

test('parses x-quota-limit with default of 10 when header missing', () => {
  const mockUpdate = jest.fn();
  setQuotaUpdater(mockUpdate);

  capturedSuccessFn({
    headers: { 'x-quota-remaining': '3' },  // no x-quota-limit
    data: {},
  });

  expect(mockUpdate).toHaveBeenCalledWith(3, 10);
});
