import type {
  HealthResponse,
  GenerateProgramRequest,
  GenerateProgramResponse,
  GenerateFullProgramRequest,
  GenerateFullProgramResponse,
  GenerateLessonIn,
  GenerateLessonOut,
  ProgramListResponse,
  ProgramListParams,
  GenerateLessonAudioRequest,
  GenerateLessonAudioResponse,
  AudioStatusResponse,
  DeleteAudioResponse,
  LessonIdsResponse,
  AudioStreamResponse,
  AudioPlaylistResponse,
  BaseResponse,
  CompleteLessonRequest,
  CompleteLessonResponse,
  EvaluateAnswerRequest,
  EvaluateAnswerResponse,
} from '../types/api';

// Configuration
const BASE_URL = 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class LifeCurriculumApi {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: response.statusText };
        }
        
        throw new ApiError(
          response.status,
          errorData.detail?.[0]?.msg || errorData.message || `HTTP ${response.status}`,
          errorData
        );
      }

      // Handle empty responses
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return {} as T;
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        0,
        error instanceof Error ? error.message : 'Network error',
        error
      );
    }
  }

  // Health Check Endpoints
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async ping(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/ping');
  }

  // Program Generation Endpoints
  async generateProgram(request: GenerateProgramRequest): Promise<GenerateProgramResponse> {
    return this.request<GenerateProgramResponse>('/api/v1/generate-program', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async generateFullProgram(request: GenerateFullProgramRequest): Promise<GenerateFullProgramResponse> {
    return this.request<GenerateFullProgramResponse>('/api/v1/generate-full-program', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Program Management Endpoints
  async getProgramById(programId: string): Promise<Record<string, any>> {
    console.log(`[API] Fetching program by ID: ${programId}`);
    const result = await this.request<Record<string, any>>(`/api/v1/programs/${programId}`);
    console.log(`[API] Program ${programId} fetched successfully:`, result);
    return result;
  }

  async listAllPrograms(params?: ProgramListParams): Promise<ProgramListResponse> {
    console.log('[API] Fetching all programs list with params:', params);
    
    const queryParams = new URLSearchParams();
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    
    const query = queryParams.toString();
    const endpoint = query ? `/api/v1/programs?${query}` : '/api/v1/programs';
    
    console.log(`[API] Making request to endpoint: ${endpoint}`);
    const result = await this.request<ProgramListResponse>(endpoint);
    console.log(`[API] Programs list fetched successfully:`, result);
    return result;
  }

  // Lesson Endpoints
  async generateLesson(request: GenerateLessonIn): Promise<GenerateLessonOut> {
    return this.request<GenerateLessonOut>('/api/v1/programs/generate-lesson', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSingleLesson(programId: string, dayNumber: number): Promise<any> {
    console.log(`[API] Fetching lesson for program ${programId}, day ${dayNumber}`);
    try {
      const result = await this.request<any>(`/api/v1/programs/${programId}/lessons/${dayNumber}`);
      console.log(`[API] Lesson ${dayNumber} for program ${programId} fetched successfully:`, result);
      return result;
    } catch (error) {
      console.error(`[API] Failed to fetch lesson ${dayNumber} for program ${programId}:`, error);
      throw error;
    }
  }

  async getAllLessonIds(): Promise<LessonIdsResponse> {
    return this.request<LessonIdsResponse>('/api/v1/programs/lessons/ids');
  }

  // Audio Generation Endpoints
  async generateLessonAudio(request: GenerateLessonAudioRequest): Promise<GenerateLessonAudioResponse> {
    return this.request<GenerateLessonAudioResponse>('/api/v1/programs/generate-lesson-audio', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async regenerateLessonAudio(request: GenerateLessonAudioRequest): Promise<GenerateLessonAudioResponse> {
    return this.request<GenerateLessonAudioResponse>('/api/v1/programs/regenerate-lesson-audio', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getLessonAudioStatus(lessonUuid: string): Promise<AudioStatusResponse> {
    return this.request<AudioStatusResponse>(`/api/v1/programs/lessons/${lessonUuid}/audio-status`);
  }

  async deleteLessonAudio(lessonUuid: string): Promise<DeleteAudioResponse> {
    return this.request<DeleteAudioResponse>(`/api/v1/programs/lessons/${lessonUuid}/audio`, {
      method: 'DELETE',
    });
  }

  async getAvailableVoices(): Promise<any> {
    return this.request<any>('/api/v1/programs/available-voices');
  }

  // Audio Streaming Endpoints
  async getAudioFileInfo(lessonUuid: string, audioId: string): Promise<AudioStreamResponse> {
    return this.request<AudioStreamResponse>(`/api/v1/programs/lessons/${lessonUuid}/audio/${audioId}/info`);
  }

  async getLessonAudioPlaylist(lessonUuid: string): Promise<AudioPlaylistResponse> {
    return this.request<AudioPlaylistResponse>(`/api/v1/programs/lessons/${lessonUuid}/audio/playlist`);
  }

  // Get streaming URL for audio file
  getAudioStreamUrl(lessonUuid: string, audioId: string, chunkSize?: number): string {
    const params = chunkSize ? `?chunk_size=${chunkSize}` : '';
    return `${this.baseUrl}/api/v1/programs/lessons/${lessonUuid}/audio/${audioId}/stream${params}`;
  }

  // Lesson Completion Endpoints
  async completeLesson(lessonId: string, request: CompleteLessonRequest): Promise<CompleteLessonResponse> {
    return this.request<CompleteLessonResponse>(`/api/v1/lessons/${lessonId}/complete`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async startLesson(lessonId: string): Promise<BaseResponse> {
    return this.request<BaseResponse>(`/api/v1/lessons/${lessonId}/start`, {
      method: 'POST',
    });
  }

  // Lesson Answer Evaluation Endpoint
  async evaluateLessonAnswer(lessonId: string, request: EvaluateAnswerRequest): Promise<EvaluateAnswerResponse> {
    return this.request<EvaluateAnswerResponse>(`/api/v1/programs/lessons/${lessonId}/evaluate-answer`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

// Create and export a singleton instance
export const lifeCurriculumApi = new LifeCurriculumApi();

// Export the class for custom instances if needed
export { LifeCurriculumApi, ApiError };

// Export default instance
export default lifeCurriculumApi;
