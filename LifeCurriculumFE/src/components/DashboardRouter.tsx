import { useState, useEffect } from 'react';
import { useListAllPrograms, useGetProgramById } from '../hooks/useApi';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';

interface ProgramData {
  id: string;
  title: string;
  description: string;
  outline?: Array<{ title: string; description?: string }>;
  prompt?: string;
}

function DashboardRouter() {
  const [programs, setPrograms] = useState<ProgramData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const listPrograms = useListAllPrograms();
  const getProgram = useGetProgramById();

  useEffect(() => {
    const fetchUserPrograms = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        console.log('[DashboardRouter] Checking user programs...');
        
        // Fetch user's programs
        const programsList = await listPrograms.execute(undefined);
        
        console.log('[DashboardRouter] Programs response:', programsList);
        
        // Check if user has any programs
        const userHasPrograms = programsList && 
                               programsList.items && 
                               programsList.items.length > 0;
        
        console.log('[DashboardRouter] User has programs:', userHasPrograms);
        
        if (userHasPrograms) {
          // Get all program details
          const allPrograms: ProgramData[] = [];
          
          for (const programItem of programsList.items) {
            const programId = programItem.program_id || programItem.id;
            
            if (programId) {
              try {
                console.log('[DashboardRouter] Fetching details for program:', programId);
                const programDetail = await getProgram.execute(programId);
                
                if (programDetail && programDetail.title) {
                  const program: ProgramData = {
                    id: programId,
                    title: programDetail.title,
                    description: programDetail.description || '',
                    outline: programDetail.outline || [],
                    prompt: programDetail.prompt || ''
                  };
                  
                  allPrograms.push(program);
                  console.log('[DashboardRouter] Program details loaded:', program);
                }
              } catch (programError) {
                console.warn('[DashboardRouter] Failed to fetch program details for:', programId, programError);
              }
            }
          }
          
          if (allPrograms.length > 0) {
            setPrograms(allPrograms);
            console.log('[DashboardRouter] All programs loaded:', allPrograms);
          } else {
            console.warn('[DashboardRouter] No valid programs found, showing landing page');
            setPrograms([]);
          }
        } else {
          console.log('[DashboardRouter] No programs found, showing landing page');
          setPrograms([]);
        }
        
      } catch (err) {
        console.error('[DashboardRouter] Failed to fetch user programs:', err);
        // On error, show landing page (safer default)
        setPrograms([]);
        setError('Failed to load program data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserPrograms();
  }, []);

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '400px',
        textAlign: 'center'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '1rem'
        }}></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  if (error) {
    console.log('[DashboardRouter] Error occurred, showing landing page as fallback');
  }

  // Show Dashboard for users with programs, LandingPage for new users
  if (programs.length > 0) {
    console.log('[DashboardRouter] Rendering Dashboard for returning user with programs:', programs.length);
    return <Dashboard programs={programs} />;
  } else {
    console.log('[DashboardRouter] Rendering LandingPage for new user');
    return <LandingPage />;
  }
}

export default DashboardRouter;
