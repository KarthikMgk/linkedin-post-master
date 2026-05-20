import React from 'react';

const PERSONALITY_COLORS = {
  bold:        { bg: '#FF6B6B', label: 'Bold' },
  structured:  { bg: '#4ECDC4', label: 'Structured' },
  provocative: { bg: '#9B59B6', label: 'Provocative' },
};

const getScoreColor = (score) => {
  if (score >= 8) return 'text-green-600 border-green-600';
  if (score >= 6) return 'text-amber-600 border-amber-600';
  return 'text-red-600 border-red-600';
};

function VariantCard({ variant, isSelected, hasUserSelected, onSelect, onCopy, index }) {
  const personality = PERSONALITY_COLORS[variant.personality] || { bg: '#666', label: variant.personality || 'Variant' };
  const safePost = typeof variant.post === 'string' ? variant.post : '';
  const safeHashtags = Array.isArray(variant.hashtags) ? variant.hashtags : [];
  const scoreColor = getScoreColor(variant.engagement_score);

  return (
    <div
      className={`min-w-[280px] flex-1 bg-white border rounded-xl shadow-sm p-6 flex flex-col gap-3 transition-opacity border-gray-200 animate-variant-fade-in ${
        isSelected ? 'border-2 border-primary shadow-lg' : ''
      } ${!isSelected && hasUserSelected ? 'opacity-60' : ''}`}
      style={{ animationDelay: `${index * 100}ms` }}
      data-testid={`variant-card-${index}`}
    >
      {/* Header: personality badge + score badge */}
      <div className="flex items-center justify-between gap-2 min-w-0">
        <span
          className="inline-block text-xs font-bold uppercase tracking-wide px-2 py-1 rounded-md text-white flex-shrink-1 min-w-0 overflow-hidden text-ellipsis"
          style={{ backgroundColor: personality.bg }}
          data-testid="personality-badge"
        >
          {variant.label || `${personality.label} Approach`}
        </span>
        <span
          className={`text-sm font-bold border-2 rounded-md px-2 py-0.5 whitespace-nowrap bg-white flex-shrink-0 ${scoreColor}`}
          data-testid="score-badge"
          aria-label={`Engagement score: ${variant.engagement_score} out of 10`}
        >
          {variant.engagement_score}/10
        </span>
      </div>

      {/* Hook strength */}
      {variant.hook_strength && (
        <div className="text-xs text-gray-600 p-2 bg-gray-50 rounded-md border border-gray-200" data-testid="hook-strength">
          Hook: <strong>{variant.hook_strength}</strong>
        </div>
      )}

      {/* Post text */}
      <div className="text-sm leading-relaxed text-gray-900 bg-gray-50 border border-gray-200 rounded-md p-4 flex-1" data-testid="post-text">
        {safePost.split('\n').map((line, i, arr) => (
          <React.Fragment key={i}>
            {line}
            {i < arr.length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>

      {/* Hashtags */}
      {safeHashtags.length > 0 && (
        <div className="flex flex-wrap gap-2" data-testid="hashtag-list">
          {safeHashtags.map((tag, i) => (
            <span key={i} className="bg-primary text-white px-3 py-0.5 rounded-md text-xs font-semibold">#{tag}</span>
          ))}
        </div>
      )}

      {/* Generated image */}
      {variant.image?.url && (
        <div className="mt-3 rounded-md overflow-hidden border border-gray-200">
          <img
            src={variant.image.url}
            alt={variant.image.alt_text || variant.image_alt_text || 'Generated LinkedIn image'}
            className="w-full h-auto block"
            style={{ aspectRatio: '1200/627', objectFit: 'cover' }}
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 mt-auto pt-3 border-t border-gray-100">
        <button
          className={`flex-1 py-3 px-4 bg-white text-gray-700 border rounded-md text-sm font-semibold transition-all hover:bg-gray-50 ${
            isSelected ? 'bg-primary text-white border-primary hover:bg-primary-dark' : 'border-gray-300 hover:border-primary hover:text-primary'
          }`}
          onClick={onSelect}
          aria-pressed={isSelected}
        >
          {isSelected ? '✓ Selected' : 'Select This Variant'}
        </button>
        <button
          className="py-3 px-4 bg-white text-gray-600 border border-gray-300 rounded-md text-sm font-semibold transition-all hover:bg-gray-50 hover:border-gray-400 whitespace-nowrap"
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
