import React from 'react';
import { Play, Pause } from 'lucide-react';
import type { AudioSegment } from '../../types/lesson';

interface CurrentSegmentProps {
  segment: AudioSegment;
  isPlaying: boolean;
  currentSegmentIndex: number;
  totalSegments: number;
  hasAudioReady: boolean;
  showLearningQuestion: boolean;
  context?: 'home' | 'driving' | 'workout';
  onPlayPause: () => void;
  onSkipToQuestion: () => void;
}

const voiceMapping = { 'Host A': 'Alloy', 'Host B': 'Echo', 'narrator': 'Nova' };
const getDisplayName = (speaker: string) => 
  voiceMapping[speaker as keyof typeof voiceMapping] || speaker;

export const CurrentSegment: React.FC<CurrentSegmentProps> = ({
  segment,
  isPlaying,
  currentSegmentIndex,
  totalSegments,
  hasAudioReady,
  showLearningQuestion,
  context,
  onPlayPause,
  onSkipToQuestion
}) => {
  if (!segment || !hasAudioReady || showLearningQuestion) {
    return null;
  }

  return (
    <div className={`current-playing-segment ${!isPlaying ? 'paused' : ''}`}>
      <div className="audio-controls-inline">
        <div className="play-control-group">
          <button 
            className={`play-pause-btn-compact ${isPlaying ? 'playing' : 'paused'}`} 
            onClick={onPlayPause} 
            disabled={!segment?.stream_url}
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
          {!isPlaying && (
            <span className="play-helper-text">Click to play / start listening</span>
          )}
        </div>
        <span className="current-segment-info">
          {getDisplayName(segment.speaker)} {currentSegmentIndex + 1} of {totalSegments}
        </span>
      </div>

      <div className="speaker-name">{getDisplayName(segment.speaker)}</div>
      <div className="segment-text">{segment.text}</div>

      {context !== 'driving' && (
        <div className="skip-controls">
          <button 
            className="skip-to-question-btn" 
            onClick={onSkipToQuestion} 
            title="Skip audio and go to learning question"
          >
            Skip to Question →
          </button>
        </div>
      )}
    </div>
  );
};
