import React, { useState } from 'react';
import './PostResult.css';
import apiService from '../services/apiService';
import VariantCard from './VariantCard';

const LINKEDIN_CHAR_LIMIT = 3000;

function PostResult({ result, onReset }) {
  // Initialise variants from multi-variant response or wrap legacy single response
  const initialVariants = result.variants && result.variants.length > 0
    ? result.variants
    : [result];

  const [variants, setVariants] = useState(initialVariants);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [hasUserSelected, setHasUserSelected] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [refinementFeedback, setRefinementFeedback] = useState('');
  const [error, setError] = useState('');
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('Post copied! Ready to paste in LinkedIn');
  const [isUpdating, setIsUpdating] = useState(false);

  const currentPost = variants[selectedIndex] || {};
  // P-7: guard against missing/non-string post field to prevent split() crash
  const post = typeof currentPost.post === 'string' ? currentPost.post : '';
  // Guard against missing/non-array hashtags to prevent map() crash
  const hashtags = Array.isArray(currentPost.hashtags) ? currentPost.hashtags : [];
  const charCount = post.length;
  const isOverLimit = charCount > LINKEDIN_CHAR_LIMIT;

  const handleSelectVariant = (index) => {
    setSelectedIndex(index);
    setHasUserSelected(true);
    setError('');
    setRefinementFeedback('');
  };

  const handleRefine = async () => {
    if (!refinementFeedback.trim()) {
      setError('Please enter refinement feedback');
      return;
    }

    setIsRefining(true);
    setError('');

    try {
      const refined = await apiService.refinePost({
        postText: post,
        feedback: refinementFeedback,
        variantId: currentPost.id,
        personality: currentPost.personality,
        label: currentPost.label,
      });

      // P-11: apply state update synchronously (no nested timeouts), single delay for animation
      setIsUpdating(true);
      setVariants((prev) => {
        const updated = [...prev];
        updated[selectedIndex] = {
          ...updated[selectedIndex],
          // P-8: guard all refinement fields — fall back to existing value if missing
          post: refined.refined_post ?? updated[selectedIndex].post,
          engagement_score: refined.engagement_score ?? updated[selectedIndex].engagement_score,
          hook_strength: refined.hook_strength || updated[selectedIndex].hook_strength,
          hashtags: Array.isArray(refined.hashtags) && refined.hashtags.length > 0
            ? refined.hashtags
            : updated[selectedIndex].hashtags,
          suggestions: Array.isArray(refined.suggestions) && refined.suggestions.length > 0
            ? refined.suggestions
            : updated[selectedIndex].suggestions,
          cta: refined.cta || updated[selectedIndex].cta,
          image_alt_text: refined.image_alt_text !== undefined
            ? refined.image_alt_text
            : updated[selectedIndex].image_alt_text,
        };
        return updated;
      });
      setTimeout(() => setIsUpdating(false), 300);

      setRefinementFeedback('');
      setToastMessage('Post refined successfully!');
      setShowCopyToast(true);
      setTimeout(() => setShowCopyToast(false), 3000);
    } catch (err) {
      setError(err.message || 'Failed to refine post');
    } finally {
      setIsRefining(false);
    }
  };

  const copyToClipboard = (variant) => {
    // Accept a specific variant to copy (from VariantCard onCopy), or fall back to currentPost.
    // P-7/P-10: safe local variables; optimistic toast; ?.catch() guards non-Promise return.
    const v = variant || currentPost;
    const safePost = typeof v.post === 'string' ? v.post : '';
    const safeHashtags = Array.isArray(v.hashtags) ? v.hashtags : [];
    const fullPost = `${safePost}\n\n${safeHashtags.map(tag => `#${tag}`).join(' ')}`;
    if (navigator.clipboard) {
      setToastMessage('Post copied! Ready to paste in LinkedIn');
      setShowCopyToast(true);
      setTimeout(() => setShowCopyToast(false), 3000);
      navigator.clipboard.writeText(fullPost)?.catch(() => {
        setToastMessage('Copy failed — please copy manually.');
      });
    } else {
      setToastMessage('Copy failed — please copy manually.');
      setShowCopyToast(true);
      setTimeout(() => setShowCopyToast(false), 3000);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return '#4caf50';
    if (score >= 6) return '#ff9800';
    return '#f44336';
  };

  const getHookColor = (strength) => {
    const colors = {
      'Exceptional': '#4caf50',
      'Strong': '#8bc34a',
      'Moderate': '#ff9800',
      'Weak': '#f44336'
    };
    return colors[strength] || '#666';
  };

  return (
    <div className="post-result">
      {showCopyToast && (
        <div className="toast-notification" role="status">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="9" fill="#059669" stroke="white" strokeWidth="2"/>
            <path d="M6 10l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{toastMessage}</span>
        </div>
      )}

      <div className={`result-card ${isRefining ? 'refining' : ''}`}>
        <div className="result-header">
          <h2>Generated Post</h2>
          <button onClick={onReset} className="btn-new">
            Create New Post
          </button>
        </div>

        {/* Variant Cards Row — all variants shown simultaneously (AC1, AC2, AC3, AC5) */}
        <div className="variant-cards-row" aria-label="Post variants">
          {variants.map((variant, index) => (
            <VariantCard
              key={variant.id || index}
              variant={variant}
              index={index}
              isSelected={index === selectedIndex}
              hasUserSelected={hasUserSelected}
              onSelect={() => handleSelectVariant(index)}
              onCopy={copyToClipboard}
            />
          ))}
        </div>

        {/* Engagement Metrics */}
        <div className={`metrics-panel ${isUpdating ? 'updating' : ''}`}>
          <div className="metric">
            <span className="metric-label">Engagement Score</span>
            <span
              className="metric-value"
              style={{ color: getScoreColor(currentPost.engagement_score) }}
              aria-label={`Engagement score: ${currentPost.engagement_score} out of 10`}
            >
              {currentPost.engagement_score}/10
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Hook Strength</span>
            <span
              className="metric-value"
              style={{ color: getHookColor(currentPost.hook_strength) }}
            >
              {currentPost.hook_strength}
            </span>
          </div>
        </div>

        {/* Generated Post */}
        <div className={`post-content ${isUpdating ? 'updating' : ''}`}>
          <label className="section-label">Post Text:</label>
          <div className="post-text">
            {post.split('\n').map((line, index) => (
              <React.Fragment key={index}>
                {line}
                {index < post.split('\n').length - 1 && <br />}
              </React.Fragment>
            ))}
          </div>
          <div
            className="char-count"
            style={{ color: isOverLimit ? '#f44336' : '#666' }}
            aria-label={`Character count: ${charCount} of ${LINKEDIN_CHAR_LIMIT}`}
          >
            {charCount.toLocaleString()} / {LINKEDIN_CHAR_LIMIT.toLocaleString()} characters
            {isOverLimit ? ' ⚠ Over LinkedIn limit' : ' ✓'}
          </div>
        </div>

        {/* Hashtags */}
        <div className={`hashtags-section ${isUpdating ? 'updating' : ''}`}>
          <label className="section-label">
            Hashtags: <span className="hashtag-count">({hashtags.length} — recommended 3–5)</span>
          </label>
          <div className="hashtags">
            {hashtags.map((tag, index) => (
              <span key={index} className="hashtag">#{tag}</span>
            ))}
          </div>
        </div>

        {/* Suggestions */}
        {currentPost.suggestions && currentPost.suggestions.length > 0 && (
          <div className={`suggestions-section ${isUpdating ? 'updating' : ''}`}>
            <label className="section-label">Optimization Suggestions</label>
            <ul className="suggestions-list">
              {currentPost.suggestions.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        {/* CTA */}
        {currentPost.cta && (
          <div className={`cta-section ${isUpdating ? 'updating' : ''}`}>
            <label className="section-label">Call to Action</label>
            <p className="cta-text">{currentPost.cta}</p>
          </div>
        )}

        {/* Suggested Image Concept */}
        {currentPost.image_alt_text && (
          <div className={`image-concept-section ${isUpdating ? 'updating' : ''}`}>
            <label className="section-label">Suggested Image Concept</label>
            <p className="image-alt-text">{currentPost.image_alt_text}</p>
          </div>
        )}

        {/* Copy action lives inside each VariantCard (AC4) */}

        {/* Refinement Section */}
        <div className="refinement-section">
          {isRefining && (
            <div className="refining-overlay">
              <div className="refining-spinner"></div>
              <p>Refining your post...</p>
            </div>
          )}

          <label className="section-label">Refine Post</label>
          <p className="refinement-hint">
            Provide feedback to improve the post (e.g., "Make it more concise", "Add a call-to-action")
          </p>

          <div className="refinement-input-group">
            <textarea
              value={refinementFeedback}
              onChange={(e) => setRefinementFeedback(e.target.value)}
              placeholder="Make it more engaging..."
              rows="3"
              disabled={isRefining}
              aria-label="Refinement feedback"
            />
            <button
              onClick={handleRefine}
              disabled={isRefining || !refinementFeedback.trim()}
              className="btn-refine"
            >
              {isRefining ? (
                <>
                  <span className="btn-spinner"></span>
                  Refining...
                </>
              ) : (
                'Refine Post'
              )}
            </button>
          </div>

          {error && <div className="error-message" role="alert">{error}</div>}
        </div>
      </div>
    </div>
  );
}

export default PostResult;
