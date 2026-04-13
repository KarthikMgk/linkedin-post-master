/**
 * Tests for VariantCard component — Story 2.2
 * AC2: Badge content/colors  AC3: Selected/dimmed state  AC4: Copy action
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import VariantCard from '../VariantCard';

// Mock clipboard
Object.assign(navigator, {
  clipboard: { writeText: jest.fn() },
});

const MOCK_VARIANT = {
  id: 'variant-001',
  personality: 'bold',
  label: 'Bold Approach',
  post: 'Test post line one.\n\nSecond paragraph here.',
  hashtags: ['Tech', 'AI', 'Innovation'],
  engagement_score: 8.5,
  hook_strength: 'Strong',
  suggestions: ['Add a data point'],
  cta: 'What do you think?',
};

function renderCard(variantOverrides = {}, propOverrides = {}) {
  const props = {
    variant: { ...MOCK_VARIANT, ...variantOverrides },
    isSelected: false,
    hasUserSelected: false,
    onSelect: jest.fn(),
    onCopy: jest.fn(),
    index: 0,
    ...propOverrides,
  };
  return { ...render(<VariantCard {...props} />), ...props };
}

// ---------------------------------------------------------------------------
// AC2 — Personality badge
// ---------------------------------------------------------------------------

test('AC2: renders personality label in badge', () => {
  renderCard();
  expect(screen.getByTestId('personality-badge')).toHaveTextContent('Bold Approach');
});

test('AC2: bold personality badge has red background (#FF6B6B)', () => {
  renderCard({ personality: 'bold', label: 'Bold Approach' });
  const badge = screen.getByTestId('personality-badge');
  expect(badge).toHaveStyle({ backgroundColor: '#FF6B6B' });
});

test('AC2: structured personality badge has teal background (#4ECDC4)', () => {
  renderCard({ personality: 'structured', label: 'Structured Approach' });
  const badge = screen.getByTestId('personality-badge');
  expect(badge).toHaveStyle({ backgroundColor: '#4ECDC4' });
});

test('AC2: provocative personality badge has purple background (#9B59B6)', () => {
  renderCard({ personality: 'provocative', label: 'Provocative Approach' });
  const badge = screen.getByTestId('personality-badge');
  expect(badge).toHaveStyle({ backgroundColor: '#9B59B6' });
});

// ---------------------------------------------------------------------------
// AC2 — Engagement score badge
// ---------------------------------------------------------------------------

test('AC2: score ≥8 renders green score badge', () => {
  renderCard({ engagement_score: 9.0 });
  const badge = screen.getByTestId('score-badge');
  expect(badge).toHaveStyle({ color: '#4caf50' });
});

test('AC2: score 6–7 renders amber score badge', () => {
  renderCard({ engagement_score: 6.5 });
  const badge = screen.getByTestId('score-badge');
  expect(badge).toHaveStyle({ color: '#ff9800' });
});

test('AC2: score <6 renders red score badge', () => {
  renderCard({ engagement_score: 4.0 });
  const badge = screen.getByTestId('score-badge');
  expect(badge).toHaveStyle({ color: '#f44336' });
});

test('AC2: score badge shows value formatted as X/10', () => {
  renderCard({ engagement_score: 8.5 });
  expect(screen.getByTestId('score-badge')).toHaveTextContent('8.5/10');
});

// ---------------------------------------------------------------------------
// AC2 — Post text and hashtags
// ---------------------------------------------------------------------------

test('AC2: renders post text content', () => {
  renderCard();
  expect(screen.getByTestId('post-text')).toHaveTextContent('Test post line one.');
});

test('AC2: post text with \\n renders both paragraphs', () => {
  renderCard();
  expect(screen.getByTestId('post-text')).toHaveTextContent('Second paragraph here.');
});

test('AC2: renders hashtags with # prefix', () => {
  renderCard();
  expect(screen.getByTestId('hashtag-list')).toHaveTextContent('#Tech');
  expect(screen.getByTestId('hashtag-list')).toHaveTextContent('#AI');
  expect(screen.getByTestId('hashtag-list')).toHaveTextContent('#Innovation');
});

test('AC2: empty hashtags array renders no hashtag list', () => {
  renderCard({ hashtags: [] });
  expect(screen.queryByTestId('hashtag-list')).not.toBeInTheDocument();
});

test('AC2: non-array hashtags field renders no hashtag list (null guard)', () => {
  renderCard({ hashtags: null });
  expect(screen.queryByTestId('hashtag-list')).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC3 — Selected / dimmed state
// ---------------------------------------------------------------------------

test('AC3: variant-card--selected class present when isSelected=true', () => {
  renderCard({}, { isSelected: true, hasUserSelected: true });
  expect(screen.getByTestId('variant-card-0')).toHaveClass('variant-card--selected');
});

test('AC3: variant-card--selected class absent when isSelected=false', () => {
  renderCard({}, { isSelected: false });
  expect(screen.getByTestId('variant-card-0')).not.toHaveClass('variant-card--selected');
});

test('AC3: variant-card--dimmed class present when not selected and hasUserSelected=true', () => {
  renderCard({}, { isSelected: false, hasUserSelected: true });
  expect(screen.getByTestId('variant-card-0')).toHaveClass('variant-card--dimmed');
});

test('AC3: variant-card--dimmed class absent when hasUserSelected=false (no selection yet)', () => {
  renderCard({}, { isSelected: false, hasUserSelected: false });
  expect(screen.getByTestId('variant-card-0')).not.toHaveClass('variant-card--dimmed');
});

test('AC3: Select This Variant button triggers onSelect callback', () => {
  const { onSelect } = renderCard();
  fireEvent.click(screen.getByRole('button', { name: /select this variant/i }));
  expect(onSelect).toHaveBeenCalledTimes(1);
});

test('AC3: selected card shows ✓ Selected label on button', () => {
  renderCard({}, { isSelected: true });
  expect(screen.getByRole('button', { name: /selected/i })).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC4 — Copy action
// ---------------------------------------------------------------------------

test('AC4: Copy button triggers onCopy with variant object', () => {
  const { onCopy, variant } = renderCard();
  fireEvent.click(screen.getByRole('button', { name: /copy/i }));
  expect(onCopy).toHaveBeenCalledTimes(1);
  expect(onCopy).toHaveBeenCalledWith(variant);
});

// ---------------------------------------------------------------------------
// AC1 — Animation delay
// ---------------------------------------------------------------------------

test('AC1: card has animationDelay based on index prop', () => {
  renderCard({}, { index: 2 });
  expect(screen.getByTestId('variant-card-2')).toHaveStyle({ animationDelay: '200ms' });
});

test('AC1: first card has 0ms animation delay', () => {
  renderCard({}, { index: 0 });
  expect(screen.getByTestId('variant-card-0')).toHaveStyle({ animationDelay: '0ms' });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

test('renders gracefully when post is missing (undefined)', () => {
  renderCard({ post: undefined });
  expect(screen.getByTestId('post-text')).toBeInTheDocument();
});

test('falls back to unknown personality gracefully', () => {
  renderCard({ personality: 'unknown', label: 'Unknown Approach' });
  expect(screen.getByTestId('personality-badge')).toHaveTextContent('Unknown Approach');
});
