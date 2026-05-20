import React, { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import AccessDenied from './components/auth/AccessDenied';
import LoginPage from './components/auth/LoginPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import PostGenerator from './components/PostGenerator';
import PostResult from './components/PostResult';
import { AuthProvider, useAuth } from './context/AuthProvider';

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
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-8 h-16 flex items-center justify-between gap-8">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity">
              <div className="flex items-center justify-center">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="#0A66C2" />
                  <path d="M8 12L16 8L24 12V20L16 24L8 20V12Z" fill="white" fillOpacity="0.9" />
                  <path d="M16 8V16M16 16L24 12M16 16L8 12" stroke="#0A66C2" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="font-display text-lg font-bold text-gray-900 tracking-tight leading-none">PostCraft AI</span>
                <span className="text-xs text-gray-500 font-medium tracking-wide">LinkedIn Content Studio</span>
              </div>
            </div>
          </div>

          <nav className="flex items-center gap-1 flex-1 justify-center">
            <button className="py-2 px-4 bg-transparent border-none text-gray-600 text-sm font-semibold rounded-md transition-all hover:text-gray-900 hover:bg-gray-100 relative">Generate</button>
            <button className="py-2 px-4 bg-transparent border-none text-gray-600 text-sm font-semibold rounded-md transition-all hover:text-gray-900 hover:bg-gray-100 relative">History</button>
            <button className="py-2 px-4 bg-transparent border-none text-gray-600 text-sm font-semibold rounded-md transition-all hover:text-gray-900 hover:bg-gray-100 relative">Templates</button>
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={handleNewPost}
              className="flex items-center gap-2 py-2 px-4 bg-gray-100 text-gray-700 border border-gray-200 rounded-md text-sm font-semibold hover:bg-gray-200 hover:border-gray-300 transition-all"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
                <circle cx="8" cy="8" r="6" strokeWidth="1.5" />
                <path d="M8 5v6M5 8h6" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span>New Post</span>
            </button>

            {user && (
              <button
                onClick={logout}
                className="flex items-center gap-2 py-2 px-4 bg-gray-100 text-gray-700 border border-gray-200 rounded-md text-sm font-semibold hover:bg-gray-200 hover:border-gray-300 transition-all"
                title={`Signed in as ${user.email} — click to log out`}
              >
                {user.picture && (
                  <img src={user.picture} alt={user.name || 'User avatar'} className="w-5 h-5 rounded-full" />
                )}
                <span>Logout</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 px-8 py-8 flex justify-center items-start main-dot-grid">
        <div className="w-full max-w-[1400px]">
          <PostGenerator
            onGenerate={handlePostGenerated}
            onGenerating={handleGenerating}
            isLoading={isLoading}
          />

          {isLoading && (
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-8 text-center mt-6">
              <div className="w-12 h-12 border-[3px] border-gray-200 border-t-primary rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-700 font-medium">Generating your optimized post...</p>
            </div>
          )}

          {generatedPost && !isLoading && (
            <PostResult result={generatedPost} onReset={handleReset} />
          )}
        </div>
      </main>

      <footer className="py-4 text-center text-gray-500 text-sm bg-white border-t border-gray-200">
        <p>Powered by Claude AI • Built with React &amp; FastAPI</p>
      </footer>
    </div>
  );
}

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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;