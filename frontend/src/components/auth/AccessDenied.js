import React from 'react';
import { useNavigate } from 'react-router-dom';

function AccessDenied() {
  const navigate = useNavigate();

  return (
    <div className="login-page">
      <div className="login-card">
        <h2 className="login-title">Access Denied</h2>
        <p className="login-subtitle">
          This application is invite-only. Your Google account does not have access.
        </p>
        <div className="login-divider" />
        <button
          className="header-btn secondary"
          onClick={() => navigate('/login', { replace: true })}
        >
          Try a different account
        </button>
      </div>
    </div>
  );
}

export default AccessDenied;
