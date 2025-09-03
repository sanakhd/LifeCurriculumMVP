# LifeCurriculum MVP

AI-powered learning platform that transforms any topic into engaging conversations between two hosts, adapted to your context and schedule.

## Key Features
- **Multi-Context Learning**: Home, Workout, and Driving modes with adaptive interactions
- **AI Conversations**: Real-time dialogue generation using OpenAI GPT-4
- **Micro-Learning Format**: ~2-3-minute sessions that fit into busy schedules
- **Progressive Structure**: 5-day learning programs for any topic

## Project Structure

## Project Structure
```LifeCurriculumMVP/
├── LifeCurriculumFE/   # Frontend code
└── LifeCurriculumBE/   # Backend code
```

- **Frontend (LifeCurriculumFE)**
  - Built with: React TS + Vite
  - Handles the user interface and client-side logic.

- **Backend (LifeCurriculumBE)**
  - Built with: Python + FastAPI
  - Provides the API and handles database or server logic.

- **Frontend (LifeCurriculumFE)**
  - Built with: React TS + Vite
  - Handles the user interface and client-side logic
- **Backend (LifeCurriculumBE)**
  - Built with: Python + FastAPI
  - Provides the API and handles AI integration

## 🚀 Quick Start

### Frontend Setup
```bash
cd LifeCurriculumFE
npm install
npm run dev
```

### Backend Setup
```bash
cd LifeCurriculumBE
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Environment Setup
Add OpenAI API key to backend .env file:
```
OPENAI_API_KEY=your_openai_key
```
