import React from 'react';
import './VariantCard.css';

const PERSONALITY_COLORS = {
  bold:        { bg: '#FF6B6B', label: 'Bold' },
  structured:  { bg: '#4ECDC4', label: 'Structured' },
  provocative: { bg: '#9B59B6', label: 'Provocative' },
};

const getScoreColor = (score) => {
  if (score >= 8) return '#4caf50';
  if (score >= 6) return '#ff9800';
  return '#f44336';
};

function VariantCard({ variant, isSelected, hasUserSelected, onSelect, onCopy, index }) {
  const personality = PERSONALITY_COLORS[variant.personality] || { bg: '#666', label: variant.personality || 'Variant' };
  const safePost = typeof variant.post === 'string' ? variant.post : '';
  const safeHashtags = Array.isArray(variant.hashtags) ? variant.hashtags : [];
  const scoreColor = getScoreColor(variant.engagement_score);

  const cardClasses = [
    'variant-card',
    isSelected ? 'variant-card--selected' : '',
    !isSelected && hasUserSelected ? 'variant-card--dimmed' : '',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={cardClasses}
      style={{ animationDelay: `${index * 100}ms` }}
      data-testid={`variant-card-${index}`}
    >
      {/* Header: personality badge + score badge */}
      <div className="variant-card__header">
        <span
          className="variant-card__badge"
          style={{ backgroundColor: personality.bg }}
          data-testid="personality-badge"
        >
          {variant.label || `${personality.label} Approach`}
        </span>
        <span
          className="variant-card__score-badge"
          style={{ color: scoreColor, borderColor: scoreColor }}
          data-testid="score-badge"
          aria-label={`Engagement score: ${variant.engagement_score} out of 10`}
        >
          {variant.engagement_score}/10
        </span>
      </div>

      {/* Hook strength */}
      {variant.hook_strength && (
        <div className="variant-card__hook" data-testid="hook-strength">
          Hook: <strong>{variant.hook_strength}</strong>
        </div>
      )}

      {/* Post text */}
      <div className="variant-card__post" data-testid="post-text">
        {safePost.split('\n').map((line, i, arr) => (
          <React.Fragment key={i}>
            {line}
            {i < arr.length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>

      {/* Hashtags */}
      {safeHashtags.length > 0 && (
        <div className="variant-card__hashtags" data-testid="hashtag-list">
          {safeHashtags.map((tag, i) => (
            <span key={i} className="variant-card__hashtag">#{tag}</span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="variant-card__actions">
        <button
          className={`variant-card__select-btn ${isSelected ? 'variant-card__select-btn--active' : ''}`}
          onClick={onSelect}
          aria-pressed={isSelected}
        >
          {isSelected ? '✓ Selected' : 'Select This Variant'}
        </button>
        <button
          className="variant-card__copy-btn"
          onClick={() => onCopy(variant)}
          aria-label="Copy to clipboard"
        >
          Copy
        </button>
      </div>
    </div>
  );
}

export default VariantCard;
