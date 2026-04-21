import React, { useState } from 'react';
import './PostGenerator.css';
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

    // Validate at least one input
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

  return (
    <div className="post-generator">
      <div className="generator-card">
        <h2>Create Your LinkedIn Post</h2>
        <p className="description">
          Drop your content below - text, PDFs, images, or URLs.
          Our AI will synthesize everything into an engaging LinkedIn post.
        </p>

        <form onSubmit={handleSubmit}>
          {/* Text Input */}
          <div className="input-group">
            <label>
              <span className="label-text">Text Content</span>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Enter your content, ideas, or paste article text..."
                rows="6"
                disabled={isLoading}
              />
            </label>
          </div>

          {/* PDF Upload */}
          <div className="input-group">
            <label>
              <span className="label-text">PDF Document</span>
              <input
                type="file"
                accept=".pdf"
                onChange={handlePdfChange}
                disabled={isLoading}
              />
              {pdfFile && <span className="file-name">Selected: {pdfFile.name}</span>}
            </label>
          </div>

          {/* Image Upload */}
          <div className="input-group">
            <label>
              <span className="label-text">Images (with text)</span>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                disabled={isLoading}
              />
              {imageFiles.length > 0 && (
                <span className="file-name">
                  Selected: {imageFiles.length} image(s)
                </span>
              )}
            </label>
          </div>

          {/* URL Input */}
          <div className="input-group">
            <label>
              <span className="label-text">URL Reference</span>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com/article"
                disabled={isLoading}
              />
            </label>
          </div>

          {error && <div className="error-message">{error}</div>}

          <QuotaDisplay />

          <div className="button-group">
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || isQuotaExhausted}
              title={isQuotaExhausted ? 'Daily limit reached. Try again tomorrow.' : ''}
            >
              {isLoading ? 'Generating...' : 'Generate Post'}
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="btn-secondary"
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
