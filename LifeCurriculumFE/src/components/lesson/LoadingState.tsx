import React from 'react';

interface LoadingStateProps {
  audioLoadingProgress: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ audioLoadingProgress }) => {
  return (
    <div className="lesson-page">
      <div className="lesson-loading">
        <div className="loading-spinner"></div>
        <p>Loading lesson...</p>
      </div>
      {audioLoadingProgress < 100 && audioLoadingProgress > 0 && (
        <div className="audio-progress">
          <p>Loading lesson content... {Math.round(audioLoadingProgress)}%</p>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${audioLoadingProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
