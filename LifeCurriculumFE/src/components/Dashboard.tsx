import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Check, RotateCcw, Play } from 'lucide-react';
import { useLessonProgress } from "../hooks/useLessonProgress";
import "../styles/Dashboard.css";
import "../styles/LandingPage.css"; // Keep for layout compatibility

interface ProgramData {
  id: string;
  title: string;
  description: string;
  outline?: Array<{ title: string; description?: string }>;
  prompt?: string;
}

interface DashboardStats {
  percentCompleted: number;
  dayStreak: number;
  totalTimeInvested: number; // in minutes
}

interface DashboardProps {
  programs: ProgramData[];
}

function Dashboard({ programs }: DashboardProps) {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const programsContainerRef = useRef<HTMLDivElement>(null);
  const [stats, setStats] = useState<DashboardStats>({
    percentCompleted: 0,
    dayStreak: 1,
    totalTimeInvested: 0
  });

  const { 
    initializeProgram, 
    isLessonCompleted,
    getProgramProgress,
    getAllProgress,
    resetProgramProgress
  } = useLessonProgress();

  useEffect(() => {
    const initializeProgramsData = async () => {
      try {
        setIsLoading(true);
        
        console.log('[Dashboard] Initializing programs data:', programs);
        
        // Initialize progress for all programs
        for (const program of programs) {
          try {
            await initializeProgram(program.id);
            console.log('[Dashboard] Initialized program:', program.id);
          } catch (err) {
            console.error(`[Dashboard] Failed to initialize program ${program.id}:`, err);
          }
        }
        
        // Calculate stats with all programs
        calculateStatsWithAllPrograms(programs);
        
      } catch (err) {
        console.error('[Dashboard] Failed to initialize programs:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (programs && programs.length > 0) {
      initializeProgramsData();
    } else {
      setIsLoading(false);
    }
  }, [programs]);

  // Handle scroll to update active card indicator
  const handleScroll = useCallback(() => {
    if (!programsContainerRef.current) return;
    
    const container = programsContainerRef.current;
    const cardWidth = container.scrollWidth / displayPrograms.length;
    const scrollLeft = container.scrollLeft;
    const newActiveIndex = Math.round(scrollLeft / cardWidth);
    
    if (newActiveIndex !== activeCardIndex && newActiveIndex >= 0 && newActiveIndex < displayPrograms.length) {
      setActiveCardIndex(newActiveIndex);
    }
  }, [activeCardIndex]);

  // Navigate to specific card
  const scrollToCard = (index: number) => {
    if (!programsContainerRef.current) return;
    
    const container = programsContainerRef.current;
    const cardWidth = container.scrollWidth / displayPrograms.length;
    const scrollLeft = cardWidth * index;
    
    container.scrollTo({
      left: scrollLeft,
      behavior: 'smooth'
    });
    setActiveCardIndex(index);
  };

  const calculateStatsWithAllPrograms = (programs: ProgramData[]) => {
    if (programs.length === 0) return;

    console.log('[Dashboard] Calculating stats for all programs');
    
    let totalLessons = 0;
    let completedLessons = 0;
    let maxStreak = 0;
    let totalTime = 0;

    programs.forEach(program => {
      console.log(`[Dashboard] Processing program ${program.id}:`, program.title);
      
      // Get total lessons from program outline, fallback to 5
      const programLessons = program.outline && program.outline.length > 0 ? program.outline.length : 5;
      totalLessons += programLessons;
      
      // Get progress for this program
      const progress = getProgramProgress(program.id);
      if (progress && progress.completedLessons) {
        const completedCount = progress.completedLessons.length;
        completedLessons += completedCount;
        console.log(`[Dashboard] Found ${completedCount} completed lessons out of ${programLessons} total for program ${program.id}`);
        
        // Calculate streak (consecutive completed lessons starting from day 1)
        let currentStreak = 0;
        for (let i = 1; i <= programLessons; i++) {
          if (progress.completedLessons.includes(i)) {
            currentStreak++;
          } else {
            break;
          }
        }
        maxStreak = Math.max(maxStreak, currentStreak);
        
        // Estimate time invested (5 minutes per completed lesson)
        totalTime += completedCount * 5;
      } else {
        console.log(`[Dashboard] No progress data found for program ${program.id}`);
      }
    });

    // Ensure minimum day streak of 1 if user has any progress
    const dayStreak = Math.max(maxStreak, completedLessons > 0 ? 1 : 0);
    const percentCompleted = totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;

    console.log(`[Dashboard] Final stats calculation:`, {
      totalLessons,
      completedLessons,
      percentCompleted: `${completedLessons}/${totalLessons} = ${percentCompleted}%`,
      dayStreak,
      totalTime
    });

    setStats({
      percentCompleted,
      dayStreak,
      totalTimeInvested: totalTime
    });
  };

  const sortPrograms = (programs: ProgramData[]): ProgramData[] => {
    return [...programs].sort((a, b) => {
      const progressA = getProgramProgress(a.id);
      const progressB = getProgramProgress(b.id);
      
      const completedA = progressA?.completedLessons?.length || 0;
      const completedB = progressB?.completedLessons?.length || 0;
      
      const totalA = a.outline?.length || 5;
      const totalB = b.outline?.length || 5;
      
      const isCompleteA = completedA === totalA;
      const isCompleteB = completedB === totalB;
      
      const hasProgressA = completedA > 0;
      const hasProgressB = completedB > 0;
      
      // In Progress programs first (has progress but not complete)
      if ((hasProgressA && !isCompleteA) && !(hasProgressB && !isCompleteB)) {
        return -1;
      }
      if (!(hasProgressA && !isCompleteA) && (hasProgressB && !isCompleteB)) {
        return 1;
      }
      
      // Among in-progress programs, sort by most recently updated (most progress)
      if ((hasProgressA && !isCompleteA) && (hasProgressB && !isCompleteB)) {
        return completedB - completedA; // More completed lessons = more recent
      }
      
      // Otherwise maintain original order
      return 0;
    });
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  };

  // Individual Program Card Component
  const ProgramCard = ({ 
    program, 
    index
  }: { 
    program: ProgramData; 
    index: number;
  }) => {
    const [animationStarted, setAnimationStarted] = useState(false);
    const [selectedRating, setSelectedRating] = useState<number | null>(null);
    const [showFeedbackForm, setShowFeedbackForm] = useState(false);
    const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

    useEffect(() => {
      // Check if user has seen the animation before
      const hasSeenAnimation = localStorage.getItem('dashboard-animation-seen');
      
      if (!hasSeenAnimation) {
        // First time visiting - show animation and mark as seen
        const timer = setTimeout(() => {
          setAnimationStarted(true);
          localStorage.setItem('dashboard-animation-seen', 'true');
        }, 300);
        return () => clearTimeout(timer);
      }
      // If they've seen it before, don't animate - just show static timeline
    }, []);

    const progress = getProgramProgress(program.id);
    const nextLesson = progress?.currentLesson || 1;
    const completedLessons = progress?.completedLessons?.length || 0;
    const totalDays = program.outline && program.outline.length > 0 ? program.outline.length : 5;
    const isCompleted = completedLessons === totalDays;
    const percentCompleted = totalDays > 0 ? Math.round((completedLessons / totalDays) * 100) : 0;
    
    // Calculate streak for this program
    let dayStreak = 0;
    if (progress && progress.completedLessons) {
      for (let i = 1; i <= totalDays; i++) {
        if (progress.completedLessons.includes(i)) {
          dayStreak++;
        } else {
          break;
        }
      }
    }
    dayStreak = Math.max(dayStreak, completedLessons > 0 ? 1 : 0);
    
    const timeInvested = completedLessons * 5; // 5 minutes per lesson

    const programStats = [
      { value: `${percentCompleted}%`, label: "Completed" },
      { value: `${dayStreak}`, label: "Day Streak" },
      { value: formatTime(timeInvested), label: "Time Invested" }
    ];

    const handleContinueProgram = () => {
      navigate(`/programs/${program.id}/lesson/${nextLesson}`);
    };

    const handleRestartProgram = () => {
      const confirmed = window.confirm('Are you sure you want to restart this program from Day 1? This will reset all your progress.');
      if (confirmed) {
        resetProgramProgress(program.id);
        window.location.reload();
      }
    };

    const handleRatingChange = (rating: number) => {
      setSelectedRating(rating);
      setFeedbackSubmitted(true);
      submitFeedback(program.id, rating);
    };

    const submitFeedback = (programId: string, rating: number) => {
      console.log(`Feedback submitted for program ${programId}: ${rating}/5`);
    };

    const handleShowFeedback = () => {
      setShowFeedbackForm(true);
    };

    // Timeline Display
    const timelineSteps = Array.from({ length: totalDays }, (_, index) => ({
      number: index + 1,
      label: `Day ${index + 1}`
    }));

    // Rating Component
    const RatingControl = () => {
      const ratingLabels = ['Not Helpful', 'Somewhat', 'Neutral', 'Helpful', 'Very Helpful'];
      
      return (
        <div className="rating-control">
          {ratingLabels.map((label, index) => (
            <button
              key={index}
              onClick={() => handleRatingChange(index + 1)}
              className={`rating-button ${selectedRating === index + 1 ? 'selected' : ''}`}
              onMouseEnter={(e) => {
                if (selectedRating !== index + 1) {
                  e.currentTarget.style.borderColor = 'var(--accent-pop)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedRating !== index + 1) {
                  e.currentTarget.style.borderColor = 'var(--border-tertiary)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <div className="rating-circle">
                {index + 1}
              </div>
              <span>{label}</span>
            </button>
          ))}
        </div>
      );
    };

    return (
      <section className="program-card program-section horizontal">
        <div className="program-header">
          <div className="program-info">
            <h2>{program.title}</h2>
            <p>{program.description || "5 minutes daily • AI-powered conversations • Fits your schedule"}</p>
          </div>

          <div className="stats-display">
            {programStats.map((stat, index) => (
              <div key={index}>
                <div>{stat.value}</div>
                <div>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={`timeline-display ${animationStarted ? 'animated' : ''}`}>
          {timelineSteps.map((step: any) => {
            const isStepCompleted = isLessonCompleted(program.id, step.number);
            const isCurrent = step.number === nextLesson && !isStepCompleted;
            const isInactive = step.number > nextLesson && !isStepCompleted;

            return (
              <div key={step.number} className={`timeline-step ${isStepCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isInactive ? 'inactive' : ''}`}>
                <div className="timeline-circle">
                  {isStepCompleted ? <Check size={16} /> : step.number}
                </div>
                <div className="timeline-label">{step.label}</div>
              </div>
            );
          })}
        </div>

        <div className="continue-section">
          {isCompleted ? (
            <div style={{ textAlign: 'center' }} className="completion-content">
              <h3 className="completion-heading">
                🎉 Congratulations! You've completed this program.
              </h3>
              
              <p className="completion-note">
                You can revisit any day at any time.
              </p>

              {!feedbackSubmitted && !showFeedbackForm && (
                <button 
                  type="button" 
                  onClick={handleShowFeedback}
                  className="feedback-button"
                >
                  Give Feedback
                </button>
              )}

              {showFeedbackForm && !feedbackSubmitted && (
                <div className="feedback-form">
                  <RatingControl />
                </div>
              )}

              {feedbackSubmitted && (
                <p className="feedback-thank-you">
                  Thank you for your feedback.
                </p>
              )}
            </div>
          ) : (
            <button className="continue-btn" type="button" onClick={handleContinueProgram}>
              Continue to Day {nextLesson}
            </button>
          )}
        </div>
      </section>
    );
  };

  // Navigation Dots Component
  const NavigationDots = () => {
    if (displayPrograms.length <= 1) return null;
    
    return (
      <div className="programs-navigation">
        {displayPrograms.map((_, index) => (
          <button
            key={index}
            className={`nav-dot ${index === activeCardIndex ? 'active' : ''}`}
            onClick={() => scrollToCard(index)}
            aria-label={`Go to program ${index + 1}`}
          />
        ))}
      </div>
    );
  };

  // Quick Actions Display
  // const QuickActionsDisplay = () => (
  //   <div className="features-display">
  //     <div>
  //       <div>View All Programs</div>
  //       <div>See your complete program collection and switch between them</div>
  //     </div>
  //     <div>
  //       <div>Create New Program</div>
  //       <div>Start a new personalized 5-day growth journey</div>
  //     </div>
  //   </div>
  // );

  if (isLoading) {
    return (
      <div className="landing-page">
        <main className="main-landing-content">
          <div className="dashboard-loading-container horizontal">
            <div className="loading-spinner"></div>
            <p>Loading your dashboard...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!programs || programs.length === 0) {
    return (
      <div className="landing-page">
        <main className="main-landing-content">
          <h1>Welcome!</h1>
          <p>No programs found. Create your first program to get started.</p>
        </main>
      </div>
    );
  }

  // Sort programs and take first 3
  const sortedPrograms = sortPrograms(programs);
  const displayPrograms = sortedPrograms.slice(0, 3);

  return (
    <div className="landing-page">
      <main className="main-landing-content">
        {/* Welcome Section */}
        <h1>Welcome Back!</h1>
        <p>Continue your personalized growth journey</p>

        {/* Programs Section - Horizontal */}
        <div 
          className="programs-container"
          ref={programsContainerRef}
          onScroll={handleScroll}
        >
          {displayPrograms.map((program, index) => (
            <ProgramCard
              key={program.id}
              program={program}
              index={index}
            />
          ))}
        </div>

        {/* Navigation Dots */}
        <NavigationDots />

        {/* Bottom Section */}
        {/* <div className="features-card">
          <h3>Quick Actions</h3>
          <QuickActionsDisplay />
        </div> */}
      </main>
    </div>
  );
}

export default Dashboard;