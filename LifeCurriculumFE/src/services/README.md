# LifeCurriculum API Client

This directory contains TypeScript model files and API client for the LifeCurriculum backend service running at `localhost:8000`.

## Files Overview

- **`api.ts`** - Main API client with all endpoint methods
- **`apiUsageExample.ts`** - Examples showing how to use the API client
- **`../types/api.ts`** - TypeScript interfaces generated from OpenAPI schema
- **`../hooks/useApi.ts`** - React hooks for easier API integration

## Quick Start

### 1. Direct API Client Usage

```typescript
import { lifeCurriculumApi } from '../services/api';
import type { GenerateProgramRequest, ContextType } from '../types/api';

// Health check
const health = await lifeCurriculumApi.healthCheck();
console.log('Service status:', health.status);

// Generate a program
const request: GenerateProgramRequest = {
  focus_area: "Learn TypeScript fundamentals and best practices",
  target_outcome: "Build a small TypeScript project with proper typing",
  context: "home" as ContextType
};

const program = await lifeCurriculumApi.generateProgram(request);
console.log('Generated program:', program.title);
```

### 2. React Hooks Usage

```typescript
import React from 'react';
import { useGenerateProgram, useListAllPrograms } from '../hooks/useApi';
import type { ContextType } from '../types/api';

export const MyComponent: React.FC = () => {
  const generateProgram = useGenerateProgram();
  const listPrograms = useListAllPrograms();

  const handleGenerateProgram = async () => {
    try {
      await generateProgram.execute({
        focus_area: "Learn modern JavaScript ES6+ features",
        target_outcome: "Write clean, modern JavaScript code",
        context: "home" as ContextType
      });
    } catch (error) {
      console.error('Failed to generate program:', error);
    }
  };

  return (
    <div>
      <button 
        onClick={handleGenerateProgram}
        disabled={generateProgram.loading}
      >
        {generateProgram.loading ? 'Generating...' : 'Generate Program'}
      </button>
      
      {generateProgram.error && (
        <p style={{ color: 'red' }}>Error: {generateProgram.error}</p>
      )}
      
      {generateProgram.data && (
        <div>
          <h3>Generated: {generateProgram.data.title}</h3>
          <p>{generateProgram.data.description}</p>
        </div>
      )}
    </div>
  );
};
```

## Available API Methods

### Health Check
- `healthCheck()` - Check service health
- `ping()` - Alternative health check

### Program Generation
- `generateProgram(request)` - Generate program skeleton only
- `generateFullProgram(request)` - Generate complete program with lessons

### Program Management  
- `getProgramById(programId)` - Get single program by ID
- `listAllPrograms(params?)` - List all programs with pagination

### Lesson Management
- `generateLesson(request)` - Generate single lesson
- `getSingleLesson(programId, dayNumber)` - Get specific lesson
- `getAllLessonIds()` - Get all lesson IDs

### Audio Generation
- `generateLessonAudio(request)` - Generate TTS audio for lesson
- `regenerateLessonAudio(request)` - Force regenerate audio
- `getLessonAudioStatus(lessonUuid)` - Check audio status
- `deleteLessonAudio(lessonUuid)` - Delete lesson audio
- `getAvailableVoices()` - Get available TTS voices

## Available React Hooks

Each API method has a corresponding React hook:

- `useHealthCheck()`, `usePing()`
- `useGenerateProgram()`, `useGenerateFullProgram()`  
- `useGetProgramById()`, `useListAllPrograms()`
- `useGenerateLesson()`, `useGetSingleLesson()`, `useGetAllLessonIds()`
- `useGenerateLessonAudio()`, `useRegenerateLessonAudio()`
- `useGetLessonAudioStatus()`, `useDeleteLessonAudio()`, `useGetAvailableVoices()`

All hooks return: `{ execute, loading, error, data, reset }`

## Error Handling

The API client includes comprehensive error handling:

```typescript
import { ApiError } from '../services/api';

try {
  await lifeCurriculumApi.generateProgram(request);
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.status, error.message);
  } else {
    console.error('Network Error:', error);
  }
}
```

## Types

All TypeScript interfaces are available from:

```typescript
import type {
  GenerateProgramRequest,
  GenerateProgramResponse,
  GenerateFullProgramRequest,
  GenerateFullProgramResponse,
  ContextType,
  // ... and many more
} from '../types/api';
```

## Configuration

The API client is configured to connect to `http://localhost:8000`. To use a different backend URL:

```typescript
import { LifeCurriculumApi } from '../services/api';

const customApi = new LifeCurriculumApi('http://your-backend-url:port');
```

## Backend Requirements

Make sure the LifeCurriculum backend service is running at `localhost:8000` before using the API client.
