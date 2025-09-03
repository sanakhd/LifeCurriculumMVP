import { useState, useCallback } from 'react';
import { lifeCurriculumApi } from '../services/api';
import type { LessonData, AudioSegment } from '../types/lesson';

interface UseLessonDataProps {
  programId: string;
  day: number;
}

export const useLessonData = ({ programId, day }: UseLessonDataProps) => {
  const [lessonData, setLessonData] = useState<LessonData | null>(null);
  const [programData, setProgramData] = useState<any>(null);
  const [audioSegments, setAudioSegments] = useState<AudioSegment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [audioLoadingProgress, setAudioLoadingProgress] = useState(0);
  const [lessonStartTime, setLessonStartTime] = useState<Date | null>(null);
  const [isLessonCompleted, setIsLessonCompleted] = useState(false);

  const createTranscriptSegments = useCallback((data: LessonData) => {
    const transcriptText = data.transcript || data.content || '';
    const paragraphs = transcriptText.split('\n\n').filter(p => p.trim().length > 0);
    
    if (!paragraphs.length) {
      const sentences = transcriptText.split(/[.!?]+/).filter(s => s.trim().length > 0);
      const segments: AudioSegment[] = [];
      
      for (let i = 0; i < sentences.length; i += 2) {
        const text = sentences.slice(i, i + 2).join('. ').trim() + '.';
        if (text.length > 1) {
          segments.push({
            audio_id: `text-${i}`,
            speaker: 'Narrator',
            voice: 'alloy',
            duration_seconds: 0,
            chunk_index: i,
            stream_url: '',
            text
          });
        }
      }
      setAudioSegments(segments);
    } else {
      const segments: AudioSegment[] = paragraphs.map((paragraph, index) => ({
        audio_id: `text-${index}`,
        speaker: 'Narrator',
        voice: 'alloy',
        duration_seconds: 0,
        chunk_index: index,
        stream_url: '',
        text: paragraph
      }));
      setAudioSegments(segments);
    }
  }, []);

  const loadAudioPlaylist = useCallback(async (lessonUuid: string, data: LessonData) => {
    try {
      setAudioLoadingProgress(60);
      const playlist = await lifeCurriculumApi.getLessonAudioPlaylist(lessonUuid);

      if (playlist?.playlist?.length) {
        const segments: AudioSegment[] = playlist.playlist.map((item: any, index: number) => {
          const chunkText = data.conversationChunks[index]?.text
            || data.conversationChunks[index]?.content
            || `${item.speaker}: [Audio ${index + 1}]`;
          
          let streamUrl = item.stream_url;
          if (!streamUrl || !streamUrl.startsWith('http')) {
            streamUrl = lifeCurriculumApi.getAudioStreamUrl(lessonUuid, item.audio_id);
          }
          
          return { ...item, stream_url: streamUrl, text: chunkText };
        });

        setAudioSegments(segments);
        setAudioLoadingProgress(100);
      } else {
        await generateLessonAudio(lessonUuid, data);
      }
    } catch {
      createTranscriptSegments(data);
      setAudioLoadingProgress(100);
    }
  }, [createTranscriptSegments]);

  const generateLessonAudio = useCallback(async (lessonUuid: string, data: LessonData) => {
    try {
      setAudioLoadingProgress(70);
      const audioResponse = await lifeCurriculumApi.generateLessonAudio({
        lesson_uuid: lessonUuid,
        voice_mapping: { 'Host A': 'alloy', 'Host B': 'echo', 'narrator': 'nova' }
      });

      if (audioResponse.success) {
        setAudioLoadingProgress(90);
        await loadAudioPlaylist(lessonUuid, data);
      } else {
        createTranscriptSegments(data);
        setAudioLoadingProgress(100);
      }
    } catch {
      createTranscriptSegments(data);
      setAudioLoadingProgress(100);
    }
  }, [loadAudioPlaylist, createTranscriptSegments]);

  const fetchLessonData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setAudioLoadingProgress(10);

      // Fetch both program and lesson data
      const [program, lesson] = await Promise.all([
        lifeCurriculumApi.getProgramById(programId),
        lifeCurriculumApi.getSingleLesson(programId, day)
      ]);

      if (!lesson) throw new Error('Lesson not found');
      if (!program) throw new Error('Program not found');

      setProgramData(program);
      setAudioLoadingProgress(30);

      const mapped: LessonData = {
        id: lesson.id || lesson.lesson_uuid,
        title: lesson.title || `Day ${day}`,
        content: lesson.content || '',
        transcript: lesson.transcript || lesson.content || '',
        conversationChunks: lesson.conversation_chunks || [],
        primary_interaction: lesson.primary_interaction,
        learning_objectives: lesson.learning_objectives || lesson.objectives || [],
        description: lesson.description || lesson.summary || '',
        context: program.context || 'home' // Get context from program data
      };
      
      setLessonData(mapped);
      setAudioLoadingProgress(50);

      await loadAudioPlaylist(lesson.lesson_uuid || lesson.id, mapped);
    } catch (err) {
      setError('Failed to load lesson. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [programId, day, loadAudioPlaylist]);

  const startLessonTracking = useCallback(async () => {
    if (!lessonStartTime && lessonData?.id) {
      setLessonStartTime(new Date());
      try {
        await lifeCurriculumApi.startLesson(lessonData.id);
      } catch {
        // Silently handle error
      }
    }
  }, [lessonStartTime, lessonData?.id]);

  const completeLesson = useCallback(async () => {
    if (isLessonCompleted || !lessonData?.id) return;
    
    if (!lessonStartTime) await startLessonTracking();

    const start = lessonStartTime || new Date(new Date().getTime() - 300 * 1000);
    const timeSpentSeconds = Math.floor((new Date().getTime() - start.getTime()) / 1000);

    try {
      setIsLessonCompleted(true);
      const completionRequest = {
        time_spent_seconds: timeSpentSeconds,
        completion_method: 'full',
        user_rating: undefined
      };
      
      const response = await lifeCurriculumApi.completeLesson(lessonData.id, completionRequest);
      if (!response.success) {
        throw new Error('Failed to complete lesson');
      }
    } catch (error) {
      setIsLessonCompleted(false);
      throw error; // Re-throw so the calling function can handle it
    }
  }, [isLessonCompleted, lessonData?.id, lessonStartTime, startLessonTracking]);

  return {
    lessonData,
    programData,
    audioSegments,
    isLoading,
    error,
    audioLoadingProgress,
    lessonStartTime,
    isLessonCompleted,
    fetchLessonData,
    startLessonTracking,
    completeLesson
  };
};
