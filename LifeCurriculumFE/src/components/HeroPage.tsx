import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Headphones, Brain, Zap, ArrowRight, Play, Volume2, Pause, SkipForward, Mic, MessageCircle, Sparkles, Users, ChevronDown, Star, Quote, TrendingUp, Shield } from "lucide-react";
import "../styles/HeroPage.css";

const HeroPage: React.FC = () => {
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentMessage, setCurrentMessage] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);
  const [cursor, setCursor] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const conversationMessages = [
    { speaker: "Host A", text: "So Sarah, yesterday we talked about power poses...", color: "#ff7a59" },
    { speaker: "Host B", text: "Right! Studies show even 2 minutes can boost confidence by 23%", color: "#9eab97" },
    { speaker: "Host A", text: "That's fascinating! What did you notice when you tried it?", color: "#ff7a59" },
    { speaker: "Host B", text: "I felt more grounded before my presentation. Small changes, big impact!", color: "#9eab97" }
  ];

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentMessage((prev) => (prev + 1) % conversationMessages.length);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isPlaying]);

  useEffect(() => {
    const move = (e: MouseEvent) => setCursor({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", move, { passive: true });
    return () => window.removeEventListener("mousemove", move);
  }, []);


  const handleGetStarted = () => {
    navigate("/welcome");
  };

  const handleWatchDemo = () => {
    console.log("Show demo video");
  };

  const scrollTo = (selector: string) => {
    document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="enhanced-hero-page">
      <div
        className="cursor-dot"
        style={{ transform: `translate3d(${cursor.x}px, ${cursor.y}px, 0)` }}
        aria-hidden
      />
      <div
        className="cursor-ring"
        style={{ transform: `translate3d(${cursor.x}px, ${cursor.y}px, 0)` }}
        aria-hidden
      />
      {/* Floating Background Elements */}
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      {/* Hero Section */}
      <div className="hero-container" ref={heroRef}>
        <div
          className="hero-content"
          style={{ transform: `translateY(${scrollY * 0.1}px)` }}
        >
          <h1>
            Personal Growth that <br />
            <span className="gradient-text">Actually Fits Your Life</span>
          </h1>
          <p>
            AI-powered 5-minute conversations that help you build better habits,
            boost confidence, and create lasting change—without the overwhelm.
          </p>

          <div className="cta-container">
            <button className="cta-primary" onClick={handleGetStarted}>
              Start Your Journey
              <ArrowRight size={20} />
            </button>
            <button className="cta-secondary" onClick={handleWatchDemo}>
              <Play size={18} />
              See How It Works
            </button>
          </div>

          {/* NEW: Benefit pills (shopify-ish quick value props) */}
          <div className="benefit-pills">
            <div className="pill"><Sparkles size={16} /> AI-Personalized</div>
            <div className="pill"><Headphones size={16} /> Podcast-Style</div>
            <div className="pill"><Brain size={16} /> Context-Aware</div>
            {/* <div className="pill"><Shield size={16} /> Private by design</div> */}
          </div>

          {/* Moved here: Scroll affordance right under hero */}
          {/* <button className="scroll-affordance" onClick={() => scrollTo("#story-one")}>
            <span>Scroll to explore</span>
            <ChevronDown size={18} />
          </button> */}
        </div>

        {/* Phone Visual stays the same */}
        <div
          className="hero-visual"
          style={{
            transform: `translateY(${scrollY * -0.05}px) rotateY(${scrollY * 0.02}deg)`
          }}
        >
          <div className="phone-3d-container">
            <div className="phone-mockup">
              <div className="phone-notch"></div>
              <div className="phone-screen">
                <div className="app-demo">
                  <div className="demo-header">
                    <div className="demo-avatar">SC</div>
                    <div className="demo-info">
                      <h3>Building Confidence</h3>
                      <p>Day 3 of 5 • 5 min conversation</p>
                    </div>
                    <button
                      className="play-button"
                      onClick={() => setIsPlaying(!isPlaying)}
                    >
                      {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                    </button>
                  </div>

                  <div className="waveform-container">
                    <div className="waveform">
                      {Array.from({ length: 20 }).map((_, i) => (
                        <div
                          key={i}
                          className={`wave-bar ${isPlaying && i % 3 === currentMessage % 3 ? 'active' : ''}`}
                          style={{
                            height: `${Math.random() * 30 + 10}px`,
                            animationDelay: `${i * 0.1}s`
                          }}
                        />
                      ))}
                    </div>
                    <div className="waveform-controls">
                      <span className="time-display">2:34 / 5:00</span>
                      <div className="audio-controls">
                        <Volume2 size={16} />
                        <SkipForward size={16} />
                      </div>
                    </div>
                  </div>

                  <div className="conversation-display">
                    {isPlaying ? (
                      <div
                        key={currentMessage}
                        className={`message ${conversationMessages[currentMessage].speaker === 'Host A' ? 'host-a' : 'host-b'}`}
                      >
                        <div
                          className="speaker"
                          style={{ color: conversationMessages[currentMessage].color }}
                        >
                          {conversationMessages[currentMessage].speaker}
                        </div>
                        <div className="text">
                          {conversationMessages[currentMessage].text}
                        </div>
                      </div>
                    ) : (
                      <div className="conversation-placeholder">
                        <MessageCircle size={32} />
                        <span>Tap play to hear the conversation</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div> {/* /hero-container */}

      {/* NEW: Metric ticker (movement + proof) */}
      <div className="metric-ticker">
        <div className="ticker-track">
          <div className="tick"><Star size={16} /> 4.9 average session rating</div>
          <div className="tick"><TrendingUp size={16} /> +23% reported confidence</div>
          <div className="tick"><Users size={16} /> 120k+ focused minutes</div>
          <div className="tick"><Mic size={16} /> 5-minute daily conversations</div>
        </div>
        <div className="ticker-track clone">
          <div className="tick"><Star size={16} /> 4.9 average session rating</div>
          <div className="tick"><TrendingUp size={16} /> +23% reported confidence</div>
          <div className="tick"><Users size={16} /> 120k+ focused minutes</div>
          <div className="tick"><Mic size={16} /> 5-minute daily conversations</div>
        </div>
      </div>

      {/* STORY ONE: Vignette row (no cards) */}
      <section id="story-one" className="vignette">
        <div className="vignette-media gradient-box"></div>
        <div className="vignette-copy">
          <h2>Learn the Things that Make You, <span className="gradient-text">You</span></h2>
          <p>Whether it's confidence, wellness, or picking up a new interest, lessons feel personal, enjoyable, and part of who you are.</p>
          <ul className="point-list">
            <li><Headphones size={18} /> Conversational—not lectures</li>
            <li><Brain size={18} /> Tailored to your goal & context</li>
            <li><Zap size={18} /> Designed for 5-minute momentum</li>
          </ul>
        </div>
      </section>

      {/* STORY TWO: Alternate layout */}
      <section className="vignette reverse">
        <div className="vignette-media rings-box"></div>
        <div className="vignette-copy">
          <h3>Built for Real Life</h3>
          <p>At home, commuting, or at the gym—content adapts to your environment so progress never feels forced.</p>
          <div className="capsule-rail">
            <span className="capsule">Driving mode</span>
            <span className="capsule">Hands-free prompts</span>
            <span className="capsule">Action check-ins</span>
          </div>
        </div>
      </section>

      {/* Sticky scrollytelling: How it works
      <section className="sticky-how-it-works">
        <div className="how-rail">
          <div className="rail-step">
            <div className="step-dot">1</div>
            <div className="rail-copy">
              <h4>Share Your Goal</h4>
              <p>“Speak with more confidence in meetings” or “Build a morning routine I enjoy”.</p>
            </div>
          </div>
          <div className="rail-step">
            <div className="step-dot">2</div>
            <div className="rail-copy">
              <h4>AI Creates Your Program</h4>
              <p>A 5-day plan with engaging host conversations tailored to your lifestyle.</p>
            </div>
          </div>
          <div className="rail-step">
            <div className="step-dot">3</div>
            <div className="rail-copy">
              <h4>Learn & Practice Daily</h4>
              <p>Five minutes a day—listen, practice, reflect. Complete within a week.</p>
            </div>
          </div>
        </div>
        <div className="how-panels">
          <div className="how-panel panel-1">
            <div className="panel-shell"><span>Examples of great goals</span></div>
          </div>
          <div className="how-panel panel-2">
            <div className="panel-shell"><span>See your 5-day plan</span></div>
          </div>
          <div className="how-panel panel-3">
            <div className="panel-shell"><span>Daily practice in action</span></div>
          </div>
        </div>
      </section> */}

      {/* Quote slab */}
      <section className="quote-slab">
        <div className="quote-inner">
          <Quote size={28} />
          <p>“It feels like a tiny podcast made just for me.”</p>
          <span className="quote-meta">— Beta user, Week 2</span>
        </div>
      </section>

      {/* Keep your existing sections below if you want, or remove the old card grid */}
    </div>
  );
};

export default HeroPage;
