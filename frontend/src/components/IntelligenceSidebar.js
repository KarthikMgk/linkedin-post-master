import React, { useCallback, useEffect, useRef, useState } from 'react';

// ---------------------------------------------------------------------------
// Color mappings
// ---------------------------------------------------------------------------

const ratingBadgeColor = {
  Exceptional: 'bg-green-100 text-green-800 border border-green-200',
  Strong:      'bg-green-100 text-green-800 border border-green-200',
  Moderate:    'bg-amber-100 text-amber-800 border border-amber-200',
  Weak:        'bg-red-100  text-red-800  border border-red-200',
};

const statusBadgeColor = {
  clear:     'bg-green-100 text-green-800 border border-green-200',
  optimal:   'bg-green-100 text-green-800 border border-green-200',
  consider:  'bg-amber-100 text-amber-800 border border-amber-200',
  too_short: 'bg-amber-100 text-amber-800 border border-amber-200',
  too_long:  'bg-amber-100 text-amber-800 border border-amber-200',
  missing:   'bg-red-100  text-red-800  border border-red-200',
};

const dotColor = {
  Exceptional: 'bg-green-500',
  Strong:      'bg-green-500',
  clear:       'bg-green-500',
  optimal:     'bg-green-500',
  Moderate:    'bg-amber-500',
  consider:    'bg-amber-500',
  too_short:   'bg-amber-500',
  too_long:    'bg-amber-500',
  Weak:        'bg-red-500',
  missing:     'bg-red-500',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isAllGreen(intel) {
  if (!intel) return false;
  return (
    ['Strong', 'Exceptional'].includes(intel.hook_strength?.rating) &&
    intel.cta_clarity?.status === 'clear' &&
    intel.length_assessment?.status === 'optimal'
  );
}

function countSuggestions(intel) {
  if (!intel) return 0;
  let n = 0;
  if (!['Strong', 'Exceptional'].includes(intel.hook_strength?.rating)) n++;
  if (intel.cta_clarity?.status !== 'clear') n++;
  if (intel.length_assessment?.status !== 'optimal') n++;
  return n;
}

function lengthDetail(intel) {
  const status = intel?.length_assessment?.status;
  if (status === 'too_short') return 'Post is short — consider adding more context or a story.';
  if (status === 'too_long')  return 'Post may be too long — LinkedIn truncates after ~3000 characters.';
  return 'Length is in the optimal range for LinkedIn engagement.';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <div className="animate-pulse space-y-2 p-3 rounded-lg border border-gray-100">
      <div className="flex items-center justify-between gap-2">
        <div className="h-3 bg-gray-200 rounded w-1/3" />
        <div className="h-5 bg-gray-200 rounded-full w-16" />
      </div>
      <div className="h-3 bg-gray-200 rounded w-5/6" />
    </div>
  );
}

function DimensionRow({ label, icon, badge, badgeColor, detail }) {
  return (
    <div className="p-3 rounded-lg border border-gray-100 space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
          <span>{icon}</span> {label}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${badgeColor}`}>
          {badge}
        </span>
      </div>
      <p className="text-xs text-gray-600 leading-relaxed">{detail}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ImageVisualSection sub-component (AC4 — Story 4.2)
// ---------------------------------------------------------------------------

function ImageVisualSection({ variant, onRegenerateImage, isRegenerating }) {
  const [showDirectionInput, setShowDirectionInput] = useState(false);
  const [customDirection, setCustomDirection] = useState('');

  const hasImage = !!variant?.image?.url;
  const promptText = variant?.image?.prompt_used || variant?.image_description || '';
  const rationale = variant?.intelligence?.image_visual_rationale || '';

  const handleRegenerate = useCallback(() => {
    if (!showDirectionInput) {
      setShowDirectionInput(true);
      return;
    }
    if (onRegenerateImage) onRegenerateImage(customDirection);
    setShowDirectionInput(false);
    setCustomDirection('');
  }, [showDirectionInput, customDirection, onRegenerateImage]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter') handleRegenerate();
      if (e.key === 'Escape') { setShowDirectionInput(false); setCustomDirection(''); }
    },
    [handleRegenerate]
  );

  return (
    <div className="p-3 rounded-lg border border-gray-100 space-y-1.5">
      {/* Header row — matches DimensionRow style */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
          <span>🖼️</span> Image Visual
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap border ${
          hasImage
            ? 'bg-green-100 text-green-800 border-green-200'
            : 'bg-gray-100 text-gray-500 border-gray-200'
        }`}>
          {hasImage ? 'Ready' : '—'}
        </span>
      </div>

      {/* Rationale — the "why" explanation; prompt shown only as tooltip */}
      <p
        className="text-xs text-gray-600 leading-relaxed"
        title={promptText || undefined}
      >
        {rationale || (hasImage ? 'Image generated.' : 'No image generated.')}
      </p>

      {/* Regenerate controls */}
      {showDirectionInput && (
        <input
          type="text"
          value={customDirection}
          onChange={(e) => setCustomDirection(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Custom direction (optional)…"
          className="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
          autoFocus
        />
      )}
      <button
        onClick={handleRegenerate}
        disabled={isRegenerating}
        className="text-xs text-blue-600 border border-blue-200 rounded px-2 py-1 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
      >
        {isRegenerating ? (
          <><span className="animate-spin inline-block w-3 h-3 border border-blue-400 border-t-transparent rounded-full" /> Regenerating…</>
        ) : showDirectionInput ? 'Go' : '↺ Regenerate'}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

function IntelligenceSidebar({ variant, isLoading = false, onRegenerateImage, isRegenerating = false }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const prevAllGreenRef = useRef(false);

  const intel = variant?.intelligence;
  const allGreen = isAllGreen(intel);
  const suggestionCount = countSuggestions(intel);

  // Trigger celebration animation when transitioning to all-green
  useEffect(() => {
    if (allGreen && !prevAllGreenRef.current) {
      setShowCelebration(true);
      const timer = setTimeout(() => setShowCelebration(false), 1200);
      return () => clearTimeout(timer);
    }
    prevAllGreenRef.current = allGreen;
  }, [allGreen]);

  // ---------------------------------------------------------------------------
  // Collapsed strip
  // ---------------------------------------------------------------------------
  if (isCollapsed) {
    const hasImage = !!(variant?.image?.url || variant?.image_description);
    const dots = intel ? [
      dotColor[intel.hook_strength?.rating]     || 'bg-gray-300',
      dotColor[intel.cta_clarity?.status]       || 'bg-gray-300',
      'bg-blue-400',
      dotColor[intel.length_assessment?.status] || 'bg-gray-300',
      hasImage ? 'bg-purple-400' : 'bg-gray-200',
    ] : Array(5).fill('bg-gray-200');

    return (
      <div className="flex flex-col items-center w-12 bg-white border border-gray-200 rounded-xl shadow-sm py-3 gap-3 flex-shrink-0">
        <button
          onClick={() => setIsCollapsed(false)}
          className="text-gray-400 hover:text-gray-700 text-xl leading-none"
          aria-label="Expand intelligence sidebar"
          title="Expand sidebar"
        >
          «
        </button>
        {dots.map((color, i) => (
          <div key={i} className={`w-3 h-3 rounded-full ${color}`} aria-hidden="true" />
        ))}
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Full panel
  // ---------------------------------------------------------------------------
  return (
    <div className="w-80 flex-shrink-0 bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col max-h-screen sticky top-4">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-semibold text-gray-700">Engagement Intel</span>
          {isLoading && (
            <div className="h-5 w-20 bg-gray-200 rounded-full animate-pulse" />
          )}
          {!isLoading && intel && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
              allGreen
                ? `bg-green-100 text-green-800 ${showCelebration ? 'animate-bounce' : ''}`
                : 'bg-amber-100 text-amber-800'
            }`}>
              {allGreen
                ? '✅ All Green'
                : `⚠️ ${suggestionCount} tip${suggestionCount !== 1 ? 's' : ''}`}
            </span>
          )}
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="text-gray-400 hover:text-gray-700 text-xl leading-none flex-shrink-0 ml-2"
          aria-label="Collapse intelligence sidebar"
          title="Collapse sidebar"
        >
          »
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">

        {/* Empty state — before generation */}
        {!variant && !isLoading && (
          <p className="text-sm text-gray-400 text-center py-10 px-4 leading-relaxed">
            Generate a post to see engagement intelligence.
          </p>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <>
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </>
        )}

        {/* Dimension rows */}
        {!isLoading && intel && (
          <>
            <DimensionRow
              label="Hook"
              icon="🎣"
              badge={intel.hook_strength?.rating || '—'}
              badgeColor={ratingBadgeColor[intel.hook_strength?.rating] || 'bg-gray-100 text-gray-600 border border-gray-200'}
              detail={intel.hook_strength?.reason || '—'}
            />
            <DimensionRow
              label="CTA"
              icon="📣"
              badge={intel.cta_clarity?.status || '—'}
              badgeColor={statusBadgeColor[intel.cta_clarity?.status] || 'bg-gray-100 text-gray-600 border border-gray-200'}
              detail={intel.cta_clarity?.suggestion || '—'}
            />
            <DimensionRow
              label="Best Time"
              icon="🕐"
              badge={intel.optimal_posting_time?.time || '—'}
              badgeColor="bg-blue-100 text-blue-800 border border-blue-200"
              detail={intel.optimal_posting_time?.reason || '—'}
            />
            <DimensionRow
              label="Length"
              icon="📏"
              badge={`${intel.length_assessment?.char_count ?? 0} chars · ${intel.length_assessment?.status || '—'}`}
              badgeColor={statusBadgeColor[intel.length_assessment?.status] || 'bg-gray-100 text-gray-600 border border-gray-200'}
              detail={lengthDetail(intel)}
            />
            <ImageVisualSection
              variant={variant}
              onRegenerateImage={onRegenerateImage}
              isRegenerating={isRegenerating}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default IntelligenceSidebar;
