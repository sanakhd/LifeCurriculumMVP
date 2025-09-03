import React from 'react';

interface AudioProgressBarProps {
  audioLoadingProgress: number;
}

export const AudioProgressBar: React.FC<AudioProgressBarProps> = ({ audioLoadingProgress }) => {
  if (audioLoadingProgress >= 100) return null;

  return (
    <div className="audio-progress">
      <p>Loading lesson content... {Math.round(audioLoadingProgress)}%</p>
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${audioLoadingProgress}%` }}
        />
      </div>
    </div>
  );
};
