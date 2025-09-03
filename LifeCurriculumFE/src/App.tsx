// App.tsx (replace your Routes with this shape)
import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import HeroLandingPage from './components/HeroPage'
import NameEntry from './components/NameEntry'
import DashboardRouter from './components/DashboardRouter'
import MyPrograms from './components/MyPrograms'
import CreateProgram from './components/CreateProgram'
import LessonPage from './components/LessonPage'
import ProgressPage from './components/ProgressPage'
import AppLayout from './components/AppLayout'

function App() {
  const [userName, setUserName] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem('userName');
    if (saved) setUserName(saved);
    setIsLoading(false);
  }, []);

  // 3) Persist on submit
  const handleNameSubmit = (name: string) => {
    setUserName(name);
    localStorage.setItem('userName', name);
  };

  // 4) Clear on logout
  const handleReset = () => {
    setUserName('');
    localStorage.removeItem('userName');
  };

  if (isLoading) return <div style={{ padding: 20, textAlign: 'center' }}>Loading...</div>

  const isAuthed = Boolean(userName)

  return (
    <BrowserRouter>
      <Routes>
        {/* Hero landing page - first page for new users */}
        <Route
          path="/hero"
          element={
            isAuthed
              ? <Navigate to="/dashboard" replace />
              : <HeroLandingPage />
          }
        />

        {/* Name entry page */}
        <Route
          path="/welcome"
          element={
            isAuthed
              ? <Navigate to="/dashboard" replace />
              : <NameEntry onNameSubmit={handleNameSubmit} />
          }
        />

        {/* Protected layout (shows Navbar on all child routes) */}
        <Route
          element={
            isAuthed
              ? <AppLayout userName={userName} onLogout={handleReset} />
              : <Navigate to="/hero" replace />
          }
        >
          <Route path="/dashboard" element={<DashboardRouter />} />
          <Route path="/create-program" element={<CreateProgram />} />
          <Route path="/programs" element={<MyPrograms />} />
          <Route path="/programs/:programId/lesson/:dayNumber" element={<LessonPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/profile" element={<div>Profile Page (Coming Soon)</div>} />
        </Route>

        {/* Default & catch-all */}
        <Route path="/" element={<Navigate to={isAuthed ? "/dashboard" : "/hero"} replace />} />
        <Route path="*" element={<Navigate to={isAuthed ? "/dashboard" : "/hero"} replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
