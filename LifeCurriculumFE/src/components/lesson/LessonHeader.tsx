import React from 'react';
import { Home, Car, Dumbbell } from 'lucide-react';

interface LessonHeaderProps {
  title: string;
  context?: 'home' | 'driving' | 'workout';
  onBackClick: () => void;
}

const getContextInfo = (context?: string) => {
  switch (context) {
    case 'home':
      return { icon: Home, label: 'Home Learning', color: 'context-home' };
    case 'driving':
      return { icon: Car, label: 'Driving Safe', color: 'context-driving' };
    case 'workout':
      return { icon: Dumbbell, label: 'Workout Mode', color: 'context-workout' };
    default:
      return { icon: Home, label: 'General', color: 'context-default' };
  }
};

export const LessonHeader: React.FC<LessonHeaderProps> = ({ title, context, onBackClick }) => {
  const contextInfo = getContextInfo(context);
  const ContextIcon = contextInfo.icon;

  return (
    <div className="lesson-header">
      <button onClick={onBackClick} className="back-button">
        ← Back to Programs
      </button>
      <div className="lesson-title-section">
        <h1>{title}</h1>
        {context && (
          <div className={`context-badge ${contextInfo.color}`}>
            <ContextIcon size={16} />
            <span>{contextInfo.label}</span>
          </div>
        )}
      </div>
    </div>
  );
};
