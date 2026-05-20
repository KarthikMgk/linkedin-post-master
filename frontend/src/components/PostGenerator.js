import React, { useState } from 'react';
import { useAuth } from '../context/AuthProvider';
import apiService from '../services/apiService';
import QuotaDisplay from './auth/QuotaDisplay';

function PostGenerator({ onGenerate, onGenerating, isLoading }) {
  const [textInput, setTextInput] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [imageFiles, setImageFiles] = useState([]);
  const [urlInput, setUrlInput] = useState('');
  const [error, setError] = useState('');
  const { quotaRemaining } = useAuth();
  const isQuotaExhausted = quotaRemaining === 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!textInput && !pdfFile && imageFiles.length === 0 && !urlInput) {
      setError('Please provide at least one input (text, file, or URL)');
      return;
    }

    onGenerating();

    try {
      const result = await apiService.generatePost({
        text: textInput,
        pdf: pdfFile,
        images: imageFiles,
        url: urlInput
      });

      onGenerate(result);
    } catch (err) {
      setError(err.message || 'Failed to generate post. Please try again.');
      onGenerate(null);
    }
  };

  const handlePdfChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
    } else {
      setError('Please select a valid PDF file');
    }
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    const validImages = files.filter(file =>
      file.type.startsWith('image/')
    );

    if (validImages.length !== files.length) {
      setError('Some files were not valid images and were skipped');
    }

    setImageFiles(validImages);
  };

  const handleReset = () => {
    setTextInput('');
    setPdfFile(null);
    setImageFiles([]);
    setUrlInput('');
    setError('');
  };

  const inputClass = "w-full p-4 border border-gray-300 rounded-lg text-sm font-sans bg-white text-gray-900 transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60";
  const labelClass = "block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide";
  const inputGroupClass = "mb-6";

  return (
    <div className="w-full">
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8">
        <h2 className="font-display text-xl font-bold text-gray-900 mb-1 tracking-tight">Create Your LinkedIn Post</h2>
        <p className="text-gray-600 mb-8 text-sm leading-relaxed">
          Drop your content below - text, PDFs, images, or URLs.
          Our AI will synthesize everything into an engaging LinkedIn post.
        </p>

        {isQuotaExhausted && (
          <div className="bg-red-50 text-red-800 border border-red-200 rounded-md px-4 py-3 mb-6 text-sm font-medium" role="alert">
            You've reached your daily generation limit. It resets at midnight UTC.
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={inputGroupClass}>
            <label>
              <span className={labelClass}>Text Content</span>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Enter your content, ideas, or paste article text..."
                rows="6"
                disabled={isLoading}
                className={`${inputClass} resize-vertical min-h-[140px] leading-relaxed`}
              />
            </label>
          </div>

          <div className={inputGroupClass}>
            <label>
              <span className={labelClass}>PDF Document</span>
              <input
                type="file"
                accept=".pdf"
                onChange={handlePdfChange}
                disabled={isLoading}
                className="w-full p-4 border-2 border-dashed border-gray-300 bg-gray-50 cursor-pointer text-sm hover:border-primary hover:bg-white file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-dark"
              />
              {pdfFile && <span className="block mt-2 text-primary text-sm font-medium">Selected: {pdfFile.name}</span>}
            </label>
          </div>

          <div className={inputGroupClass}>
            <label>
              <span className={labelClass}>Images (with text)</span>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                disabled={isLoading}
                className="w-full p-4 border-2 border-dashed border-gray-300 bg-gray-50 cursor-pointer text-sm hover:border-primary hover:bg-white file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary-dark"
              />
              {imageFiles.length > 0 && (
                <span className="block mt-2 text-primary text-sm font-medium">
                  Selected: {imageFiles.length} image(s)
                </span>
              )}
            </label>
          </div>

          <div className={inputGroupClass}>
            <label>
              <span className={labelClass}>URL Reference</span>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com/article"
                disabled={isLoading}
                className={inputClass}
              />
            </label>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-md mb-6 border-l-4 border-red-600 text-sm font-medium">
              {error}
            </div>
          )}

          <QuotaDisplay />

          <div className="flex gap-4 mt-8 pt-8 border-t border-gray-200">
            <button
              type="submit"
              className="flex-1 py-3 px-6 bg-primary text-white border-none rounded-lg text-sm font-semibold shadow-sm transition-all hover:bg-primary-dark hover:shadow-md hover:-translate-y-px active:translate-y-0 active:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading || isQuotaExhausted}
              title={isQuotaExhausted ? 'Daily limit reached. Try again tomorrow.' : ''}
            >
              {isLoading ? 'Generating...' : 'Generate Post'}
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="py-3 px-6 bg-white text-gray-700 border border-gray-300 rounded-lg text-sm font-semibold flex-shrink-0 transition-all hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PostGenerator;