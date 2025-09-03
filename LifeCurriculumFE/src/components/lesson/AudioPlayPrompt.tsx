import React from 'react';
import { Play } from 'lucide-react';

interface AudioPlayPromptProps {
  onPlay: () => void;
  hasAudioReady: boolean;
}

export const AudioPlayPrompt: React.FC<AudioPlayPromptProps> = ({ onPlay, hasAudioReady }) => {
  if (!hasAudioReady) return null;

  return (
    <div className="audio-ready-prompt">
      <div className="audio-controls-center">
        <button className="play-pause-btn" onClick={onPlay}>
          <Play size={24} />
        </button>
        <span className="play-helper-text">Click to start the lesson audio</span>
      </div>
    </div>
  );
};
