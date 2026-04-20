import React, { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import './App.css';
import AccessDenied from './components/auth/AccessDenied';
import LoginPage from './components/auth/LoginPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import PostGenerator from './components/PostGenerator';
import PostResult from './components/PostResult';
import { AuthProvider, useAuth } from './context/AuthProvider';

// ---------------------------------------------------------------------------
// Main app shell — only rendered when authenticated
// ---------------------------------------------------------------------------

function MainApp() {
  const [generatedPost, setGeneratedPost] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user, logout } = useAuth();

  const handlePostGenerated = (result) => {
    setGeneratedPost(result);
    setIsLoading(false);
  };

  const handleGenerating = () => {
    setIsLoading(true);
    setGeneratedPost(null);
  };

  const handleReset = () => {
    setGeneratedPost(null);
    setIsLoading(false);
  };

  const handleNewPost = () => {
    handleReset();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <div className="logo-icon">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="#0A66C2" />
                  <path
                    d="M8 12L16 8L24 12V20L16 24L8 20V12Z"
                    fill="white"
                    fillOpacity="0.9"
                  />
                  <path
                    d="M16 8V16M16 16L24 12M16 16L8 12"
                    stroke="#0A66C2"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <div className="logo-text">
                <span className="logo-title">PostCraft AI</span>
                <span className="logo-subtitle">LinkedIn Content Studio</span>
              </div>
            </div>
          </div>

          <nav className="header-nav">
            <button className="nav-item active">Generate</button>
            <button className="nav-item">History</button>
            <button className="nav-item">Templates</button>
          </nav>

          <div className="header-right">
            <button className="header-btn secondary" onClick={handleNewPost}>
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
              >
                <circle cx="8" cy="8" r="6" strokeWidth="1.5" />
                <path d="M8 5v6M5 8h6" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span>New Post</span>
            </button>

            {user && (
              <button
                className="header-btn secondary"
                onClick={logout}
                title={`Signed in as ${user.email} — click to log out`}
              >
                {user.picture && (
                  <img
                    src={user.picture}
                    alt={user.name || 'User avatar'}
                    style={{ width: 20, height: 20, borderRadius: '50%' }}
                  />
                )}
                <span>Logout</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="App-main">
        <div className="container">
          <PostGenerator
            onGenerate={handlePostGenerated}
            onGenerating={handleGenerating}
            isLoading={isLoading}
          />

          {isLoading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>Generating your optimized post...</p>
            </div>
          )}

          {generatedPost && !isLoading && (
            <PostResult result={generatedPost} onReset={handleReset} />
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>Powered by Claude AI • Built with React &amp; FastAPI</p>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root — providers + routing
// ---------------------------------------------------------------------------

function App() {
  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/access-denied" element={<AccessDenied />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainApp />
                </ProtectedRoute>
              }
            />
            {/* Catch-all: redirect unknown paths to home (which redirects to login if unauthed) */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
