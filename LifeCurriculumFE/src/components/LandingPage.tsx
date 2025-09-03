import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import "../styles/LandingPage.css"

const PROGRAM_STATS = [
  { value: "5", label: "Days" },
  { value: "5", label: "Minutes Daily" },
  { value: "∞", label: "Potential" }
]

const TIMELINE_STEPS = [
  { number: 1, label: "Set Your Goal" },
  { number: 2, label: "Learn & Practice" },
  { number: 3, label: "Build Momentum" },
  { number: 4, label: "Apply Skills" },
  { number: 5, label: "Make it Stick" },
]


const StatsDisplay = () => (
  <div className="stats-display">
    {PROGRAM_STATS.map((stat, index) => (
      <div key={index}>
        <div>{stat.value}</div>
        <div>{stat.label}</div>
      </div>
    ))}
  </div>
)

const TimelineDisplay = ({ isFirstTime = true }) => {
  const [animationStarted, setAnimationStarted] = useState(false);

  useEffect(() => {
    if (isFirstTime) {
      // Small delay before starting animation to ensure component is mounted
      const timer = setTimeout(() => {
        setAnimationStarted(true);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isFirstTime]);

  return (
    <div className={`timeline-display ${isFirstTime && animationStarted ? 'animated' : ''}`}>
      {TIMELINE_STEPS.map((step) => (
        <div key={step.number}>
          <div>{step.number}</div>
          <div>{step.label}</div>
        </div>
      ))}
    </div>
  )
}


function LandingPage() {
  const navigate = useNavigate();
  const [isFirstTimeUser, setIsFirstTimeUser] = useState(true);

  const handleCreateProgram = () => {
    navigate("/create-program");
  };

  return (
    <div className="landing-page">
      <main className="main-landing-content">
        {/* Welcome Section */}
        <h1>Ready to level up?</h1>
        <p>Create your personalized 5-day growth program</p>

        {/* Program Section */}
        <section className="program-section">
          <div className="program-header">
            <div className="program-info">
              <h2>Your Growth <span className="text-pop">Journey</span> Starts Here</h2>
              <p>5 minutes daily • AI-powered conversations • Fits your schedule</p>
            </div>
            <StatsDisplay />
          </div>
          <TimelineDisplay isFirstTime={isFirstTimeUser} />
          <div className="continue-section">
            <button className="continue-btn" type="button" onClick={handleCreateProgram}>
              Create Your First Program
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default LandingPage;
