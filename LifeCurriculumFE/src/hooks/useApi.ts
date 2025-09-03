import { useState, useCallback } from 'react';
import type {
  GenerateProgramRequest,
  GenerateProgramResponse,
  GenerateFullProgramRequest,
  GenerateFullProgramResponse,
  ProgramListResponse,
  ProgramListParams,
  GenerateLessonIn,
  GenerateLessonOut,
  GenerateLessonAudioRequest,
  GenerateLessonAudioResponse,
  AudioStatusResponse,
  DeleteAudioResponse,
  LessonIdsResponse,
  HealthResponse,
} from '../types/api';
import { lifeCurriculumApi, ApiError } from '../services/api';

// Generic hook for API calls with loading and error states
export function useApiCall<TRequest, TResponse>(
  apiMethod: (request: TRequest) => Promise<TResponse>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TResponse | null>(null);

  const execute = useCallback(
    async (request: TRequest) => {
      setLoading(true);
      setError(null);
      
      try {
        const result = await apiMethod(request);
        setData(result);
        return result;
      } catch (err) {
        const errorMessage = err instanceof ApiError ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiMethod]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setData(null);
  }, []);

  return { execute, loading, error, data, reset };
}

// Hook for no-parameter API calls
export function useApiCallNoParams<TResponse>(
  apiMethod: () => Promise<TResponse>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TResponse | null>(null);

  const execute = useCallback(
    async () => {
      setLoading(true);
      setError(null);
      
      try {
        const result = await apiMethod();
        setData(result);
        return result;
      } catch (err) {
        const errorMessage = err instanceof ApiError ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiMethod]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setData(null);
  }, []);

  return { execute, loading, error, data, reset };
}

// Specific hooks for common operations

// Health check hooks
export const useHealthCheck = () => {
  return useApiCallNoParams(() => lifeCurriculumApi.healthCheck());
};

export const usePing = () => {
  return useApiCallNoParams(() => lifeCurriculumApi.ping());
};

// Program generation hooks
export const useGenerateProgram = () => {
  return useApiCall<GenerateProgramRequest, GenerateProgramResponse>(
    (request) => lifeCurriculumApi.generateProgram(request)
  );
};

export const useGenerateFullProgram = () => {
  return useApiCall<GenerateFullProgramRequest, GenerateFullProgramResponse>(
    (request) => lifeCurriculumApi.generateFullProgram(request)
  );
};

// Program management hooks
export const useGetProgramById = () => {
  return useApiCall<string, Record<string, any>>(
    (programId) => lifeCurriculumApi.getProgramById(programId)
  );
};

export const useListAllPrograms = () => {
  return useApiCall<ProgramListParams | undefined, ProgramListResponse>(
    (params) => lifeCurriculumApi.listAllPrograms(params)
  );
};

// Lesson hooks
export const useGenerateLesson = () => {
  return useApiCall<GenerateLessonIn, GenerateLessonOut>(
    (request) => lifeCurriculumApi.generateLesson(request)
  );
};

export const useGetSingleLesson = () => {
  return useApiCall<{ programId: string; dayNumber: number }, any>(
    ({ programId, dayNumber }) => lifeCurriculumApi.getSingleLesson(programId, dayNumber)
  );
};

export const useGetAllLessonIds = () => {
  return useApiCallNoParams(() => lifeCurriculumApi.getAllLessonIds());
};

// Audio hooks
export const useGenerateLessonAudio = () => {
  return useApiCall<GenerateLessonAudioRequest, GenerateLessonAudioResponse>(
    (request) => lifeCurriculumApi.generateLessonAudio(request)
  );
};

export const useRegenerateLessonAudio = () => {
  return useApiCall<GenerateLessonAudioRequest, GenerateLessonAudioResponse>(
    (request) => lifeCurriculumApi.regenerateLessonAudio(request)
  );
};

export const useGetLessonAudioStatus = () => {
  return useApiCall<string, AudioStatusResponse>(
    (lessonUuid) => lifeCurriculumApi.getLessonAudioStatus(lessonUuid)
  );
};

export const useDeleteLessonAudio = () => {
  return useApiCall<string, DeleteAudioResponse>(
    (lessonUuid) => lifeCurriculumApi.deleteLessonAudio(lessonUuid)
  );
};

export const useGetAvailableVoices = () => {
  return useApiCallNoParams(() => lifeCurriculumApi.getAvailableVoices());
};
