# LifeCurriculum MVP

AI-powered learning platform that transforms any topic into engaging conversations between two hosts, adapted to your context and schedule.

## Key Features
- **Multi-Context Learning**: Home, Workout, and Driving modes with adaptive interactions
- **AI Conversations**: Real-time dialogue generation using OpenAI GPT-4
- **Micro-Learning Format**: ~2-3-minute sessions that fit into busy schedules
- **Progressive Structure**: 5-day learning programs for any topic


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

## Documentation:
- [Product Documentation](https://www.figma.com/design/3dnp3cUNPKFSnQkRh6lbrL/ABP-Demo--Product-Documentation?node-id=52-1501&t=oscjr2nqInn4RV01-1)  
- [Demo Slides](https://www.canva.com/design/DAGx3vUi53Y/cXF7m1PU3M52axuxG_1Scg/edit?utm_content=DAGx3vUi53Y&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)  

## Design: 
- [Figma Mockup (Drafts)](https://www.figma.com/make/sNp6BokGthaYVEC92DyHC8/Mock-Up-Version-of-LifeCurriculum--IDEA-ENHANCER?node-id=0-1&t=XgP127SIleWPM5u7-1)  
- [Figma MVP Wireframes](https://www.figma.com/design/ma3igLL0oVEr4RmaHwZgBI/MVP-Wireframe---LifeCurriculum-V2?node-id=0-1&t=7DlvmfvSC6vE0H79-1)


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
