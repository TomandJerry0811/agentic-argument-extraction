import React from 'react';
import './ErrorDisplay.css';

interface ErrorDisplayProps {
  error: string;
  onRetry: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry }) => {
  return (
    <div className="error-container">
      <div className="error-icon">❌</div>
      <h3>Analysis Failed</h3>
      <p className="error-message">{error}</p>
      <button className="retry-button" onClick={onRetry}>
        🔄 Try Again
      </button>
    </div>
  );
};

export default ErrorDisplay;