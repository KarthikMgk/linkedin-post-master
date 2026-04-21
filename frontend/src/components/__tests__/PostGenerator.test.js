/**
 * Tests for PostGenerator component — Story 1.3
 * AC1: Loading state activates on submit; form becomes non-interactive
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import PostGenerator from '../PostGenerator';

// Mock apiService
jest.mock('../../services/apiService', () => ({
  __esModule: true,
  default: {
    generatePost: jest.fn(),
    refinePost: jest.fn(),
  },
}));

// Mutable quota state — can be overridden per-test block
// Must use `var` so the value is accessible inside the jest.mock hoisted factory
var mockQuotaRemaining = null;
jest.mock('../../context/AuthProvider', () => ({
  useAuth: () => ({ quotaRemaining: mockQuotaRemaining }),
}));

import apiService from '../../services/apiService';

const MOCK_RESULT = {
  success: true,
  post: 'AI is transforming enterprise.',
  hashtags: ['AIAgents', 'Tech', 'Future'],
  engagement_score: 8.5,
  hook_strength: 'Strong',
  suggestions: ['Add a data point'],
  cta: "What's your experience?",
  image_alt_text: 'A professional at a desk with a laptop.',
};

function renderGenerator(overrides = {}) {
  const props = {
    onGenerate: jest.fn(),
    onGenerating: jest.fn(),
    isLoading: false,
    ...overrides,
  };
  return { ...render(<PostGenerator {...props} />), ...props };
}

// ---------------------------------------------------------------------------
// AC1 — loading state
// ---------------------------------------------------------------------------

test('Generate Post button is present and enabled initially', () => {
  renderGenerator();
  expect(screen.getByRole('button', { name: /generate post/i })).toBeEnabled();
});

test('AC1: button shows Generating... when isLoading=true', () => {
  renderGenerator({ isLoading: true });
  expect(screen.getByRole('button', { name: /generating/i })).toBeDisabled();
});

test('AC1: textarea is disabled when isLoading=true', () => {
  renderGenerator({ isLoading: true });
  expect(screen.getByPlaceholderText(/enter your content/i)).toBeDisabled();
});

test('AC1: onGenerating is called before API resolves', async () => {
  let resolvePost;
  apiService.generatePost.mockReturnValue(new Promise(res => { resolvePost = res; }));
  const { onGenerating } = renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  expect(onGenerating).toHaveBeenCalledTimes(1);

  // Cleanup
  await act(async () => resolvePost(MOCK_RESULT));
});

test('AC1: apiService.generatePost is called with text payload', async () => {
  apiService.generatePost.mockResolvedValue(MOCK_RESULT);
  const { onGenerate } = renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'My post idea' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  expect(apiService.generatePost).toHaveBeenCalledWith(
    expect.objectContaining({ text: 'My post idea' })
  );
  await waitFor(() => expect(onGenerate).toHaveBeenCalledWith(MOCK_RESULT));
});

test('onGenerate called with result on success', async () => {
  apiService.generatePost.mockResolvedValue(MOCK_RESULT);
  const { onGenerate } = renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Content here' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  await waitFor(() => expect(onGenerate).toHaveBeenCalledWith(MOCK_RESULT));
});

// ---------------------------------------------------------------------------
// Empty input validation
// ---------------------------------------------------------------------------

test('shows error message on empty submit', async () => {
  renderGenerator();
  fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  expect(await screen.findByText(/please provide at least one input/i)).toBeInTheDocument();
});

test('does not call apiService on empty submit', () => {
  renderGenerator();
  fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  expect(apiService.generatePost).not.toHaveBeenCalled();
});

// ---------------------------------------------------------------------------
// Error state
// ---------------------------------------------------------------------------

test('shows API error message when generatePost rejects', async () => {
  apiService.generatePost.mockRejectedValue(new Error('Claude API rate limit reached'));
  renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some idea' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  await waitFor(() =>
    expect(screen.getByText(/claude api rate limit reached/i)).toBeInTheDocument()
  );
});

// ---------------------------------------------------------------------------
// AC3 — network error message (Story 1.4)
// ---------------------------------------------------------------------------

test('AC3: shows network error message when backend unreachable', async () => {
  apiService.generatePost.mockRejectedValue(
    new Error('Unable to connect to the server. Please check your connection and try again.')
  );
  renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  await waitFor(() =>
    expect(screen.getByText(/unable to connect to the server/i)).toBeInTheDocument()
  );
});

test('AC3: Generate button re-enabled after network error', async () => {
  apiService.generatePost.mockRejectedValue(
    new Error('Unable to connect to the server. Please check your connection and try again.')
  );
  renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  await waitFor(() =>
    expect(screen.getByRole('button', { name: /generate post/i })).toBeEnabled()
  );
});

// ---------------------------------------------------------------------------
// AC5 — timeout message (Story 1.4)
// ---------------------------------------------------------------------------

test('AC5: shows timeout message when request times out', async () => {
  apiService.generatePost.mockRejectedValue(
    new Error('Generation is taking longer than expected. Please try again.')
  );
  renderGenerator();

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  await waitFor(() =>
    expect(screen.getByText(/taking longer than expected/i)).toBeInTheDocument()
  );
});

test('AC5: loading state clears after timeout', async () => {
  apiService.generatePost.mockRejectedValue(
    new Error('Generation is taking longer than expected. Please try again.')
  );
  renderGenerator({ isLoading: false });

  await act(async () => {
    fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
      target: { value: 'Some content' },
    });
    fireEvent.click(screen.getByRole('button', { name: /generate post/i }));
  });

  // After rejection the button label returns to "Generate Post" (not "Generating...")
  await waitFor(() =>
    expect(screen.queryByRole('button', { name: /generating/i })).not.toBeInTheDocument()
  );
});

// ---------------------------------------------------------------------------
// Reset
// ---------------------------------------------------------------------------

test('Reset button clears text input', () => {
  renderGenerator();
  fireEvent.change(screen.getByPlaceholderText(/enter your content/i), {
    target: { value: 'Some content' },
  });
  fireEvent.click(screen.getByRole('button', { name: /reset/i }));
  expect(screen.getByPlaceholderText(/enter your content/i)).toHaveValue('');
});

// ---------------------------------------------------------------------------
// PDF file input handler
// ---------------------------------------------------------------------------

test('accepts valid PDF file', () => {
  renderGenerator();
  const pdfFile = new File(['pdf content'], 'report.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"][accept=".pdf"]');
  Object.defineProperty(input, 'files', { value: [pdfFile], configurable: true });
  fireEvent.change(input);
  expect(screen.getByText(/selected: report\.pdf/i)).toBeInTheDocument();
});

test('shows error for non-PDF file', () => {
  renderGenerator();
  const badFile = new File(['content'], 'notes.txt', { type: 'text/plain' });
  const input = document.querySelector('input[type="file"][accept=".pdf"]');
  Object.defineProperty(input, 'files', { value: [badFile], configurable: true });
  fireEvent.change(input);
  expect(screen.getByText(/please select a valid pdf file/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// Image file input handler
// ---------------------------------------------------------------------------

test('accepts valid image files', () => {
  renderGenerator();
  const img = new File(['img'], 'photo.png', { type: 'image/png' });
  const input = document.querySelector('input[accept="image/*"]');
  Object.defineProperty(input, 'files', { value: [img], configurable: true });
  fireEvent.change(input);
  expect(screen.getByText(/selected: 1 image/i)).toBeInTheDocument();
});

test('shows warning when non-image files included in image upload', () => {
  renderGenerator();
  const img = new File(['img'], 'photo.png', { type: 'image/png' });
  const doc = new File(['doc'], 'doc.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[accept="image/*"]');
  Object.defineProperty(input, 'files', { value: [img, doc], configurable: true });
  fireEvent.change(input);
  expect(screen.getByText(/some files were not valid images/i)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// AC9 — quota exhausted state (Story 5.3)
// ---------------------------------------------------------------------------

describe('quota exhausted state', () => {
  beforeEach(() => {
    mockQuotaRemaining = 0;
  });

  afterEach(() => {
    mockQuotaRemaining = null;
  });

  test('AC9: Generate button is disabled when quotaRemaining is 0', () => {
    renderGenerator();
    expect(screen.getByRole('button', { name: /generate post/i })).toBeDisabled();
  });

  test('AC9: button has descriptive title when disabled by quota', () => {
    renderGenerator();
    const btn = screen.getByRole('button', { name: /generate post/i });
    expect(btn).toHaveAttribute('title', expect.stringMatching(/daily limit reached/i));
  });
});

describe('quota normal state', () => {
  beforeEach(() => {
    mockQuotaRemaining = 5;
  });

  afterEach(() => {
    mockQuotaRemaining = null;
  });

  test('Generate button is enabled when quota remaining > 0', () => {
    renderGenerator();
    expect(screen.getByRole('button', { name: /generate post/i })).toBeEnabled();
  });
});
