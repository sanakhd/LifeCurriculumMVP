import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Home, Car, Dumbbell } from 'lucide-react';
import "../styles/MyPrograms.css";
import { useListAllPrograms, useGetProgramById, useGetSingleLesson } from "../hooks/useApi";
import { useLessonProgress } from "../hooks/useLessonProgress";

interface Program {
  id: string;
  title: string;
  description: string;
  context?: 'home' | 'driving' | 'workout';
}

interface ProgramViewState {
  isVisible: boolean;
  programId: string | null;
  programTitle: string | null;
}

function MyPrograms() {
  const navigate = useNavigate();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progressLoading, setProgressLoading] = useState(false);
  const [progressLoadedPrograms, setProgressLoadedPrograms] = useState<Set<string>>(new Set());
  const [programViewState, setProgramViewState] = useState<ProgramViewState>({
    isVisible: false,
    programId: null,
    programTitle: null
  });
  const [programData, setProgramData] = useState<any>(null);
  const [programLoading, setProgramLoading] = useState(false);
  const [programError, setProgramError] = useState<string | null>(null);

  const listPrograms = useListAllPrograms();
  const getProgram = useGetProgramById();
  const getSingleLesson = useGetSingleLesson();
  const { 
    initializeProgram, 
    isLessonAvailable, 
    isLessonCompleted,
    refreshProgramProgress,
    getProgramProgress
  } = useLessonProgress();

  const getContextInfo = (context?: string) => {
    switch (context) {
      case 'home':
        return { icon: Home, label: 'Home Learning', color: 'context-home' };
      case 'driving':
        return { icon: Car, label: 'Driving Safe', color: 'context-driving' };
      case 'workout':
        return { icon: Dumbbell, label: 'Workout Mode', color: 'context-workout' };
      default:
        return { icon: Home, label: 'Home Learning', color: 'context-home' };
    }
  };

  useEffect(() => {
    const fetchPrograms = async () => {
      console.log('[MyPrograms] Starting to fetch programs list');
      
      try {
        setIsLoading(true);
        setError(null);

        // First, get the list of all programs
        console.log('[MyPrograms] Fetching programs list from API');
        const programsList = await listPrograms.execute(undefined);
        console.log('[MyPrograms] Programs list response:', programsList);
        
        if (!programsList || !programsList.items || programsList.items.length === 0) {
          console.log('[MyPrograms] No programs found in response');
          setPrograms([]);
          setIsLoading(false);
          return;
        }

        console.log(`[MyPrograms] Found ${programsList.items.length} programs, fetching details...`);

        // Then, fetch details for each program
        const programDetails: Program[] = [];
        
        for (const programItem of programsList.items) {
          try {
            // Extract program_id from the program item
            const programId = programItem.program_id || programItem.id;
            console.log(`[MyPrograms] Processing program with ID: ${programId}`);
            
            if (programId) {
              const programDetail = await getProgram.execute(programId);
              console.log(`[MyPrograms] Program ${programId} details:`, programDetail);
              
              if (programDetail && programDetail.title) {
                const program = {
                  id: programId,
                  title: programDetail.title,
                  description: programDetail.description || 'No description available',
                  context: programDetail.context || 'home'
                };
                programDetails.push(program);
                console.log(`[MyPrograms] Added program ${programId} to list: ${program.title}`);
              } else {
                console.warn(`[MyPrograms] Program ${programId} missing title, skipping`);
              }
            } else {
              console.warn('[MyPrograms] Program item missing ID, skipping:', programItem);
            }
          } catch (programError) {
            console.error(`[MyPrograms] Failed to fetch program ${programItem.program_id || programItem.id}:`, programError);
          }
        }
        
        console.log(`[MyPrograms] Successfully loaded ${programDetails.length} programs`);
        setPrograms(programDetails);
        
        // Initialize progress tracking for all programs to check button states
        console.log(`[MyPrograms] Initializing progress tracking for all programs`);
        setProgressLoading(true);
        const loadedPrograms = new Set<string>();
        
        for (const program of programDetails) {
          try {
            await initializeProgram(program.id);
            await refreshProgramProgress(program.id);
            loadedPrograms.add(program.id);
            console.log(`[MyPrograms] Progress initialized for program ${program.id}`);
            
            // Check lesson completion status for debugging
            const day1Completed = isLessonCompleted(program.id, 1);
            console.log(`[MyPrograms] Program ${program.id} day 1 completed:`, day1Completed);
          } catch (err) {
            console.error(`[MyPrograms] Failed to initialize progress for program ${program.id}:`, err);
          }
        }
        
        setProgressLoadedPrograms(loadedPrograms);
        setProgressLoading(false);
        console.log(`[MyPrograms] Progress tracking initialization complete`);
        
        // Force a re-render by updating programs state again
        setPrograms([...programDetails]);
      } catch (err) {
        console.error('[MyPrograms] Failed to fetch programs:', err);
        setError('Failed to load programs. Please make sure the backend is running on localhost:8000.');
      } finally {
        setIsLoading(false);
        console.log('[MyPrograms] Finished loading programs');
      }
    };
    
    fetchPrograms();
  }, []);

  const handleProgramClick = (programId: string) => {
    // Handle program selection - this would navigate to program details
    console.log(`Selected program: ${programId}`);
  };

  const handleStartProgram = async (e: React.MouseEvent, programId: string, programTitle: string) => {
    e.stopPropagation(); // Prevent card click event
    console.log(`[MyPrograms] Starting program ${programId}: ${programTitle}`);
    
    setProgramViewState({
      isVisible: true,
      programId,
      programTitle
    });

    console.log(`[MyPrograms] Initializing program progress for ${programId}`);
    // Initialize program progress tracking and refresh from API
    await initializeProgram(programId);

    // Fetch full program details (including outline)
    console.log(`[MyPrograms] Fetching full program details for ${programId}`);
    setProgramLoading(true);
    setProgramError(null);
    setProgramData(null);

    try {
      const program = await getProgram.execute(programId);
      console.log(`[MyPrograms] Program details loaded for ${programId}:`, program);
      setProgramData(program);
      
      // Refresh progress after getting program data
      console.log(`[MyPrograms] Refreshing progress data for ${programId}`);
      await refreshProgramProgress(programId);
      console.log(`[MyPrograms] Program view setup complete for ${programId}`);
    } catch (err) {
      console.error(`[MyPrograms] Failed to fetch program ${programId}:`, err);
      setProgramError('Failed to load program details. Please try again.');
    } finally {
      setProgramLoading(false);
    }
  };

  const closeProgramView = () => {
    console.log(`[MyPrograms] Closing program view for program ${programViewState.programId}`);
    setProgramViewState({
      isVisible: false,
      programId: null,
      programTitle: null
    });
    setProgramData(null);
    setProgramError(null);
  };

  const handleDayClick = (dayNumber: number) => {
    console.log(`[MyPrograms] Starting lesson for program ${programViewState.programId}, day ${dayNumber}`);
    if (programViewState.programId) {
      console.log(`[MyPrograms] Navigating to /programs/${programViewState.programId}/lesson/${dayNumber}`);
      navigate(`/programs/${programViewState.programId}/lesson/${dayNumber}`);
    } else {
      console.error('[MyPrograms] No program ID available for lesson start');
    }
  };

  return (
    <div className="programs-page">
      <main className="main-programs-content">
        {/* Header Section */}
        <div className="programs-header">
          <div className="header-content">
            <div className="header-text">
              <h1>My <span className="text-pop">Programs</span></h1>
              <p>Discover personalized growth programs designed just for you</p>
            </div>
            {!isLoading && !error && programs.length > 0 && (
              <button className="create-new-program-btn" onClick={() => navigate("/create-program")}>
                Create New Program
              </button>
            )}
          </div>
        </div>

        {/* Programs Grid Section */}
        <section className="programs-section">
          {isLoading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading your programs...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <h3>Unable to load programs</h3>
              <p>{error}</p>
              <button 
                className="retry-btn"
                onClick={() => window.location.reload()}
              >
                Try Again
              </button>
            </div>
          ) : (
            <>
              <div className="programs-grid">
                {programs.map((program) => (
                  <div 
                    key={program.id} 
                    className="program-card"
                    onClick={() => handleProgramClick(program.id)}
                  >
                    <div className="program-card-inner">
                      {program.context && (() => {
                        const contextInfo = getContextInfo(program.context);
                        const ContextIcon = contextInfo.icon;
                        return (
                          <div className={`program-context-icon ${contextInfo.color}`} title={contextInfo.label}>
                            <ContextIcon size={20} />
                          </div>
                        );
                      })()}
                      <h3>{program.title}</h3>
                      <p>{program.description}</p>
                      <div className="program-card-footer">
                        <span className="program-duration">5 days • 5 min daily</span>
                        <button 
                          className="start-program-btn"
                          onClick={(e) => handleStartProgram(e, program.id, program.title)}
                        >
                          {progressLoadedPrograms.has(program.id) && isLessonCompleted(program.id, 1) ? 'Continue' : 'Start Program'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {programs.length === 0 && (
                <div className="empty-state">
                  <h3>No programs yet</h3>
                  <p>Create your first personalized growth program to get started</p>
                  <button className="create-program-btn" onClick={() => navigate("/create-program")}>
                    Create New Program
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      </main>

        {/* Program Outline Modal */}
        {programViewState.isVisible && (
          <div className="modal-overlay" onClick={closeProgramView}>
            <div className="modal-content program-outline-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{programViewState.programTitle}</h2>
                <button className="modal-close-btn" onClick={closeProgramView}>
                  ×
                </button>
              </div>
              
              <div className="modal-body">
                {programLoading ? (
                  <div className="program-outline-loading">
                    <div className="loading-spinner"></div>
                    <p>Loading program details...</p>
                  </div>
                ) : programError ? (
                  <div className="program-outline-error">
                    <h3>Error loading program</h3>
                    <p>{programError}</p>
                    <button 
                      className="retry-program-btn"
                      onClick={() => programViewState.programId && handleStartProgram(
                        {} as React.MouseEvent, 
                        programViewState.programId, 
                        programViewState.programTitle || ''
                      )}
                    >
                      Try Again
                    </button>
                  </div>
                ) : programData && programData.outline ? (
                  <div className="program-days-grid">
                    {programData.outline.map((day: any, index: number) => {
                      const dayNumber = index + 1;
                      
                      const isCompleted = programViewState.programId ? isLessonCompleted(programViewState.programId, dayNumber) : false;
                      const isAvailable = programViewState.programId ? isLessonAvailable(programViewState.programId, dayNumber) : dayNumber === 1;
                      
                      let statusClass = '';
                      let statusText = '';
                      
                      if (isCompleted) {
                        statusClass = 'completed';
                        statusText = 'Completed';
                      } else if (isAvailable) {
                        statusClass = 'available';
                        statusText = 'Available';
                      } else {
                        statusClass = 'locked';
                        statusText = 'Locked';
                      }
                      
                      const handleDayCardClick = () => {
                        if (isAvailable) {
                          handleDayClick(dayNumber);
                        }
                      };

                      return (
                        <div 
                          key={index} 
                          className={`program-day-card ${statusClass} ${isAvailable ? 'clickable' : ''}`}
                          onClick={handleDayCardClick}
                          role={isAvailable ? 'button' : undefined}
                          tabIndex={isAvailable ? 0 : undefined}
                          onKeyDown={isAvailable ? (e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleDayCardClick();
                            }
                          } : undefined}
                        >
                          <div className="program-day-header">
                            <div className="day-number-badge">
                              <span className="day-number">Day {dayNumber}</span>
                            </div>
                            <div className="day-status">
                              <span className="day-status-text">{statusText}</span>
                            </div>
                          </div>
                          
                          <div className="program-day-body">
                            <h3 className="day-title">{day.title || day.day_title || `Day ${dayNumber}`}</h3>
                            {day.description && (
                              <p className="day-description">{day.description}</p>
                            )}
                            {((day.learning_objectives && day.learning_objectives.length > 0) || 
                              (day.key_concepts && day.key_concepts.length > 0)) && (
                              <div className="day-objectives">
                                <h4>What you'll learn:</h4>
                                <ul>
                                  {day.learning_objectives && day.learning_objectives.length > 0 ? (
                                    <>
                                      {day.learning_objectives.slice(0, 3).map((objective: string, objIndex: number) => (
                                        <li key={objIndex}>{objective}</li>
                                      ))}
                                      {day.learning_objectives.length > 3 && (
                                        <li className="objectives-more">+{day.learning_objectives.length - 3} more</li>
                                      )}
                                    </>
                                  ) : day.key_concepts && day.key_concepts.length > 0 ? (
                                    <>
                                      {day.key_concepts.slice(0, 3).map((concept: string, objIndex: number) => (
                                        <li key={objIndex}>{concept}</li>
                                      ))}
                                      {day.key_concepts.length > 3 && (
                                        <li className="concepts-more">+{day.key_concepts.length - 3} more</li>
                                      )}
                                    </>
                                  ) : null}
                                </ul>
                              </div>
                            )}
                          </div>
                          
                          <div className="program-day-footer">
                            {!isAvailable && (
                              <p className="day-lock-message">Complete previous lessons to unlock</p>
                            )}
                            {isAvailable && (
                              <span className="day-action-hint">Click to start this lesson</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}
    </div>
  );
}

export default MyPrograms;
