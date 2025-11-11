import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <div className="loading-text">
        <h3>🧠 AI is analyzing...</h3>
        <p>Mapping arguments and logical structures</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;