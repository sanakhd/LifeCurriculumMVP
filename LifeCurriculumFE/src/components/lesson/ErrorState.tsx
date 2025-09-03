import React from 'react';

interface ErrorStateProps {
  error: string;
  onBackClick: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onBackClick }) => {
  return (
    <div className="lesson-page">
      <div className="lesson-error">
        <h2>Error Loading Lesson</h2>
        <p>{error}</p>
        <button onClick={onBackClick} className="back-btn">
          Back to Programs
        </button>
      </div>
    </div>
  );
};
