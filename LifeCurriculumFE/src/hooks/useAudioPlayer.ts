import { useState, useRef, useCallback } from 'react';
import type { AudioSegment } from '../types/lesson';

interface UseAudioPlayerProps {
  audioSegments: AudioSegment[];
  onAudioComplete: () => void;
  onLessonStart: () => void;
}

export const useAudioPlayer = ({ audioSegments, onAudioComplete, onLessonStart }: UseAudioPlayerProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handlePlayPause = useCallback(() => {
    if (!audioRef.current || audioSegments.length === 0) return;
    
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      onLessonStart();
      const segment = audioSegments[currentSegmentIndex];
      if (segment?.stream_url) {
        audioRef.current.src = segment.stream_url;
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch(() => setIsPlaying(false));
      }
    }
  }, [isPlaying, currentSegmentIndex, audioSegments, onLessonStart]);

  const handleAudioEnded = useCallback(() => {
    setIsPlaying(false);
    if (currentSegmentIndex === audioSegments.length - 1) {
      onAudioComplete();
      return;
    }
    
    const nextIndex = currentSegmentIndex + 1;
    setCurrentSegmentIndex(nextIndex);
    const nextSegment = audioSegments[nextIndex];
    
    if (nextSegment?.stream_url && audioRef.current) {
      audioRef.current.src = nextSegment.stream_url;
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(() => {});
    }
  }, [currentSegmentIndex, audioSegments, onAudioComplete]);

  const handleSegmentClick = useCallback((index: number) => {
    setCurrentSegmentIndex(index);
    const segment = audioSegments[index];
    
    if (segment?.stream_url && audioRef.current && isPlaying) {
      audioRef.current.src = segment.stream_url;
      audioRef.current.play().catch(() => {});
    }
  }, [audioSegments, isPlaying]);

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  return {
    audioRef,
    isPlaying,
    currentSegmentIndex,
    handlePlayPause,
    handleAudioEnded,
    handleSegmentClick,
    stopPlayback,
    currentSegment: audioSegments[currentSegmentIndex] || null,
    hasAudioReady: audioSegments.some(s => s.stream_url)
  };
};
