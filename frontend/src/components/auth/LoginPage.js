import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthProvider';

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSuccess = async (credentialResponse) => {
    setError(null);
    setLoading(true);
    try {
      await login(credentialResponse.credential);
      navigate('/', { replace: true });
    } catch (err) {
      // err.message is the actual backend error (e.g. "Access denied", "Token verification failed: ...")
      setError(err.message || 'Sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleError = () => {
    setError('Google sign-in was cancelled or failed. Please try again.');
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#0A66C2" />
            <path d="M8 12L16 8L24 12V20L16 24L8 20V12Z" fill="white" fillOpacity="0.9" />
            <path
              d="M16 8V16M16 16L24 12M16 16L8 12"
              stroke="#0A66C2"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <h1 className="login-title">PostCraft AI</h1>
        <p className="login-subtitle">LinkedIn Content Studio</p>

        <div className="login-divider" />

        {loading ? (
          <p className="login-loading">Signing you in…</p>
        ) : (
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap={false}
          />
        )}

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default LoginPage;
