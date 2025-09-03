import { useState, useEffect } from 'react';
import { lifeCurriculumApi } from '../services/api';

interface LessonProgress {
  programId: string;
  completedLessons: number[]; // Array of completed lesson day numbers
  currentLesson: number; // Next available lesson
}

interface LessonProgressState {
  [programId: string]: LessonProgress;
}

interface LessonWithStatus {
  day_number: number;
  status?: string;
  completed_at?: string;
  id?: string;
  lesson_uuid?: string;
}

export function useLessonProgress() {
  const [progressState, setProgressState] = useState<LessonProgressState>({});
  const [loadingPrograms, setLoadingPrograms] = useState<Set<string>>(new Set());

  const fetchProgramProgress = async (programId: string): Promise<void> => {
    if (loadingPrograms.has(programId)) {
      console.log(`[useLessonProgress] Already loading progress for program ${programId}`);
      return; // Already loading this program
    }

    console.log(`[useLessonProgress] Starting to fetch progress for program ${programId}`);

    try {
      setLoadingPrograms(prev => new Set([...prev, programId]));
      
      // Get the program details first to get all lessons
      console.log(`[useLessonProgress] Fetching program details for ${programId}`);
      const program = await lifeCurriculumApi.getProgramById(programId);
      
      if (!program) {
        console.warn(`[useLessonProgress] Program ${programId} not found`);
        return;
      }

      console.log(`[useLessonProgress] Program found: ${program.title}, checking lessons...`);
      const completedLessons: number[] = [];
      
      // Check each lesson (assuming 5-day program)
      for (let day = 1; day <= 5; day++) {
        try {
          console.log(`[useLessonProgress] Checking lesson ${day} for program ${programId}`);
          const lesson = await lifeCurriculumApi.getSingleLesson(programId, day);
          console.log(`[useLessonProgress] Lesson ${day} status:`, lesson?.status || 'not found');
          
          if (lesson && lesson.status === 'completed') {
            completedLessons.push(day);
            console.log(`[useLessonProgress] Added day ${day} to completed lessons`);
          }
        } catch (err) {
          // Lesson might not exist yet, that's ok
          console.debug(`[useLessonProgress] Lesson ${day} for program ${programId} not found or error:`, err);
        }
      }

      // Sort completed lessons
      completedLessons.sort((a, b) => a - b);
      console.log(`[useLessonProgress] Completed lessons for ${programId}:`, completedLessons);

      // Determine next available lesson
      const currentLesson = completedLessons.length > 0 
        ? Math.min(Math.max(...completedLessons) + 1, 5)
        : 1;

      console.log(`[useLessonProgress] Next available lesson for ${programId}: ${currentLesson}`);

      setProgressState(prev => ({
        ...prev,
        [programId]: {
          programId,
          completedLessons,
          currentLesson
        }
      }));

      console.log(`[useLessonProgress] Progress state updated for ${programId}`);

    } catch (error) {
      console.error(`[useLessonProgress] Failed to fetch progress for program ${programId}:`, error);
      // Initialize with default state if fetch fails
      setProgressState(prev => ({
        ...prev,
        [programId]: {
          programId,
          completedLessons: [],
          currentLesson: 1
        }
      }));
      console.log(`[useLessonProgress] Set default progress state for ${programId} due to error`);
    } finally {
      setLoadingPrograms(prev => {
        const updated = new Set(prev);
        updated.delete(programId);
        return updated;
      });
      console.log(`[useLessonProgress] Finished loading progress for ${programId}`);
    }
  };

  const fetchProgramProgressAndReturn = async (programId: string): Promise<LessonProgress> => {
    if (loadingPrograms.has(programId)) {
      console.log(`[useLessonProgress] Already loading progress for program ${programId}`);
      // Return current state if exists, otherwise default
      return progressState[programId] || {
        programId,
        completedLessons: [],
        currentLesson: 1
      };
    }

    console.log(`[useLessonProgress] Starting to fetch progress for program ${programId} (with return)`);

    try {
      setLoadingPrograms(prev => new Set([...prev, programId]));
      
      // Get the program details first to get all lessons
      console.log(`[useLessonProgress] Fetching program details for ${programId}`);
      const program = await lifeCurriculumApi.getProgramById(programId);
      
      if (!program) {
        console.warn(`[useLessonProgress] Program ${programId} not found`);
        const defaultProgress = {
          programId,
          completedLessons: [],
          currentLesson: 1
        };
        return defaultProgress;
      }

      console.log(`[useLessonProgress] Program found: ${program.title}, checking lessons...`);
      const completedLessons: number[] = [];
      
      // Check each lesson (assuming 5-day program)
      for (let day = 1; day <= 5; day++) {
        try {
          console.log(`[useLessonProgress] Checking lesson ${day} for program ${programId}`);
          const lesson = await lifeCurriculumApi.getSingleLesson(programId, day);
          console.log(`[useLessonProgress] Lesson ${day} status:`, lesson?.status || 'not found');
          
          if (lesson && lesson.status === 'completed') {
            completedLessons.push(day);
            console.log(`[useLessonProgress] Added day ${day} to completed lessons`);
          }
        } catch (err) {
          // Lesson might not exist yet, that's ok
          console.debug(`[useLessonProgress] Lesson ${day} for program ${programId} not found or error:`, err);
        }
      }

      // Sort completed lessons
      completedLessons.sort((a, b) => a - b);
      console.log(`[useLessonProgress] Completed lessons for ${programId}:`, completedLessons);

      // Determine next available lesson
      const currentLesson = completedLessons.length > 0 
        ? Math.min(Math.max(...completedLessons) + 1, 5)
        : 1;

      console.log(`[useLessonProgress] Next available lesson for ${programId}: ${currentLesson}`);

      const progressData = {
        programId,
        completedLessons,
        currentLesson
      };

      // Update state as well
      setProgressState(prev => ({
        ...prev,
        [programId]: progressData
      }));

      console.log(`[useLessonProgress] Progress state updated for ${programId}, returning data:`, progressData);
      return progressData;

    } catch (error) {
      console.error(`[useLessonProgress] Failed to fetch progress for program ${programId}:`, error);
      // Return default state if fetch fails
      const defaultProgress = {
        programId,
        completedLessons: [],
        currentLesson: 1
      };
      
      setProgressState(prev => ({
        ...prev,
        [programId]: defaultProgress
      }));
      
      console.log(`[useLessonProgress] Set default progress state for ${programId} due to error`);
      return defaultProgress;
    } finally {
      setLoadingPrograms(prev => {
        const updated = new Set(prev);
        updated.delete(programId);
        return updated;
      });
      console.log(`[useLessonProgress] Finished loading progress for ${programId}`);
    }
  };

  const initializeProgram = async (programId: string): Promise<LessonProgress> => {
    console.log(`[useLessonProgress] Initializing program ${programId}`);
    
    // First set a default state
    const defaultProgress = {
      programId,
      completedLessons: [],
      currentLesson: 1
    };
    
    setProgressState(prev => ({
      ...prev,
      [programId]: prev[programId] || defaultProgress
    }));

    console.log(`[useLessonProgress] Set default state for ${programId}, now fetching actual progress`);
    
    // Then fetch actual progress from API and return it
    const actualProgress = await fetchProgramProgressAndReturn(programId);
    
    console.log(`[useLessonProgress] Program ${programId} initialization complete, returning:`, actualProgress);
    return actualProgress;
  };

  const markLessonCompleted = async (programId: string, dayNumber: number) => {
    console.log(`[useLessonProgress] Marking lesson ${dayNumber} as completed for program ${programId}`);
    
    // Update local state immediately for UI responsiveness
    setProgressState(prev => {
      const programProgress = prev[programId] || {
        programId,
        completedLessons: [],
        currentLesson: 1
      };

      const completedLessons = [...programProgress.completedLessons];
      
      // Add lesson to completed if not already there
      if (!completedLessons.includes(dayNumber)) {
        completedLessons.push(dayNumber);
        completedLessons.sort((a, b) => a - b); // Keep sorted
        console.log(`[useLessonProgress] Added day ${dayNumber} to completed lessons for ${programId}`);
      } else {
        console.log(`[useLessonProgress] Day ${dayNumber} already marked as completed for ${programId}`);
      }

      // Update current lesson to next available
      const nextLesson = Math.max(...completedLessons) + 1;
      console.log(`[useLessonProgress] Next lesson for ${programId} will be ${nextLesson}`);

      return {
        ...prev,
        [programId]: {
          ...programProgress,
          completedLessons,
          currentLesson: Math.min(nextLesson, 5) // Assuming 5-day programs
        }
      };
    });

    // Also refresh from API to ensure consistency
    console.log(`[useLessonProgress] Refreshing progress from API for ${programId}`);
    await fetchProgramProgress(programId);
  };

  const refreshProgramProgress = async (programId: string) => {
    console.log(`[useLessonProgress] Refreshing progress for program ${programId}`);
    await fetchProgramProgress(programId);
  };

  const isLessonAvailable = (programId: string, dayNumber: number): boolean => {
    const programProgress = progressState[programId];
    console.log(`[useLessonProgress] Checking availability for program ${programId}, day ${dayNumber}`);
    console.log(`[useLessonProgress] Current progress state:`, programProgress);
    
    // If no progress exists, only day 1 is available
    if (!programProgress) {
      console.log(`[useLessonProgress] No progress found for ${programId}, only day 1 available`);
      return dayNumber === 1;
    }

    // Day 1 is always available
    if (dayNumber === 1) {
      console.log(`[useLessonProgress] Day 1 is always available for ${programId}`);
      return true;
    }

    // Check if previous lesson is completed
    const previousCompleted = programProgress.completedLessons.includes(dayNumber - 1);
    console.log(`[useLessonProgress] Day ${dayNumber - 1} completed: ${previousCompleted}`);
    console.log(`[useLessonProgress] Day ${dayNumber} available: ${previousCompleted}`);
    
    return previousCompleted;
  };

  const isLessonCompleted = (programId: string, dayNumber: number): boolean => {
    const programProgress = progressState[programId];
    const completed = programProgress?.completedLessons.includes(dayNumber) || false;
    console.log(`[useLessonProgress] Is day ${dayNumber} completed for ${programId}? ${completed}`);
    return completed;
  };

  const getProgramProgress = (programId: string): LessonProgress | null => {
    return progressState[programId] || null;
  };

  const resetProgramProgress = (programId: string) => {
    setProgressState(prev => {
      const newState = { ...prev };
      delete newState[programId];
      return newState;
    });
  };

  const getAllProgress = (): LessonProgressState => {
    return progressState;
  };

  return {
    initializeProgram,
    markLessonCompleted,
    isLessonAvailable,
    isLessonCompleted,
    getProgramProgress,
    resetProgramProgress,
    refreshProgramProgress,
    getAllProgress
  };
}
