import React, { useState, useCallback } from 'react';
import { CheckCircle, XCircle, FileText, Bot, Lightbulb, Mic, MicOff, ArrowUpDown, Link, RotateCcw } from 'lucide-react';
import { lifeCurriculumApi } from '../../services/api';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import type { LessonData, EvaluationFeedback, PrimaryInteraction, InteractionField } from '../../types/lesson';
import type { EvaluateAnswerRequest } from '../../types/api';

interface LearningQuestionProps {
  lessonData: LessonData;
  onLessonComplete: () => void;
}

export const LearningQuestion: React.FC<LearningQuestionProps> = ({ 
  lessonData, 
  onLessonComplete 
}) => {
  // State for different interaction types
  const [userAnswer, setUserAnswer] = useState('');
  const [selectedChoice, setSelectedChoice] = useState('');
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [selectedOrder, setSelectedOrder] = useState<string[]>([]);
  const [selectedPairs, setSelectedPairs] = useState<Record<string, string>>({});
  
  // General state
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [aiFeedback, setAiFeedback] = useState<EvaluationFeedback | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  const { isRecording, speechSupported, toggleRecording } = useSpeechRecognition();

  const handleSpeechResult = useCallback((transcript: string) => {
    setUserAnswer(prev => prev + transcript);
  }, []);

  const handleSpeechToggle = useCallback(() => {
    toggleRecording(handleSpeechResult);
  }, [toggleRecording, handleSpeechResult]);

  // Handle field value changes for structured interactions
  const handleFieldChange = useCallback((fieldId: string, value: string, maxChars?: number) => {
    if (maxChars && value.length > maxChars) {
      return; // Don't allow exceeding character limit
    }
    setFieldValues(prev => ({ ...prev, [fieldId]: value }));
  }, []);

  // Handle ordering interaction
  const handleOrderingItemClick = useCallback((item: string) => {
    setSelectedOrder(prev => {
      if (prev.includes(item)) {
        return prev.filter(i => i !== item);
      } else {
        return [...prev, item];
      }
    });
  }, []);

  const resetOrderingSelection = useCallback(() => {
    setSelectedOrder([]);
  }, []);

  // Handle matching interaction
  const handleMatchingPairChange = useCallback((concept: string, example: string) => {
    setSelectedPairs(prev => ({ ...prev, [concept]: example }));
  }, []);

  const handleAnswerSubmit = async () => {
    if (!lessonData?.id || !lessonData.primary_interaction) return;

    const interaction = lessonData.primary_interaction;
    const interactionType = interaction.type;
    
    // Validation based on interaction type
    if (interactionType === 'multiple_choice' && !selectedChoice.trim()) return;
    if (interactionType === 'reflection_prompt' && !userAnswer.trim()) return;
    if (interactionType === 'teach_back' || interactionType === 'self_explanation') {
      const hasFields = interaction.config?.fields && interaction.config.fields.length > 0;
      if (hasFields) {
        const hasAllFields = interaction.config!.fields!.every(field => fieldValues[field.id]?.trim());
        if (!hasAllFields) return;
      } else if (!userAnswer.trim()) {
        return;
      }
    }
    if (interactionType === 'ordering_interaction' && selectedOrder.length === 0) return;
    if (interactionType === 'matching_interaction') {
      const concepts = Object.keys(interaction.pairs);
      const hasAllPairs = concepts.every(concept => selectedPairs[concept]);
      if (!hasAllPairs) return;
    }

    setIsEvaluating(true);
    setEvaluationError(null);

    try {
      let requestBody: EvaluateAnswerRequest;

      switch (interactionType) {
        case 'multiple_choice':
          requestBody = { selected_option: selectedChoice };
          break;
        case 'reflection_prompt':
          requestBody = { user_answer: userAnswer.trim() };
          break;
        case 'teach_back':
        case 'self_explanation':
          if (interaction.config?.fields && interaction.config.fields.length > 0) {
            requestBody = { field_values: fieldValues };
          } else {
            requestBody = { user_answer: userAnswer.trim() };
          }
          break;
        case 'ordering_interaction':
          requestBody = { selected_order: selectedOrder };
          break;
        case 'matching_interaction':
          requestBody = { selected_pairs: selectedPairs };
          break;
        default:
          requestBody = { user_answer: userAnswer.trim() };
      }

      const response = await lifeCurriculumApi.evaluateLessonAnswer(lessonData.id, requestBody);
      setAiFeedback(response);
      setIsAnswerSubmitted(true);
    } catch (err: any) {
      setEvaluationError(err?.message || 'Failed to evaluate answer');
    } finally {
      setIsEvaluating(false);
    }
  };

  const renderInteractionInput = () => {
    const interaction = lessonData.primary_interaction;
    if (!interaction) return null;

    switch (interaction.type) {
      case 'multiple_choice':
        return (
          <div className="multiple-choice-container">
            <div className="radio-options">
              {interaction.options.map((option, idx) => (
                <label key={idx} className="radio-option">
                  <input
                    type="radio"
                    name="multiple-choice"
                    value={option}
                    checked={selectedChoice === option}
                    onChange={(e) => setSelectedChoice(e.target.value)}
                    disabled={isAnswerSubmitted}
                  />
                  <span className="radio-label">{option}</span>
                </label>
              ))}
            </div>
          </div>
        );

      case 'reflection_prompt':
        return (
          <div className="textarea-container">
            <textarea
              className="answer-textarea"
              placeholder={interaction.placeholder || 'Enter your reflection here...'}
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              rows={6}
              disabled={isAnswerSubmitted}
            />
            {speechSupported && (
              <button
                className={`speech-btn ${isRecording ? 'recording' : ''}`}
                onClick={handleSpeechToggle}
                title={isRecording ? 'Stop recording' : 'Start voice input'}
                disabled={isAnswerSubmitted}
              >
                {isRecording ? <Mic size={20} /> : <MicOff size={20} />}
              </button>
            )}
          </div>
        );

      case 'teach_back':
      case 'self_explanation':
        if (interaction.config?.fields && interaction.config.fields.length > 0) {
          return (
            <div className="structured-fields-container">
              {interaction.config.fields.map((field: InteractionField) => (
                <div key={field.id} className="field-group">
                  <label className="field-label">
                    {field.label}
                    {field.max_chars && (
                      <span className="char-limit">
                        ({fieldValues[field.id]?.length || 0}/{field.max_chars})
                      </span>
                    )}
                  </label>
                  <textarea
                    className="field-textarea"
                    value={fieldValues[field.id] || ''}
                    onChange={(e) => handleFieldChange(field.id, e.target.value, field.max_chars)}
                    placeholder={`Enter your ${field.label.toLowerCase()}...`}
                    rows={3}
                    disabled={isAnswerSubmitted}
                  />
                </div>
              ))}
            </div>
          );
        } else {
          return (
            <div className="textarea-container">
              <textarea
                className="answer-textarea"
                placeholder="Explain your understanding..."
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                rows={6}
                disabled={isAnswerSubmitted}
              />
              {speechSupported && (
                <button
                  className={`speech-btn ${isRecording ? 'recording' : ''}`}
                  onClick={handleSpeechToggle}
                  title={isRecording ? 'Stop recording' : 'Start voice input'}
                  disabled={isAnswerSubmitted}
                >
                  {isRecording ? <Mic size={20} /> : <MicOff size={20} />}
                </button>
              )}
            </div>
          );
        }

      case 'ordering_interaction':
        return (
          <div className="ordering-container">
            <div className="ordering-instructions">
              <p>Tap items in the correct order. Selected items will appear numbered below.</p>
              <button 
                className="reset-order-btn"
                onClick={resetOrderingSelection}
                disabled={isAnswerSubmitted}
              >
                <RotateCcw size={16} /> Reset
              </button>
            </div>
            <div className="ordering-options">
              {interaction.options.map((option) => (
                <button
                  key={option}
                  className={`ordering-option ${selectedOrder.includes(option) ? 'selected' : ''}`}
                  onClick={() => handleOrderingItemClick(option)}
                  disabled={isAnswerSubmitted}
                >
                  {selectedOrder.includes(option) && (
                    <span className="order-number">{selectedOrder.indexOf(option) + 1}</span>
                  )}
                  {option}
                </button>
              ))}
            </div>
            {selectedOrder.length > 0 && (
              <div className="selected-order">
                <h4>Your Order:</h4>
                <ol>
                  {selectedOrder.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        );

      case 'matching_interaction':
        const concepts = Object.keys(interaction.pairs);
        const examples = Object.values(interaction.pairs);
        
        return (
          <div className="matching-container">
            <div className="matching-instructions">
              <p>Match each concept with its corresponding example:</p>
            </div>
            <div className="matching-pairs">
              {concepts.map((concept) => (
                <div key={concept} className="matching-pair">
                  <div className="concept-label">{concept}</div>
                  <select
                    className="example-select"
                    value={selectedPairs[concept] || ''}
                    onChange={(e) => handleMatchingPairChange(concept, e.target.value)}
                    disabled={isAnswerSubmitted}
                  >
                    <option value="">Select an example...</option>
                    {examples.map((example) => (
                      <option key={example} value={example}>{example}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return (
          <div className="textarea-container">
            <textarea
              className="answer-textarea"
              placeholder="Enter your answer here..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              rows={6}
              disabled={isAnswerSubmitted}
            />
          </div>
        );
    }
  };

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'multiple_choice': return <CheckCircle size={24} className="inline-icon" />;
      case 'reflection_prompt': return <FileText size={24} className="inline-icon" />;
      case 'teach_back': return <Bot size={24} className="inline-icon" />;
      case 'self_explanation': return <Lightbulb size={24} className="inline-icon" />;
      case 'ordering_interaction': return <ArrowUpDown size={24} className="inline-icon" />;
      case 'matching_interaction': return <Link size={24} className="inline-icon" />;
      default: return <FileText size={24} className="inline-icon" />;
    }
  };

  const getInteractionHeader = (type: string) => {
    switch (type) {
      case 'multiple_choice': return 'Knowledge Check';
      case 'reflection_prompt': return 'Learning Reflection';
      case 'teach_back': return 'Teach Back';
      case 'self_explanation': return 'Self Explanation';
      case 'ordering_interaction': return 'Order the Steps';
      case 'matching_interaction': return 'Match the Pairs';
      default: return 'Learning Activity';
    }
  };

  const getSubmitDisabled = () => {
    if (isAnswerSubmitted || isEvaluating) return true;

    const interaction = lessonData.primary_interaction;
    if (!interaction) return true;

    switch (interaction.type) {
      case 'multiple_choice':
        return !selectedChoice.trim();
      case 'reflection_prompt':
        return !userAnswer.trim();
      case 'teach_back':
      case 'self_explanation':
        if (interaction.config?.fields && interaction.config.fields.length > 0) {
          return !interaction.config.fields.every(field => fieldValues[field.id]?.trim());
        }
        return !userAnswer.trim();
      case 'ordering_interaction':
        return selectedOrder.length === 0;
      case 'matching_interaction':
        const concepts = Object.keys(interaction.pairs);
        return !concepts.every(concept => selectedPairs[concept]);
      default:
        return !userAnswer.trim();
    }
  };

  // Check if this lesson should show interactions based on context
  const shouldShowInteraction = () => {
    if (!lessonData.primary_interaction) return false;
    
    const context = lessonData.context;
    const interactionType = lessonData.primary_interaction.type;
    
    // Driving lessons have no interactions
    if (context === 'driving') return false;
    
    // Workout lessons only allow quick tap interactions
    if (context === 'workout') {
      return ['multiple_choice', 'ordering_interaction', 'matching_interaction'].includes(interactionType);
    }
    
    // Home lessons allow all interactions
    return true;
  };

  if (!shouldShowInteraction()) {
    return (
      <div className="learning-question">
        <div className="question-content">
          <p className="question-prompt">
            You've completed the audio portion of this lesson. Feel free to navigate back when you're ready.
          </p>
        </div>
      </div>
    );
  }

  const interaction = lessonData.primary_interaction!;
  const interactionType = interaction.type;
  const instructions = interaction.instructions || getDefaultInstructions(interactionType);

  function getDefaultInstructions(type: string): string {
    switch (type) {
      case 'multiple_choice': return 'Pick the single best answer.';
      case 'reflection_prompt': return 'Take a moment to reflect on this question.';
      case 'teach_back': return 'Explain what you learned in your own words.';
      case 'self_explanation': return 'Break down your understanding step by step.';
      case 'ordering_interaction': return 'Arrange these items in the correct order.';
      case 'matching_interaction': return 'Match each concept with its corresponding example.';
      default: return 'Complete this learning activity.';
    }
  }

  return (
    <div className="learning-question">
      <div className="question-header">
        <h3>{getInteractionIcon(interactionType)} {getInteractionHeader(interactionType)}</h3>
        <p className="question-instructions">{instructions}</p>
      </div>

      <div className="question-content">
        <p className="question-prompt">{interaction.prompt}</p>

        <div className="answer-section">
          {renderInteractionInput()}

          <div className="question-footer">
            <div className="left-footer">
              {interactionType === 'reflection_prompt' && 'min_words' in interaction && interaction.min_words && interaction.min_words > 0 && (
                <span className="word-count">
                  Words: {userAnswer.split(/\s+/).filter(w => w.length > 0).length} / {interaction.min_words} minimum
                </span>
              )}
              {speechSupported && isRecording && (
                <span className="recording-indicator">Recording...</span>
              )}
              {speechSupported && !isRecording && userAnswer && (
                <span className="speech-tip">
                  <Lightbulb size={16} className="inline-icon-small" /> Click microphone to add more
                </span>
              )}
            </div>

            <button className="submit-answer-btn" onClick={handleAnswerSubmit} disabled={getSubmitDisabled()}>
              {isEvaluating ? 'Evaluating...' : (isAnswerSubmitted ? 'Submitted ✓' : 'Submit Answer')}
            </button>
          </div>
        </div>
      </div>

      {isAnswerSubmitted && aiFeedback && (
        <div className="ai-feedback-section">
          <div className="feedback-header">
            <h4><Bot size={20} className="inline-icon-small" /> AI Feedback</h4>
            {aiFeedback.evaluation_timestamp && (
              <div className="feedback-metadata">
                <span className="evaluation-time">
                  Evaluated {new Date(aiFeedback.evaluation_timestamp).toLocaleString()}
                </span>
                {aiFeedback.model_used && (
                  <span className="model-info">via {aiFeedback.model_used}</span>
                )}
              </div>
            )}
          </div>
          <div className="feedback-content">
            <p>{aiFeedback.feedback}</p>
          </div>

          <div className="lesson-completion-section">
            <p className="completion-message">
              Great work! You've completed the learning activity and received your feedback.
            </p>
            <button className="complete-lesson-btn" onClick={onLessonComplete}>
              Complete Lesson & Return to Dashboard
            </button>
          </div>
        </div>
      )}

      {evaluationError && (
        <div className="evaluation-error">
          <p><XCircle size={16} className="inline-icon-small" /> Error evaluating answer: {evaluationError}</p>
          <button className="retry-btn" onClick={handleAnswerSubmit} disabled={isEvaluating}>
            Retry Evaluation
          </button>
        </div>
      )}

      {isEvaluating && (
        <div className="evaluation-loading">
          <div className="loading-spinner small"></div>
          <p>Getting AI feedback on your answer...</p>
        </div>
      )}
    </div>
  );
};
