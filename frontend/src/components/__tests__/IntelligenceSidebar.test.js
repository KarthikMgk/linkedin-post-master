/**
 * Tests for IntelligenceSidebar component — Stories 3.2 + 3.3
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import IntelligenceSidebar from '../IntelligenceSidebar';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ALL_GREEN_INTEL = {
  hook_strength:       { rating: 'Strong',    reason: 'Opens with a bold challenge' },
  cta_clarity:         { status: 'clear',     suggestion: 'Direct question invites engagement' },
  optimal_posting_time:{ time: 'Tuesday 10am UTC', reason: 'B2B tech peaks mid-morning' },
  length_assessment:   { status: 'optimal',   char_count: 900 },
};

const WARNING_INTEL = {
  hook_strength:       { rating: 'Moderate', reason: 'Acceptable but predictable opener' },
  cta_clarity:         { status: 'consider', suggestion: 'CTA is weak — make it more direct' },
  optimal_posting_time:{ time: 'Wednesday 12pm UTC', reason: 'General business content midweek' },
  length_assessment:   { status: 'optimal',  char_count: 600 },
};

const EXHAUSTED_INTEL = {
  hook_strength:       { rating: 'Weak',    reason: 'Generic opening — could be anyone' },
  cta_clarity:         { status: 'missing', suggestion: 'Add an explicit call to action' },
  optimal_posting_time:{ time: 'Monday 8am UTC', reason: 'Career content early week' },
  length_assessment:   { status: 'too_short', char_count: 200 },
};

const makeVariant = (intel) => ({
  id: 'v-1', personality: 'bold', label: 'Bold Approach',
  post: 'Test post', hashtags: [], engagement_score: 8, hook_strength: 'Strong',
  intelligence: intel,
});

// ---------------------------------------------------------------------------
// AC7 Story 3.2: empty / placeholder state
// ---------------------------------------------------------------------------

test('renders placeholder when variant is null', () => {
  render(<IntelligenceSidebar variant={null} />);
  expect(screen.getByText(/generate a post/i)).toBeInTheDocument();
});

test('renders placeholder when variant has no intelligence', () => {
  const variantNoIntel = { id: 'v-1', post: 'test', intelligence: null };
  render(<IntelligenceSidebar variant={variantNoIntel} />);
  // Should not crash; shows placeholder or nothing but no dimension rows
  expect(screen.queryByText(/Hook/i)).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC3: "All Green Lights" summary state
// ---------------------------------------------------------------------------

test('shows All Green status when all dimensions are optimal', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/all green/i)).toBeInTheDocument();
});

test('shows suggestion count when not all green', () => {
  render(<IntelligenceSidebar variant={makeVariant(WARNING_INTEL)} />);
  // Moderate hook + consider CTA = 2 tips
  expect(screen.getByText(/2 tip/i)).toBeInTheDocument();
});

test('shows 3 tips when all dimensions need attention', () => {
  render(<IntelligenceSidebar variant={makeVariant(EXHAUSTED_INTEL)} />);
  expect(screen.getByText(/3 tip/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC4: dimension rows rendered correctly
// ---------------------------------------------------------------------------

test('renders hook strength rating badge', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText('Strong')).toBeInTheDocument();
});

test('renders hook strength reason text', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/opens with a bold challenge/i)).toBeInTheDocument();
});

test('renders cta clarity status badge', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText('clear')).toBeInTheDocument();
});

test('renders cta suggestion text', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/direct question invites engagement/i)).toBeInTheDocument();
});

test('renders posting time', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/tuesday 10am utc/i)).toBeInTheDocument();
});

test('renders character count', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/900 chars/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC5: badge color classes for each state
// ---------------------------------------------------------------------------

test('applies green badge for Strong hook', () => {
  const { container } = render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  const greenBadges = container.querySelectorAll('.bg-green-100');
  expect(greenBadges.length).toBeGreaterThan(0);
});

test('applies amber badge for Moderate hook', () => {
  const { container } = render(<IntelligenceSidebar variant={makeVariant(WARNING_INTEL)} />);
  const amberBadges = container.querySelectorAll('.bg-amber-100');
  expect(amberBadges.length).toBeGreaterThan(0);
});

test('applies red badge for Weak hook', () => {
  const { container } = render(<IntelligenceSidebar variant={makeVariant(EXHAUSTED_INTEL)} />);
  const redBadges = container.querySelectorAll('.bg-red-100');
  expect(redBadges.length).toBeGreaterThan(0);
});

// ---------------------------------------------------------------------------
// AC6: collapse / expand toggle
// ---------------------------------------------------------------------------

test('collapses to icon strip on toggle click', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  fireEvent.click(screen.getByLabelText(/collapse/i));
  // After collapse, dimension rows should be gone
  expect(screen.queryByText(/opens with a bold challenge/i)).not.toBeInTheDocument();
});

test('expands again after second toggle click', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  fireEvent.click(screen.getByLabelText(/collapse/i));
  fireEvent.click(screen.getByLabelText(/expand/i));
  expect(screen.getByText(/opens with a bold challenge/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC2 Story 3.3: loading skeleton state
// ---------------------------------------------------------------------------

test('renders skeletons when isLoading=true', () => {
  const { container } = render(
    <IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} isLoading={true} />
  );
  const skeletons = container.querySelectorAll('.animate-pulse');
  expect(skeletons.length).toBeGreaterThan(0);
});

test('does not render dimension rows when isLoading=true', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} isLoading={true} />);
  expect(screen.queryByText(/opens with a bold challenge/i)).not.toBeInTheDocument();
});

test('renders dimension rows when isLoading=false', () => {
  render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} isLoading={false} />);
  expect(screen.getByText(/opens with a bold challenge/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC1 Story 3.3: instant update on variant switch
// ---------------------------------------------------------------------------

test('updates displayed intelligence when variant prop changes', () => {
  const { rerender } = render(<IntelligenceSidebar variant={makeVariant(ALL_GREEN_INTEL)} />);
  expect(screen.getByText(/opens with a bold challenge/i)).toBeInTheDocument();

  rerender(<IntelligenceSidebar variant={makeVariant(WARNING_INTEL)} />);
  expect(screen.getByText(/acceptable but predictable opener/i)).toBeInTheDocument();
  expect(screen.queryByText(/opens with a bold challenge/i)).not.toBeInTheDocument();
});
