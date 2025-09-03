import React from 'react';
import { FileText } from 'lucide-react';
import type { AudioSegment } from '../../types/lesson';

interface TranscriptContainerProps {
  audioSegments: AudioSegment[];
  currentSegmentIndex: number;
  onSegmentClick: (index: number) => void;
}

const voiceMapping = { 'Host A': 'Alloy', 'Host B': 'Echo', 'narrator': 'Nova' };
const getDisplayName = (speaker: string) => 
  voiceMapping[speaker as keyof typeof voiceMapping] || speaker;

export const TranscriptContainer: React.FC<TranscriptContainerProps> = ({
  audioSegments,
  currentSegmentIndex,
  onSegmentClick
}) => {
  return (
    <div className="transcript-container">
      <h3>Lesson Content (No Audio Available)</h3>
      <div className="transcript-segments">
        {audioSegments.map((segment, index) => (
          <div
            key={`${segment.audio_id}-${index}`}
            className={`transcript-segment ${index === currentSegmentIndex ? 'active' : ''} text-only`}
            onClick={() => onSegmentClick(index)}
          >
            <div className="segment-indicator">
              <span className="speaker-label">{getDisplayName(segment.speaker)}</span>
              <span className="text-only">
                <FileText size={14} />
              </span>
            </div>
            <p>{segment.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
