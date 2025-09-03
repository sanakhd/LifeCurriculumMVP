// Core API Types from OpenAPI Schema
export type ContextType = 'home' | 'driving' | 'workout';

// Health Check Types
export interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
  version: string;
}

// Validation Error Types
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

// Program Generation Types
export interface GenerateProgramRequest {
  focus_area: string; // minimum 5 characters
  target_outcome: string; // minimum 5 characters
  context: ContextType;
  prompt?: string;
}

export interface GenerateProgramResponse {
  status: string;
  program_id: string;
  title: string;
  description: string;
  outline: Record<string, any>[];
  timestamp: string;
}

// Full Program Generation Types
export interface GenerateFullProgramRequest {
  focus_area: string; // minimum 5 characters
  target_outcome: string; // minimum 5 characters
  context: ContextType;
  prompt?: string;
  model?: string;
  generate_audio?: boolean;
  voice_mapping?: Record<string, string>;
}

export interface GenerateFullProgramResponse {
  status: string;
  program_id: string;
  title: string;
  description: string;
  outline: Record<string, any>[];
  lessons: Record<string, any>[];
  generation_stats: GenerationStats;
  timestamp: string;
}

// Lesson Generation Types
export interface GenerateLessonIn {
  program_id: string;
  day_number: number; // minimum 1
  model?: string;
}

export interface GenerateLessonOut {
  success: boolean;
  program_id: string;
  day_number: number;
  lesson_id: string;
}

// Program List Types
export interface ProgramListResponse {
  items: Record<string, any>[];
  offset: number;
  limit: number;
}

// Audio Generation Types
export interface AudioFileMetadata {
  chunk_index: number;
  audio_id?: string;
  speaker: string;
  voice?: string;
  file_path?: string;
  duration_seconds?: number;
  regenerated: boolean;
  error?: string;
}

export interface GenerateLessonAudioRequest {
  lesson_uuid: string;
  voice_mapping?: Record<string, string>;
}

export interface GenerateLessonAudioResponse {
  success: boolean;
  lesson_id: string;
  audio_files: AudioFileMetadata[];
  total_duration_seconds: number;
  files_generated: number;
  files_total: number;
  manifest_path: string;
}

export interface AudioStatusResponse {
  exists: boolean;
  lesson_id?: string;
  has_conversation_chunks?: boolean;
  total_chunks?: number;
  manifest?: Record<string, any>;
  audio_directory?: string;
  error?: string;
}

export interface DeleteAudioResponse {
  success: boolean;
  lesson_id?: string;
  deleted_files?: string[];
  files_deleted?: number;
  message?: string;
  error?: string;
}

// Statistics Types
export interface AudioGenerationStats {
  audio_generation_enabled: boolean;
  lessons_with_audio?: number;
  audio_files_generated?: number;
  audio_generation_time_seconds?: number;
  audio_errors?: string[];
}

export interface GenerationStats {
  program_generation_time_seconds: number;
  lesson_generation_times_seconds: number[];
  total_time_seconds: number;
  lessons_generated: number;
  errors_encountered?: string[];
  audio_stats: AudioGenerationStats;
}

// Lesson IDs Types
export interface LessonIdsResponse {
  lesson_ids: string[];
  count: number;
}

// Audio Streaming Types
export interface AudioStreamResponse {
  lesson_uuid: string;
  audio_id: string;
  speaker: string;
  voice: string;
  duration_seconds: number;
  chunk_index: number;
  file_size_bytes: number;
}

export interface AudioPlaylistItem {
  audio_id: string;
  speaker: string;
  voice: string;
  duration_seconds: number;
  chunk_index: number;
  stream_url: string;
  text?: string;
}

export interface AudioPlaylistResponse {
  lesson_uuid: string;
  total_chunks: number;
  total_duration_seconds: number;
  playlist: AudioPlaylistItem[];
}

// Lesson Completion Types
export interface BaseResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

export interface CompleteLessonRequest {
  time_spent_seconds?: number;
  completion_method?: string;
  user_rating?: number;
}

export interface CompleteLessonResponse extends BaseResponse {
  lesson_id: string;
  completed_at: string;
  previous_status: string;
  time_spent_seconds?: number;
}

// Evaluate Answer Types
export interface EvaluateAnswerRequest {
  // For multiple_choice interactions
  selected_option?: string;
  
  // For reflection_prompt interactions or free text teach_back/self_explanation
  user_answer?: string; // 1-2000 characters
  
  // For structured teach_back/self_explanation with config.fields
  field_values?: Record<string, string>;
  
  // For ordering_interaction
  selected_order?: string[];
  
  // For matching_interaction
  selected_pairs?: Record<string, string>;
}

export interface EvaluateAnswerResponse {
  feedback: string;
  lesson_title: string;
  prompt_text: string;
  evaluation_timestamp?: string;
  model_used?: string;
}

// API Query Parameters
export interface ProgramListParams {
  offset?: number;
  limit?: number;
}
