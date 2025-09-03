# Life Curriculum - System Patterns

## System Architecture

### Application Flow
```
User Visit → Name Entry → Cookie Check → Landing Page → Program Creation
     ↓            ↓           ↓              ↓              ↓
First Visit   Onboarding   Persistence   Dashboard    Future Feature
```

### Component Hierarchy
```
App (Root)
├── NameEntry (First-time users)
│   └── Name form with validation
└── LandingPage (Returning users)
    ├── Header (Navigation + Avatar)
    ├── Journey Steps (5-step process)
    ├── Program Ideas (Curated suggestions)
    └── What to Expect (Feature explanation)
```

## Key Technical Decisions

### State Management Pattern
- **Decision**: Use local React state with cookie persistence
- **Rationale**: Simple user flow doesn't require complex state management
- **Implementation**: useState for UI state, cookies for persistence
- **Future**: Will likely need Context or Redux for complex program state

### Routing Strategy
- **Decision**: Conditional rendering instead of React Router
- **Rationale**: Only two main views currently
- **Implementation**: State-based view switching in App.tsx
- **Future**: React Router when multiple pages are needed

### Styling Architecture
- **Decision**: Custom CSS with component-scoped classes
- **Rationale**: Full control over design system and animations
- **Implementation**: Single App.css with BEM-like naming
- **Future**: Consider CSS modules or styled-components for larger app

## Design Patterns

### Component Patterns
- **Functional Components**: All components use function syntax with hooks
- **Props Interface**: TypeScript interfaces define component contracts
- **Event Handling**: Callback props for parent-child communication
- **Conditional Rendering**: State-driven UI changes

### Data Flow Patterns
- **Unidirectional Flow**: Data flows down, events bubble up
- **Single Source of Truth**: App.tsx maintains primary application state
- **Effect Patterns**: useEffect for side effects (cookie reading)

### User Experience Patterns
- **Progressive Disclosure**: Start simple (name), reveal complexity gradually
- **Immediate Feedback**: Form validation and state updates
- **Persistence**: Seamless experience across sessions
- **Visual Hierarchy**: Clear information architecture

## Critical Implementation Paths

### User Onboarding Flow
1. **Initial Load**: Check for existing user cookie
2. **New User Path**: Show NameEntry component
3. **Form Submission**: Validate, store cookie, update state
4. **State Transition**: Switch to LandingPage view
5. **Returning User**: Direct to LandingPage with personalized content

### Cookie Management System
```javascript
// Set cookie with 365-day expiration
setCookie(name, value, days)

// Read cookie with null fallback
getCookie(name) → string | null

// Clear cookie for reset functionality
Reset sets expiration to past date
```

### Component Communication
```
App.tsx (State Owner)
├── userName: string
├── showWelcome: boolean
├── handleNameSubmit(name) → updates state + cookie
└── handleReset() → clears state + cookie

NameEntry.tsx
├── Receives: onNameSubmit callback
└── Manages: local input state

LandingPage.tsx
├── Receives: userName, onReset callback
└── Displays: personalized content
```

## Architectural Principles

### Separation of Concerns
- **App.tsx**: Application state and routing logic
- **Components**: UI rendering and local interaction
- **CSS**: Visual design and layout
- **Utilities**: Cookie management functions

### Component Responsibilities
- **Single Purpose**: Each component has one clear responsibility
- **Reusability**: Components designed for potential reuse
- **Encapsulation**: Internal state management where appropriate
- **Interface Contracts**: Clear props and callback definitions

### Performance Considerations
- **Minimal Re-renders**: State updates only when necessary
- **Component Optimization**: Functional components with hooks
- **Asset Loading**: CSS animations and transitions for smooth UX
- **Development Speed**: Vite's HMR for fast iteration

## Future Architectural Evolution

### Scalability Patterns
- **Routing**: React Router for multi-page application
- **State Management**: Context API or Redux for complex program state
- **Component Library**: Shared design system components
- **API Integration**: Service layer for backend communication

### Modularization Strategy
- **Feature Modules**: Organize by feature rather than file type
- **Shared Components**: Common UI elements in shared directory
- **Custom Hooks**: Extract complex logic into reusable hooks
- **Utility Libraries**: Helper functions and common patterns
