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
      setError(err.message || 'Sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleError = () => {
    setError('Google sign-in was cancelled or failed. Please try again.');
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{
        background: 'radial-gradient(ellipse at 30% 20%, rgba(10,102,194,0.08) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(10,102,194,0.06) 0%, transparent 50%), #f3f2ef',
      }}
    >
      <div className="bg-white rounded-xl shadow-xl p-12 flex flex-col items-center gap-4 min-w-[340px] max-w-[420px] w-full">
        <div className="mb-1" style={{ filter: 'drop-shadow(0 4px 8px rgba(10,102,194,0.15))' }}>
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

        <h1 className="font-display text-2xl font-bold text-gray-900 m-0">PostCraft AI</h1>
        <p className="text-sm text-gray-500 text-center m-0">LinkedIn Content Studio</p>
        <p className="text-xs text-primary font-medium text-center m-0">AI-powered content that actually gets engagement</p>

        <div className="w-full h-px bg-gray-200 my-1" />

        {loading ? (
          <p className="text-sm text-gray-500">Signing you in…</p>
        ) : (
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap={false}
          />
        )}

        {error && (
          <div className="text-red-600 bg-red-50 border border-red-200 rounded-md text-sm px-3 py-2 text-center w-full" role="alert">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default LoginPage;