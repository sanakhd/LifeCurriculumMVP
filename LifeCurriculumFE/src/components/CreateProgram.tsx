import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check } from 'lucide-react';
import lifeCurriculumApi from '../services/api';
import type { GenerateFullProgramRequest, ContextType } from '../types/api';
import '../styles/CreateProgram.css';


const STEPS = [
  { number: 1, label: 'What to Learn' },
  { number: 2, label: 'Learning Outcome' },
  { number: 3, label: 'Learning Setting' },
] as const;

const CONTEXT_OPTIONS: {
  value: ContextType;
  label: string;
  description: string;
  locked?: boolean;
}[] = [
  {
    value: 'home',
    label: 'Home',
    description: 'Perfect for focused learning with text-based interactions and detailed reflections',
  },
  {
    value: 'workout',
    label: 'Workout',
    description: 'Quick tap interactions designed for active learning while exercising',
  },
  {
    value: 'driving',
    label: 'Driving',
    description: 'Audio-only lessons perfect for hands-free learning while commuting',
  },
];

interface FormData {
  focus_area: string;
  target_outcome: string;
  context: ContextType;
}

function CreateProgram() {
  const navigate = useNavigate();

  // ----- Local state -----
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null); // kept private to this file
  const [formData, setFormData] = useState<FormData>({
    focus_area: '',
    target_outcome: '',
    context: 'home',
  });

  // ----- Helpers -----
  const trimmedFocus = useMemo(
    () => formData.focus_area.trim(),
    [formData.focus_area]
  );
  const trimmedOutcome = useMemo(
    () => formData.target_outcome.trim(),
    [formData.target_outcome]
  );

  const isCurrentStepValid = useCallback((): boolean => {
    switch (currentStep) {
      case 1:
        return trimmedFocus.length >= 5;
      case 2:
        return trimmedOutcome.length >= 5;
      case 3:
        return formData.context !== null;
      default:
        return false;
    }
  }, [currentStep, trimmedFocus, trimmedOutcome, formData.context]);

  const goToStep = useCallback((next: number) => {
    setCurrentStep((prev) => {
      if (next < 1) return 1;
      if (next > 3) return 3;
      return next;
    });
  }, []);

  const handleNext = useCallback(() => {
    if (currentStep < 3) goToStep(currentStep + 1);
  }, [currentStep, goToStep]);

  const handleBack = useCallback(() => {
    if (currentStep > 1) goToStep(currentStep - 1);
  }, [currentStep, goToStep]);

  const handleTextChange = useCallback(
    (key: keyof FormData) =>
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setFormData((prev) => ({ ...prev, [key]: e.target.value }));
      },
    []
  );

  const handleContextChange = useCallback(
    (value: ContextType) => {
      setFormData((prev) => ({ ...prev, context: value }));
    },
    []
  );

  const handleSubmit = useCallback(async () => {
    // Validate current step before submitting
    if (!isCurrentStepValid()) return;

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const request: GenerateFullProgramRequest = {
        focus_area: trimmedFocus,
        target_outcome: trimmedOutcome,
        context: formData.context,
        generate_audio: true, // Can be customized later
      };

      await lifeCurriculumApi.generateFullProgram(request);
      navigate('/programs');
    } catch (error) {
      console.error('Error generating program:', error);
      setErrorMessage('Something went wrong while creating your program. Please try again.');
    } finally {
      // Only stop the loading state if we didn't navigate (i.e., on error)
      setIsLoading(false);
    }
  }, [formData.context, isCurrentStepValid, navigate, trimmedFocus, trimmedOutcome]);

  // ----- UI bits -----

  // Progress bar as an inline component (kept for cohesion).
  const ProgressBar = useCallback(() => (
    <div className="create-program-progress" role="progressbar" aria-valuemin={1} aria-valuemax={3} aria-valuenow={currentStep}>
      {STEPS.map((step) => {
        const isActive = currentStep >= step.number;
        const isCompleted = currentStep > step.number;
        return (
          <div key={step.number} className="create-program-step">
            <div
              className={`step-number ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              aria-current={currentStep === step.number ? 'step' : undefined}
            >
              {isCompleted ? <Check size={16} aria-hidden="true" /> : step.number}
            </div>
            <div className="step-label">{step.label}</div>
          </div>
        );
      })}
    </div>
  ), [currentStep]);

  // Renders the main content for the current step.
  const renderStepContent = useCallback(() => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            <h2>What do you want to learn about?</h2>
            <p>Tell us what skill, habit, or area you'd like to focus on for the next 5 days.</p>
            <textarea
              value={formData.focus_area}
              onChange={handleTextChange('focus_area')}
              placeholder="e.g., Building morning routines, Speaking with confidence, Managing stress..."
              className="text-input"
              rows={4}
              maxLength={500}
              aria-label="What to learn"
            />
            <div className="character-count">
              {formData.focus_area.length}/500 characters
              {formData.focus_area.length < 5 && (
                <span className="requirement"> (minimum 5 characters)</span>
              )}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <h2>By the end of 5 days, I want to…</h2>
            <p>Describe what you hope to achieve or how you want to feel after completing this program.</p>
            <textarea
              value={formData.target_outcome}
              onChange={handleTextChange('target_outcome')}
              placeholder="e.g., I want to feel more energized in the mornings, I want to speak up confidently in meetings..."
              className="text-input"
              rows={4}
              maxLength={500}
              aria-label="Learning outcome"
            />
            <div className="character-count">
              {formData.target_outcome.length}/500 characters
              {formData.target_outcome.length < 5 && (
                <span className="requirement"> (minimum 5 characters)</span>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content">
            <h2>What is the setting of your learning?</h2>
            <p>Choose where you'll primarily be engaging with your program.</p>
            <div className="context-options" role="radiogroup" aria-label="Learning setting">
              {CONTEXT_OPTIONS.map((option) => {
                const selected = formData.context === option.value;
                const locked = !!option.locked;

                return (
                  <div
                    key={option.value}
                    className={`context-option ${selected ? 'selected' : ''} ${locked ? 'locked' : ''}`}
                    onClick={() => !locked && handleContextChange(option.value)}
                    role="radio"
                    aria-checked={selected}
                    aria-disabled={locked}
                    tabIndex={locked ? -1 : 0}
                    onKeyDown={(e) => {
                      if (locked) return;
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleContextChange(option.value);
                      }
                    }}
                  >
                    <div className="option-header">
                      <input
                        type="radio"
                        name="context"
                        value={option.value}
                        checked={selected}
                        disabled={locked}
                        onChange={(e) => !locked && handleContextChange(e.target.value as ContextType)}
                        aria-label={option.label}
                      />
                      <label>{option.label}</label>
                    </div>
                    <div className="option-description">{option.description}</div>
                  </div>
                );
              })}
            </div>
          </div>
        );

      default:
        return null;
    }
  }, [currentStep, formData.context, formData.focus_area.length, formData.target_outcome.length, handleContextChange, handleTextChange]);

  // ----- Render -----

  if (isLoading) {
    return (
      <div className="create-program-container">
        <div className="loading-screen" aria-busy="true" aria-live="polite">
          <div className="loading-spinner"></div>
          <h2>Creating Your Program</h2>
          <p>We're generating your personalized 5-day learning journey...</p>
        </div>
      </div>
    );
  }

  const nextDisabled = !isCurrentStepValid();
  const isFinalStep = currentStep === 3;

  return (
    <div className="create-program-container">
      <div className="create-program-content">
        <ProgressBar />

        {renderStepContent()}

        {/* Lightweight error surface (non-intrusive; style via existing css file if desired) */}
        {errorMessage && (
          <div role="alert" className="error-message" style={{ marginTop: 12 }}>
            {errorMessage}
          </div>
        )}

        <div className="step-actions">
          {currentStep > 1 && (
            <button
              type="button"
              className="back-btn"
              onClick={handleBack}
              aria-label="Back"
            >
              Back
            </button>
          )}

          <button
            type="button"
            className={`next-btn ${nextDisabled ? 'disabled' : ''}`}
            onClick={isFinalStep ? handleSubmit : handleNext}
            disabled={nextDisabled}
            aria-disabled={nextDisabled}
            aria-label={isFinalStep ? 'Create Program' : 'Next'}
          >
            {isFinalStep ? 'Create Program' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateProgram;
