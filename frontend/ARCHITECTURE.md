# Frontend Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND APPLICATION                      │
│                    (Next.js 14 + TypeScript)                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Login     │  │  Dashboard   │  │    Camps     │         │
│  │    Page      │  │    Page      │  │    Pages     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Volunteers  │  │ Assignments  │  │  ⭐ Activity │         │
│  │    Page      │  │    Page      │  │   Timeline   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      COMPONENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │  Navbar  │ │ CampCard │ │Volunteer │ │Assignment│         │
│  │          │ │          │ │  Card    │ │   Card   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                 │
│  ┌──────────┐ ┌──────────────────────────────────┐            │
│  │ Sidebar  │ │  ⭐ ActivityTimeline Component  │            │
│  │          │ │  (Visual Timeline with Icons)    │            │
│  └──────────┘ └──────────────────────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────┐            │
│  │          AuthContext (React Context)           │            │
│  │  • User state                                  │            │
│  │  • Token management                            │            │
│  │  • Login/Logout functions                      │            │
│  │  • Authentication status                       │            │
│  └────────────────────────────────────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CUSTOM HOOKS LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  useAuth    │  │  useFetch   │  │   useApi    │            │
│  │             │  │             │  │             │            │
│  │ • login()   │  │ • data      │  │ • execute() │            │
│  │ • logout()  │  │ • loading   │  │ • data      │            │
│  │ • user      │  │ • error     │  │ • loading   │            │
│  │ • token     │  │ • refetch() │  │ • error     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API CLIENT LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────┐            │
│  │         Axios Instance (lib/api.ts)            │            │
│  │                                                │            │
│  │  Request Interceptor:                          │            │
│  │  • Add JWT token to Authorization header      │            │
│  │                                                │            │
│  │  Response Interceptor:                         │            │
│  │  • Handle 401 (auto-logout)                   │            │
│  │  • Error formatting                            │            │
│  └────────────────────────────────────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND REST API                           │
│                   (FastAPI @ localhost:8000)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST   /auth/login              → Login                       │
│  GET    /auth/me                 → Current user                │
│  GET    /api/camps               → List camps                  │
│  GET    /api/camps/{id}          → Camp details                │
│  ⭐ GET  /api/activity/{camp_id} → Activity logs ⭐            │
│  GET    /api/volunteers          → List volunteers             │
│  GET    /api/assignments         → List assignments            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE                                │
│                    (MongoDB @ localhost)                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### Authentication Flow
```
1. User enters credentials
   ↓
2. POST /auth/login with { email, password }
   ↓
3. Backend validates & returns JWT token
   ↓
4. Frontend stores token in localStorage
   ↓
5. Token attached to all future requests
   ↓
6. 401 response → auto logout & redirect
```

### Activity Log Flow (NEW!)
```
1. User navigates to /camps/[id]/activity
   ↓
2. Component calls useFetch('/api/activity/{camp_id}')
   ↓
3. Axios adds JWT token to request
   ↓
4. GET /api/activity/{camp_id}
   ↓
5. Backend queries activity_logs collection
   ↓
6. Returns ActivityLog[] sorted by timestamp DESC
   ↓
7. ActivityTimeline component renders visual timeline
   ↓
8. User sees color-coded events with icons & metadata
```

### Standard Data Fetching Flow
```
1. Component renders
   ↓
2. useFetch hook triggered
   ↓
3. Axios request with auth token
   ↓
4. Backend processes request
   ↓
5. Response data received
   ↓
6. Component re-renders with data
```

## 🧩 Component Hierarchy

```
App
├── AuthProvider (Context)
│   └── Router
│       ├── Public Routes
│       │   ├── / (Home - redirect)
│       │   └── /login
│       └── Protected Routes
│           ├── Navbar
│           └── Content
│               ├── /dashboard
│               │   └── CampCard[]
│               ├── /camps
│               │   └── CampCard[]
│               ├── /camps/[id]
│               │   └── Camp Details
│               ├── /camps/[id]/activity ⭐
│               │   └── ActivityTimeline ⭐
│               ├── /volunteers
│               │   └── VolunteerCard[]
│               └── /assignments
│                   └── AssignmentCard[]
```

## 📦 Module Dependencies

```
Next.js 14.2.0
├── React 18.3.0
├── React DOM 18.3.0
└── TypeScript 5.4.0

Styling
├── TailwindCSS 3.4.0
├── PostCSS 8.4.0
└── Autoprefixer 10.4.0

HTTP & Data
├── Axios 1.6.0
└── date-fns 3.3.0

State (Optional)
├── Zustand 4.5.0
└── React Query 5.28.0
```

## 🔐 Security Architecture

```
┌─────────────────────────────────┐
│   User Authentication           │
├─────────────────────────────────┤
│ 1. Login Form                   │
│ 2. JWT Token Generation         │
│ 3. Token Storage (localStorage) │
│ 4. Token Validation             │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   Request Security              │
├─────────────────────────────────┤
│ 1. Axios Interceptor            │
│ 2. Add Authorization Header     │
│ 3. HTTPS (production)           │
│ 4. CORS Handling                │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   Route Protection              │
├─────────────────────────────────┤
│ 1. Auth Context Check           │
│ 2. Redirect if not authenticated│
│ 3. Middleware (optional)        │
└─────────────────────────────────┘
```

## 🎨 Styling Architecture

```
Global Styles (styles/globals.css)
├── Tailwind Base
├── Tailwind Components
├── Tailwind Utilities
└── Custom CSS
    ├── Scrollbar styles
    ├── Animations
    └── Custom classes

Component Styles (Inline Tailwind)
├── Layout classes
├── Responsive breakpoints
├── Color utilities
├── Spacing utilities
└── State variants (hover, focus, etc.)

Theme Configuration (tailwind.config.js)
├── Colors (primary, success, warning, danger)
├── Breakpoints (sm, md, lg, xl)
├── Spacing scale
└── Typography
```

## 📱 Responsive Strategy

```
Mobile First Approach
├── Base: Mobile (< 640px)
│   └── Single column layout
├── sm: (640px+)
│   └── Adjusted typography
├── md: (768px+)
│   └── 2-column grids
├── lg: (1024px+)
│   └── 3-column grids
└── xl: (1280px+)
    └── Max width containers
```

## 🚀 Build & Deploy Architecture

```
Development
├── npm run dev
├── Hot reload enabled
├── Source maps
└── Fast refresh

Production
├── npm run build
│   ├── TypeScript compilation
│   ├── Tree shaking
│   ├── Code splitting
│   ├── Minification
│   └── Optimization
└── npm start
    └── Production server
```

## 🧪 Testing Strategy (Future)

```
Unit Tests
├── Component tests (Jest + React Testing Library)
├── Hook tests
└── Utility tests

Integration Tests
├── API integration tests
├── Authentication flow tests
└── User journey tests

E2E Tests
├── Cypress or Playwright
├── Critical user paths
└── Cross-browser testing
```

## 📊 Performance Optimization

```
Next.js Built-in
├── Automatic code splitting
├── Route prefetching
├── Image optimization
└── Font optimization

Custom Optimizations
├── Lazy loading components
├── Memoization (React.memo)
├── useMemo for expensive calculations
└── useCallback for event handlers

Future Enhancements
├── React Query for caching
├── Service Worker for offline
├── Virtual scrolling for large lists
└── CDN for static assets
```

## 🔍 Error Handling Architecture

```
API Level
├── Axios interceptors
├── 401 → Auto logout
├── 500 → Error message
└── Network errors → User notification

Component Level
├── Error boundaries (React 18)
├── Try-catch blocks
├── Error state in hooks
└── User-friendly messages

User Feedback
├── Toast notifications (future)
├── Error banners
├── Loading states
└── Empty states
```

---

## ✅ Architecture Benefits

1. **Separation of Concerns**: Clear layer separation
2. **Reusability**: Custom hooks and components
3. **Type Safety**: TypeScript throughout
4. **Maintainability**: Clean folder structure
5. **Scalability**: Easy to add new features
6. **Security**: JWT auth with interceptors
7. **Performance**: Next.js optimizations
8. **Developer Experience**: Hot reload, TypeScript, ESLint

---

*Architecture designed for production-grade applications* 🏗️

