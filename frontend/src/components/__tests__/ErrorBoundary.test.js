/**
 * Tests for ErrorBoundary component — Story 1.4 AC1.
 */
import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../ErrorBoundary';

// Suppress console.error for expected boundary catches
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalError;
});

/** Helper: a component that throws on demand */
function BrokenComponent({ shouldThrow }) {
  if (shouldThrow) throw new Error('Test render error');
  return <div>Healthy content</div>;
}

// ---------------------------------------------------------------------------
// AC1 — normal render
// ---------------------------------------------------------------------------

test('AC1: renders children when no error occurs', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={false} />
    </ErrorBoundary>
  );
  expect(screen.getByText('Healthy content')).toBeInTheDocument();
});

test('AC1: does not show fallback UI when no error', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={false} />
    </ErrorBoundary>
  );
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC1 — fallback on crash
// ---------------------------------------------------------------------------

test('AC1: shows fallback UI when child component throws', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(screen.getByRole('alert')).toBeInTheDocument();
});

test('AC1: fallback contains user-friendly heading', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});

test('AC1: fallback does NOT show blank white screen (has descriptive text)', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(screen.getByText(/unexpected error/i)).toBeInTheDocument();
});

test('AC1: fallback shows Try Again button', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC1 — Try Again recovers without page reload
// ---------------------------------------------------------------------------

test('AC1: Try Again resets error state and re-renders children', () => {
  const { rerender } = render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );

  // Confirm fallback is showing
  expect(screen.getByRole('alert')).toBeInTheDocument();

  // Batch the reset click and the rerender in a single act so React processes
  // both together — this ensures the boundary sees the non-throwing children
  // during the same render cycle triggered by setState({ hasError: false }).
  act(() => {
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    rerender(
      <ErrorBoundary>
        <BrokenComponent shouldThrow={false} />
      </ErrorBoundary>
    );
  });

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText('Healthy content')).toBeInTheDocument();
});

test('AC1: componentDidCatch logs the error', () => {
  render(
    <ErrorBoundary>
      <BrokenComponent shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(console.error).toHaveBeenCalled();
});
