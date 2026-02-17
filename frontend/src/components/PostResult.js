import React, { useState } from 'react';
import './PostResult.css';
import apiService from '../services/apiService';

function PostResult({ result, onReset }) {
  const [isRefining, setIsRefining] = useState(false);
  const [refinementFeedback, setRefinementFeedback] = useState('');
  const [currentPost, setCurrentPost] = useState(result);
  const [error, setError] = useState('');
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('Copied to clipboard!');
  const [isUpdating, setIsUpdating] = useState(false);

  const handleRefine = async () => {
    if (!refinementFeedback.trim()) {
      setError('Please enter refinement feedback');
      return;
    }

    setIsRefining(true);
    setError('');

    try {
      const refined = await apiService.refinePost({
        postText: currentPost.post,
        feedback: refinementFeedback
      });

      // Trigger fade-out animation
      setIsUpdating(true);

      // Wait for fade-out, then update content
      setTimeout(() => {
        setCurrentPost({
          ...currentPost,
          post: refined.refined_post,
          engagement_score: refined.engagement_score,
          hook_strength: refined.hook_strength || currentPost.hook_strength,
          hashtags: refined.hashtags || currentPost.hashtags,
          suggestions: refined.suggestions || currentPost.suggestions
        });

        // Trigger fade-in animation
        setTimeout(() => setIsUpdating(false), 50);
      }, 300);

      setRefinementFeedback('');

      // Show success toast
      setToastMessage('Post refined successfully!');
      setShowCopyToast(true);
      setTimeout(() => setShowCopyToast(false), 3000);
    } catch (err) {
      setError(err.message || 'Failed to refine post');
      setIsUpdating(false);
    } finally {
      setIsRefining(false);
    }
  };

  const copyToClipboard = () => {
    const fullPost = `${currentPost.post}\n\n${currentPost.hashtags.map(tag => `#${tag}`).join(' ')}`;
    navigator.clipboard.writeText(fullPost);

    // Show toast notification
    setToastMessage('Copied to clipboard!');
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3000);
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
      {/* Toast Notification */}
      {showCopyToast && (
        <div className="toast-notification">
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

        {/* Engagement Metrics */}
        <div className={`metrics-panel ${isUpdating ? 'updating' : ''}`}>
          <div className="metric">
            <span className="metric-label">Engagement Score</span>
            <span
              className="metric-value"
              style={{ color: getScoreColor(currentPost.engagement_score) }}
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
            {currentPost.post.split('\n').map((line, index) => (
              <React.Fragment key={index}>
                {line}
                {index < currentPost.post.split('\n').length - 1 && <br />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Hashtags */}
        <div className={`hashtags-section ${isUpdating ? 'updating' : ''}`}>
          <label className="section-label">Hashtags:</label>
          <div className="hashtags">
            {currentPost.hashtags.map((tag, index) => (
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

        {/* Actions */}
        <div className="actions">
          <button onClick={copyToClipboard} className="btn-action">
            Copy to Clipboard
          </button>
        </div>

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

          {error && <div className="error-message">{error}</div>}
        </div>
      </div>
    </div>
  );
}

export default PostResult;
