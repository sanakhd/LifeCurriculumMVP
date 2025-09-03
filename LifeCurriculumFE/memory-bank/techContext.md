# Life Curriculum - Technical Context

## Technology Stack

### Core Technologies
- **React**: 19.1.1 - Latest version with concurrent features
- **TypeScript**: ~5.8.3 - Type safety and developer experience
- **Vite**: ^7.1.2 - Fast build tool with HMR
- **Node.js**: Modern ES modules setup

### Development Tools
- **ESLint**: Code quality and consistency
- **TypeScript ESLint**: Type-aware linting
- **React Hooks ESLint**: React-specific rules
- **React Refresh**: Fast development updates

## Development Setup

### Project Structure
```
src/
├── App.tsx              # Main application component
├── App.css              # Global styles and animations
├── main.tsx             # Application entry point
├── components/          # React components
│   ├── NameEntry.tsx    # Initial user onboarding
│   └── LandingPage.tsx  # Main dashboard/landing
├── hooks/               # Custom React hooks (future)
├── services/            # API and external services (future)
└── types/               # TypeScript type definitions (future)
```

### Build Configuration
- **Vite Config**: Standard React setup with fast refresh
- **TypeScript Config**: Strict mode enabled, modern target
- **ESLint Config**: React and TypeScript best practices

## Technical Patterns

### State Management
- **Local State**: React hooks (useState, useEffect)
- **Persistence**: Browser cookies for user data
- **Pattern**: Simple state lifting, no complex state management yet

### Component Architecture
- **Functional Components**: Modern React with hooks
- **Props Interface**: TypeScript interfaces for type safety
- **Conditional Rendering**: Based on authentication/onboarding state

### Styling Approach
- **CSS**: Custom CSS with modern features
- **Animation**: CSS transitions and transforms
- **Responsive**: Mobile-first responsive design
- **Visual Design**: Gradient backgrounds, modern UI patterns

## Technical Constraints

### Browser Support
- Modern browsers with ES6+ support
- Cookie support required for persistence
- CSS Grid and Flexbox support

### Performance Considerations
- Vite's fast HMR for development
- Tree shaking for production builds
- Minimal dependencies for fast loading

### Security
- Client-side only (no sensitive data)
- Cookie-based user persistence
- No authentication system currently

## Development Workflow

### Local Development
```bash
npm run dev     # Start development server (usually port 5173+)
npm run build   # Production build
npm run lint    # Code quality checks
npm run preview # Preview production build
```

### Hot Module Replacement
- Vite provides instant updates during development
- React Fast Refresh preserves component state
- CSS updates without page refresh

## Future Technical Considerations

### Planned Integrations
- Backend API for program data and progress
- User authentication system
- AI conversation endpoints
- Progress tracking and analytics

### Scalability Patterns
- Component library structure
- Custom hooks for complex logic
- Context providers for global state
- Service layer for API calls

### Performance Optimization
- Code splitting for larger app
- Lazy loading for program content
- Caching strategies for user data
- Progressive Web App features
