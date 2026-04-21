import React from 'react';
import { useAuth } from '../../context/AuthProvider';

function QuotaDisplay() {
  const { quotaRemaining, quotaLimit } = useAuth();

  // Render nothing until the first API call populates quota from headers
  if (quotaRemaining === null) return null;

  const isExhausted = quotaRemaining === 0;
  const isWarning = quotaRemaining > 0 && quotaRemaining <= 3;

  const className = isExhausted
    ? 'quota-display quota-exhausted'
    : isWarning
    ? 'quota-display quota-warning'
    : 'quota-display';

  return (
    <div className={className}>
      {isExhausted ? (
        <span>Quota exhausted — resets at midnight UTC</span>
      ) : (
        <span>
          <strong>{quotaRemaining} of {quotaLimit}</strong> generations remaining today
        </span>
      )}
    </div>
  );
}

export default QuotaDisplay;
