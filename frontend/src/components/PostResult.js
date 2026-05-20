import React, { useState } from 'react';
import apiService from '../services/apiService';
import IntelligenceSidebar from './IntelligenceSidebar';
import VariantCard from './VariantCard';

const LINKEDIN_CHAR_LIMIT = 3000;

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

function PostResult({ result, onReset }) {
  const initialVariants = result.variants && result.variants.length > 0
    ? result.variants
    : [result];

  const [variants, setVariants] = useState(initialVariants);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [hasUserSelected, setHasUserSelected] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [isRegeneratingImage, setIsRegeneratingImage] = useState(false);
  const [refinementFeedback, setRefinementFeedback] = useState('');
  const [error, setError] = useState('');
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('Post copied! Ready to paste in LinkedIn');
  const [isUpdating, setIsUpdating] = useState(false);

  const currentPost = variants[selectedIndex] || {};
  const post = typeof currentPost.post === 'string' ? currentPost.post : '';
  const hashtags = Array.isArray(currentPost.hashtags) ? currentPost.hashtags : [];
  const charCount = post.length;
  const isOverLimit = charCount > LINKEDIN_CHAR_LIMIT;

  const handleSelectVariant = (index) => {
    setSelectedIndex(index);
    setHasUserSelected(true);
    setError('');
    setRefinementFeedback('');
  };

  const updateVariantImage = (variantId, newImage) => {
    setVariants((prev) =>
      prev.map((v) => (v.id === variantId ? { ...v, image: newImage } : v))
    );
  };

  const handleRegenerateImage = async (customDirection = '') => {
    if (isRegeneratingImage) return;
    setIsRegeneratingImage(true);
    try {
      const data = await apiService.regenerateImage({
        imageDescription: currentPost.image_description || '',
        altText: currentPost.image_alt_text || '',
        customDirection,
      });
      updateVariantImage(currentPost.id, data.image);
    } catch (err) {
      console.error('Image regeneration failed:', err.message);
    } finally {
      setIsRegeneratingImage(false);
    }
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

      setIsUpdating(true);
      setVariants((prev) => {
        const updated = [...prev];
        updated[selectedIndex] = {
          ...updated[selectedIndex],
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
          intelligence: refined.intelligence ?? updated[selectedIndex].intelligence,
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

  return (
    <div className="mt-8 relative animate-slide-up">
      {showCopyToast && (
        <div className="fixed bottom-8 right-8 bg-gray-900 text-white flex items-center gap-3 px-5 py-3 rounded-lg shadow-xl z-50 animate-slideInUp">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="9" fill="#059669" stroke="white" strokeWidth="2"/>
            <path d="M6 10l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      <div className="flex gap-4 items-start">
        <div className="flex-1 min-w-0">
          <div className={`bg-white rounded-xl shadow-md border border-gray-200 p-8 relative transition-opacity ${isRefining ? 'pointer-events-none' : ''}`}>
            <div className="flex justify-between items-center mb-8 pb-6 border-b border-gray-200 flex-wrap gap-3">
              <h2 className="font-display text-xl font-bold text-gray-900 tracking-tight">Generated Post</h2>
              <button onClick={onReset} className="py-3 px-5 bg-white text-gray-700 border border-gray-300 rounded-md text-sm font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all">
                Create New Post
              </button>
            </div>

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

            <div className={`grid grid-cols-2 gap-6 mb-8 p-5 bg-gray-50 rounded-xl border border-gray-200 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Engagement Score</span>
                <span className="text-3xl font-bold" style={{ color: getScoreColor(currentPost.engagement_score) }}>
                  {currentPost.engagement_score}/10
                </span>
                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${currentPost.engagement_score * 10}%`, backgroundColor: getScoreColor(currentPost.engagement_score), transition: 'width 0.7s cubic-bezier(0.4, 0, 0.2, 1)' }} />
                </div>
              </div>
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Hook Strength</span>
                <span className="text-3xl font-bold" style={{ color: getHookColor(currentPost.hook_strength) }}>
                  {currentPost.hook_strength}
                </span>
                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${currentPost.hook_strength === 'Exceptional' ? 100 : currentPost.hook_strength === 'Strong' ? 75 : currentPost.hook_strength === 'Moderate' ? 50 : 25}%`, backgroundColor: getHookColor(currentPost.hook_strength), transition: 'width 0.7s cubic-bezier(0.4, 0, 0.2, 1)' }} />
                </div>
              </div>
            </div>

            <div className={`mb-8 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
              <span className="block text-xs font-semibold text-gray-700 mb-2">Post Text:</span>
              <div className="bg-gray-50 p-5 rounded-xl border border-gray-200 leading-relaxed text-sm text-gray-900">
                {post.split('\n').map((line, index) => (
                  <React.Fragment key={index}>
                    {line}
                    {index < post.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
              <div className="text-xs mt-2" style={{ color: isOverLimit ? '#f44336' : '#666' }}>
                {charCount.toLocaleString()} / {LINKEDIN_CHAR_LIMIT.toLocaleString()} characters
                {isOverLimit ? ' ⚠ Over LinkedIn limit' : ' ✓'}
              </div>
            </div>

            <div className={`mb-8 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
              <span className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                Hashtags: <span className="normal-case font-normal text-gray-500">({hashtags.length} — recommended 3–5)</span>
              </span>
              <div className="flex flex-wrap gap-2">
                {hashtags.map((tag, index) => (
                  <span key={index} className="bg-primary text-white py-1 px-4 rounded-md text-xs font-semibold">#{tag}</span>
                ))}
              </div>
            </div>

            {currentPost.suggestions && currentPost.suggestions.length > 0 && (
              <div className={`p-4 bg-amber-50 border border-amber-200 rounded-xl mb-6 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
                <span className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">Optimization Suggestions</span>
                <ul className="list-none p-0">
                  {currentPost.suggestions.map((suggestion, index) => (
                    <li key={index} className="text-sm text-gray-800 relative pl-6 py-1 leading-relaxed">💡{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}

            {currentPost.cta && (
              <div className={`mb-6 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
                <span className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Call to Action</span>
                <p className="text-sm text-gray-700">{currentPost.cta}</p>
              </div>
            )}

            {currentPost.image_alt_text && (
              <div className={`mb-6 transition-opacity ${isUpdating ? 'opacity-0 -translate-y-2' : ''}`}>
                <span className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Suggested Image Concept</span>
                <p className="text-sm text-gray-700 break-words">{currentPost.image_alt_text}</p>
              </div>
            )}

            <div className="pt-8 border-t border-gray-200 relative">
              {isRefining && (
                <div className="absolute inset-0 bg-white/95 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-3 z-10">
                  <div className="w-10 h-10 border-3 border-gray-200 border-t-primary rounded-full animate-spin" />
                  <p className="text-gray-700 font-medium text-sm">Refining your post...</p>
                </div>
              )}

              <span className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Refine Post</span>
              <p className="text-gray-500 text-sm mb-4 leading-relaxed">
                Provide feedback to improve the post (e.g., "Make it more concise", "Add a call-to-action")
              </p>

              <div className="flex gap-3 items-start">
                <textarea
                  value={refinementFeedback}
                  onChange={(e) => setRefinementFeedback(e.target.value)}
                  placeholder="Make it more engaging..."
                  rows="3"
                  disabled={isRefining}
                  aria-label="Refinement feedback"
                  className="flex-1 p-3 border border-gray-300 rounded-lg text-sm font-sans focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 resize-y"
                />
                <button
                  onClick={handleRefine}
                  disabled={isRefining || !refinementFeedback.trim()}
                  className="py-3 px-5 bg-primary text-white border-none rounded-lg text-sm font-semibold shadow-sm transition-all flex items-center gap-2 hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  {isRefining ? (
                    <>
                      <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Refining...
                    </>
                  ) : 'Refine Post'}
                </button>
              </div>

              {error && (
                <div className="bg-red-50 text-red-600 px-4 py-3 rounded-md mt-4 border-l-4 border-red-600 text-sm font-medium" role="alert">
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>

        <IntelligenceSidebar
          variant={currentPost}
          isLoading={isRefining}
          onRegenerateImage={handleRegenerateImage}
          isRegenerating={isRegeneratingImage}
        />
      </div>
    </div>
  );
}

export default PostResult;