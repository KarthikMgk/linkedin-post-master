/**
 * Tests for PostResult component — Story 1.3
 * AC2: All fields render  AC3: Copy toast text  AC4: Refinement
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import PostResult from '../PostResult';

jest.mock('../../services/apiService', () => ({
  __esModule: true,
  default: {
    generatePost: jest.fn(),
    refinePost: jest.fn(),
  },
}));

import apiService from '../../services/apiService';

// Mock clipboard
Object.assign(navigator, {
  clipboard: { writeText: jest.fn() },
});

const MOCK_RESULT = {
  post: 'AI agents are transforming enterprise.\n\nHere is what most people miss.',
  hashtags: ['AIAgents', 'EnterpriseTech', 'FutureOfWork'],
  engagement_score: 8.5,
  hook_strength: 'Strong',
  suggestions: ['Add a specific data point', 'End with a question'],
  cta: "What's your experience with AI agents?",
  image_alt_text: 'A professional at a whiteboard drawing an AI workflow diagram.',
};

const MOCK_REFINED = {
  success: true,
  refined_post: 'AI agents are your new colleagues.\n\nHere is the truth nobody talks about.',
  engagement_score: 9.0,
  hook_strength: 'Exceptional',
  hashtags: ['AIAgents', 'Innovation'],
  suggestions: ['Near perfect!'],
  cta: 'Drop your thoughts below',
  changes_made: ['make it punchier'],
};

function renderResult(overrides = {}) {
  const props = {
    result: { ...MOCK_RESULT, ...overrides },
    onReset: jest.fn(),
  };
  return { ...render(<PostResult {...props} />), ...props };
}

// ---------------------------------------------------------------------------
// AC2 — all fields render
// ---------------------------------------------------------------------------

test('AC2: post text renders with content', () => {
  renderResult();
  expect(screen.getByText(/ai agents are transforming enterprise/i)).toBeInTheDocument();
});

test('AC2: engagement score displays as X/10', () => {
  renderResult();
  expect(screen.getByText('8.5/10')).toBeInTheDocument();
});

test('AC2: hook strength label renders', () => {
  renderResult();
  expect(screen.getByText('Strong')).toBeInTheDocument();
});

test('AC2: hashtags render with # prefix', () => {
  renderResult();
  expect(screen.getByText('#AIAgents')).toBeInTheDocument();
  expect(screen.getByText('#EnterpriseTech')).toBeInTheDocument();
  expect(screen.getByText('#FutureOfWork')).toBeInTheDocument();
});

test('AC2: improvement suggestions render', () => {
  renderResult();
  expect(screen.getByText('Add a specific data point')).toBeInTheDocument();
  expect(screen.getByText('End with a question')).toBeInTheDocument();
});

test('AC2: CTA renders', () => {
  renderResult();
  expect(screen.getByText(/what's your experience with ai agents/i)).toBeInTheDocument();
});

test('AC2: image alt-text renders as Suggested Image Concept', () => {
  renderResult();
  expect(screen.getByText(/suggested image concept/i)).toBeInTheDocument();
  expect(screen.getByText(/ai workflow diagram/i)).toBeInTheDocument();
});

test('AC2: character count is displayed', () => {
  renderResult();
  expect(screen.getByText(/\/ 3,000 characters/i)).toBeInTheDocument();
});

test('AC2: character count shows correct number', () => {
  renderResult();
  const expectedCount = MOCK_RESULT.post.length;
  expect(screen.getByText(new RegExp(`${expectedCount}`))).toBeInTheDocument();
});

test('AC2: character count shows green checkmark when under limit', () => {
  renderResult();
  expect(screen.getByText(/✓/)).toBeInTheDocument();
});

test('AC2: character count shows warning when over 3000 chars', () => {
  const longPost = 'x'.repeat(3001);
  renderResult({ post: longPost });
  expect(screen.getByText(/over linkedin limit/i)).toBeInTheDocument();
});

test('AC2: hashtag count indicator renders', () => {
  renderResult();
  expect(screen.getByText(/3 — recommended 3–5/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC2 — conditional rendering
// ---------------------------------------------------------------------------

test('CTA section hidden when cta is empty', () => {
  renderResult({ cta: '' });
  expect(screen.queryByText(/call to action/i)).not.toBeInTheDocument();
});

test('Suggested Image Concept hidden when image_alt_text is empty', () => {
  renderResult({ image_alt_text: '' });
  expect(screen.queryByText(/suggested image concept/i)).not.toBeInTheDocument();
});

test('Suggestions section hidden when suggestions array is empty', () => {
  renderResult({ suggestions: [] });
  expect(screen.queryByText(/optimization suggestions/i)).not.toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC3 — copy to clipboard
// ---------------------------------------------------------------------------

test('AC3: Copy to Clipboard button is present', () => {
  renderResult();
  expect(screen.getByRole('button', { name: /copy to clipboard/i })).toBeInTheDocument();
});

test('AC3: clicking Copy calls navigator.clipboard.writeText', () => {
  renderResult();
  fireEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
  expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(1);
});

test('AC3: clipboard content includes post text and hashtags', () => {
  renderResult();
  fireEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
  const clipboardArg = navigator.clipboard.writeText.mock.calls[0][0];
  expect(clipboardArg).toContain('AI agents are transforming enterprise');
  expect(clipboardArg).toContain('#AIAgents');
  expect(clipboardArg).toContain('#EnterpriseTech');
});

test('AC3: toast shows "Post copied! Ready to paste in LinkedIn"', async () => {
  renderResult();
  fireEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
  expect(await screen.findByText('Post copied! Ready to paste in LinkedIn')).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC4 — refinement
// ---------------------------------------------------------------------------

test('AC4: Refine Post button is present', () => {
  renderResult();
  expect(screen.getByRole('button', { name: /refine post/i })).toBeInTheDocument();
});

test('AC4: Refine Post button disabled when feedback is empty', () => {
  renderResult();
  expect(screen.getByRole('button', { name: /refine post/i })).toBeDisabled();
});

test('AC4: apiService.refinePost called with correct args', async () => {
  apiService.refinePost.mockResolvedValue(MOCK_REFINED);
  renderResult();

  fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
    target: { value: 'make it punchier' },
  });

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  expect(apiService.refinePost).toHaveBeenCalledWith(
    expect.objectContaining({
      postText: MOCK_RESULT.post,
      feedback: 'make it punchier',
    })
  );
});

test('AC4: refined post text replaces original', async () => {
  apiService.refinePost.mockResolvedValue(MOCK_REFINED);
  renderResult();

  fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
    target: { value: 'make it punchier' },
  });

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  await waitFor(() =>
    expect(screen.getByText(/ai agents are your new colleagues/i)).toBeInTheDocument()
  );
});

test('AC4: engagement score updates after refinement', async () => {
  apiService.refinePost.mockResolvedValue(MOCK_REFINED);
  renderResult();

  fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
    target: { value: 'punchy' },
  });

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  await waitFor(() => expect(screen.getByText('9/10')).toBeInTheDocument());
});

test('AC4: refinement feedback cleared after successful refine', async () => {
  apiService.refinePost.mockResolvedValue(MOCK_REFINED);
  renderResult();

  const textarea = screen.getByLabelText(/refinement feedback/i);
  fireEvent.change(textarea, { target: { value: 'punchy' } });

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  await waitFor(() => expect(textarea).toHaveValue(''));
});

test('AC4: error shown when refinement fails', async () => {
  apiService.refinePost.mockRejectedValue(new Error('Rate limit reached'));
  renderResult();

  fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
    target: { value: 'punchy' },
  });

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  await waitFor(() =>
    expect(screen.getByRole('alert')).toHaveTextContent(/rate limit reached/i)
  );
});

// ---------------------------------------------------------------------------
// AC4 (Story 1.4) — image generation unavailable notice
// ---------------------------------------------------------------------------

test('AC4: image unavailable notice absent by default', () => {
  renderResult();
  expect(screen.queryByText(/image generation unavailable/i)).not.toBeInTheDocument();
});

test('AC4: image unavailable notice never shown (feature not yet wired)', () => {
  renderResult({ imageGenerationFailed: true });
  expect(screen.queryByText(/image generation unavailable/i)).not.toBeInTheDocument();
});

test('AC4: full text post still displays when imageGenerationFailed=true', () => {
  renderResult({ imageGenerationFailed: true });
  expect(screen.getByText(/ai agents are transforming enterprise/i)).toBeInTheDocument();
  expect(screen.getByText('#AIAgents')).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC5 — loading state visible during refine
// ---------------------------------------------------------------------------

test('AC5: Refining... shown while refine is in progress', async () => {
  let resolveRefine;
  apiService.refinePost.mockReturnValue(new Promise(res => { resolveRefine = res; }));
  renderResult();

  fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
    target: { value: 'make it punchy' },
  });

  act(() => {
    fireEvent.click(screen.getByRole('button', { name: /refine post/i }));
  });

  expect(await screen.findByText(/refining\.\.\./i)).toBeInTheDocument();

  await act(async () => resolveRefine(MOCK_REFINED));
});
