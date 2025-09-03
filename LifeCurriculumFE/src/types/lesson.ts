// Field configuration for teach_back and self_explanation interactions
export interface InteractionField {
  id: string;
  label: string;
  max_chars?: number;
}

// Base interaction interface
export interface BaseInteraction {
  type: string;
  prompt: string;
  instructions?: string;
}

// Multiple choice interaction
export interface MultipleChoiceInteraction extends BaseInteraction {
  type: 'multiple_choice';
  options: string[];
  correct_option: string;
}

// Reflection prompt interaction
export interface ReflectionPromptInteraction extends BaseInteraction {
  type: 'reflection_prompt';
  placeholder?: string;
  min_words?: number;
}

// Teach back interaction
export interface TeachBackInteraction extends BaseInteraction {
  type: 'teach_back';
  config?: {
    fields?: InteractionField[];
  };
}

// Self explanation interaction
export interface SelfExplanationInteraction extends BaseInteraction {
  type: 'self_explanation';
  config?: {
    fields?: InteractionField[];
  };
}

// Ordering interaction
export interface OrderingInteraction extends BaseInteraction {
  type: 'ordering_interaction';
  options: string[]; // 2-4 items
  correct_order: string[];
}

// Matching interaction
export interface MatchingInteraction extends BaseInteraction {
  type: 'matching_interaction';
  pairs: Record<string, string>; // concept -> example mapping
}

// Union type for all possible interactions
export type PrimaryInteraction =
  | MultipleChoiceInteraction
  | ReflectionPromptInteraction
  | TeachBackInteraction
  | SelfExplanationInteraction
  | OrderingInteraction
  | MatchingInteraction;

export interface LessonData {
  id: string;
  title: string;
  content: string;
  transcript: string;
  conversationChunks: any[];
  primary_interaction?: PrimaryInteraction;
  learning_objectives?: string[];
  description?: string;
  context?: 'home' | 'driving' | 'workout';
}

export interface AudioSegment {
  audio_id: string;
  speaker: string;
  voice: string;
  duration_seconds: number;
  chunk_index: number;
  stream_url: string;
  text: string;
}

export interface EvaluationFeedback {
  feedback: string;
  lesson_title: string;
  prompt_text: string;
  evaluation_timestamp?: string;
  model_used?: string | null;
}

export interface LessonProgress {
  lessonStartTime: Date | null;
  isLessonCompleted: boolean;
  audioLoadingProgress: number;
}

export interface AudioState {
  isPlaying: boolean;
  currentSegmentIndex: number;
  audioSegments: AudioSegment[];
}

export interface QuestionState {
  showLearningQuestion: boolean;
  userAnswer: string;
  selectedChoice: string;
  sliderValue: number;
  isAnswerSubmitted: boolean;
  isEvaluating: boolean;
  aiFeedback: EvaluationFeedback | null;
  evaluationError: string | null;
}
