/**
 * Tests for QuotaDisplay component — Story 5.3 AC8
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// useAuth is mocked so QuotaDisplay can render without a real AuthProvider
const mockUseAuth = jest.fn();
jest.mock('../../context/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

import QuotaDisplay from '../auth/QuotaDisplay';

function renderQuota(quotaRemaining, quotaLimit = 10) {
  mockUseAuth.mockReturnValue({ quotaRemaining, quotaLimit });
  return render(<QuotaDisplay />);
}

// ---------------------------------------------------------------------------
// AC8: null state — no render before first API call
// ---------------------------------------------------------------------------

test('renders nothing when quotaRemaining is null', () => {
  const { container } = renderQuota(null);
  expect(container.firstChild).toBeNull();
});

// ---------------------------------------------------------------------------
// AC8: normal state (≥ 4 remaining)
// ---------------------------------------------------------------------------

test('shows remaining count in normal state', () => {
  renderQuota(7);
  expect(screen.getByText(/7 of 10/i)).toBeInTheDocument();
  expect(screen.getByText(/generations remaining today/i)).toBeInTheDocument();
});

test('applies default quota-display class in normal state', () => {
  const { container } = renderQuota(7);
  expect(container.firstChild).toHaveClass('quota-display');
  expect(container.firstChild).not.toHaveClass('quota-warning');
  expect(container.firstChild).not.toHaveClass('quota-exhausted');
});

test('shows correct count for any remaining value ≥ 4', () => {
  renderQuota(10);
  expect(screen.getByText(/10 of 10/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC8: warning state (≤ 3 remaining)
// ---------------------------------------------------------------------------

test('applies quota-warning class when 3 remaining', () => {
  const { container } = renderQuota(3);
  expect(container.firstChild).toHaveClass('quota-warning');
});

test('applies quota-warning class when 1 remaining', () => {
  const { container } = renderQuota(1);
  expect(container.firstChild).toHaveClass('quota-warning');
});

test('shows count text in warning state', () => {
  renderQuota(2);
  expect(screen.getByText(/2 of 10/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC8: exhausted state (0 remaining)
// ---------------------------------------------------------------------------

test('shows exhausted message when remaining is 0', () => {
  renderQuota(0);
  expect(screen.getByText(/quota exhausted/i)).toBeInTheDocument();
  expect(screen.getByText(/resets at midnight utc/i)).toBeInTheDocument();
});

test('applies quota-exhausted class when remaining is 0', () => {
  const { container } = renderQuota(0);
  expect(container.firstChild).toHaveClass('quota-exhausted');
  expect(container.firstChild).not.toHaveClass('quota-warning');
});

test('does not show remaining count text when exhausted', () => {
  renderQuota(0);
  expect(screen.queryByText(/generations remaining today/i)).not.toBeInTheDocument();
});
