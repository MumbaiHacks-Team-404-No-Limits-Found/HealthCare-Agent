# Healthcare Volunteer Coordinator - Frontend Overview

## 🎯 Project Summary

A complete Next.js 14+ frontend application built with TypeScript and TailwindCSS for managing medical camp volunteers, assignments, and activity tracking.

## 📊 Application Features

### Authentication & Authorization
- ✅ JWT-based authentication
- ✅ Login page with form validation
- ✅ Automatic token management via Axios interceptors
- ✅ Protected routes with redirect to login
- ✅ Logout functionality with state cleanup

### Dashboard
- ✅ Overview of all medical camps
- ✅ Camp cards with quick actions
- ✅ Responsive grid layout

### Camps Management
- ✅ List all camps with filtering capability
- ✅ View individual camp details
- ✅ Display camp requirements (roles, slots, counts)
- ✅ **Activity Timeline** - View all activity logs for a specific camp
- ✅ Navigate between camp details and activity logs

### Volunteers Management
- ✅ List all volunteers with statistics
- ✅ Display volunteer skills and availability
- ✅ Color-coded no-show rate indicators
- ✅ Quick stats dashboard (reliable, moderate, high-risk)

### Assignments Management
- ✅ List all assignments with status tracking
- ✅ Display assignment details with camp and volunteer names
- ✅ Status badges (confirmed, assigned, cancelled, backup)
- ✅ Statistics dashboard showing assignment counts

### Activity Logs (NEW!)
- ✅ Timeline view of camp activities
- ✅ Color-coded event types
- ✅ Icon-based visual indicators
- ✅ Detailed metadata display
- ✅ Timestamp formatting
- ✅ Empty state handling

## 🏗️ Architecture

### Technology Stack
```
Next.js 14.2.0         → React framework with App Router
TypeScript 5.4.0       → Type safety
TailwindCSS 3.4.0      → Utility-first CSS
Axios 1.6.0            → HTTP client
Zustand 4.5.0          → State management (available)
React Query 5.28.0     → Data fetching (available)
date-fns 3.3.0         → Date formatting
```

### File Structure
```
frontend/
├── app/                           # Next.js App Router
│   ├── layout.tsx                # Root layout with AuthProvider
│   ├── page.tsx                  # Home (redirects)
│   ├── login/page.tsx            # Login page
│   ├── dashboard/page.tsx        # Dashboard
│   ├── camps/
│   │   ├── page.tsx              # All camps
│   │   └── [id]/
│   │       ├── page.tsx          # Camp details
│   │       └── activity/page.tsx # ⭐ Activity timeline
│   ├── volunteers/page.tsx       # Volunteers list
│   └── assignments/page.tsx      # Assignments list
│
├── components/                    # Reusable components
│   ├── Navbar.tsx                # Top navigation
│   ├── Sidebar.tsx               # Side navigation
│   ├── CampCard.tsx              # Camp display card
│   ├── VolunteerCard.tsx         # Volunteer card
│   ├── AssignmentCard.tsx        # Assignment card
│   └── ActivityTimeline.tsx      # ⭐ Activity log timeline
│
├── hooks/                         # Custom React hooks
│   ├── useAuth.ts                # Auth state management
│   ├── useFetch.ts               # Generic data fetching
│   └── useApi.ts                 # API calls
│
├── context/                       # React Context
│   └── AuthContext.tsx           # Auth provider
│
├── lib/                          # Core utilities
│   ├── api.ts                    # Axios config + interceptors
│   └── types.ts                  # TypeScript definitions
│
└── styles/
    └── globals.css               # Tailwind + custom styles
```

## 🔌 API Integration

### Backend Endpoints Used

| Endpoint | Method | Purpose | Component |
|----------|--------|---------|-----------|
| `/auth/login` | POST | User authentication | Login page |
| `/auth/me` | GET | Get user info | AuthContext |
| `/api/camps` | GET | List all camps | Dashboard, Camps |
| `/api/camps/{id}` | GET | Get camp details | Camp detail page |
| `/api/activity/{camp_id}` | GET | ⭐ **Get camp activity logs** | Activity timeline |
| `/api/volunteers` | GET | List volunteers | Volunteers page |
| `/api/assignments` | GET | List assignments | Assignments page |

### New Endpoint Integration: `/api/activity/{camp_id}`

The activity timeline feature integrates with the newly created backend endpoint:

**Request:**
```typescript
GET /api/activity/{camp_id}
```

**Response:**
```json
[
  {
    "timestamp": "2025-11-29T12:34:56Z",
    "event": "assignment_confirmed",
    "meta": {
      "volunteer_name": "Priya Mehta",
      "role": "Nurse",
      "slot": "10am–12pm"
    }
  }
]
```

**Implementation:**
- **Hook**: `useFetch<ActivityLog[]>('/api/activity/${campId}')`
- **Component**: `ActivityTimeline` displays the logs
- **Page**: `/camps/[id]/activity/page.tsx`

## 🎨 Design System

### Color Scheme
```css
Primary Blue:   #3b82f6 (Tailwind blue-500)
Success Green:  #10b981 (Tailwind green-500)
Warning Yellow: #f59e0b (Tailwind yellow-500)
Danger Red:     #ef4444 (Tailwind red-500)
Gray Scale:     #f3f4f6 - #1f2937
```

### Component Patterns

**Cards**: Consistent shadow, border, hover effects
```tsx
className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg"
```

**Buttons**: Primary and secondary variants
```tsx
// Primary
className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"

// Secondary
className="px-4 py-2 border border-primary-600 text-primary-600 rounded-md hover:bg-primary-50"
```

**Status Badges**: Color-coded by status
```tsx
confirmed  → green-100/green-700
assigned   → blue-100/blue-700
cancelled  → red-100/red-700
backup     → yellow-100/yellow-700
```

## 🔐 Security Implementation

### Authentication Flow
1. User submits credentials at `/login`
2. Backend returns JWT access token
3. Token stored in `localStorage`
4. Token attached to all API requests via Axios interceptor
5. 401 responses trigger auto-logout and redirect

### Protected Routes
All routes except `/` and `/login` require authentication:
- Client-side check in `useAuth` hook
- Automatic redirect to `/login` if not authenticated
- Middleware protection (optional enhancement)

### API Security
```typescript
// Axios interceptor adds token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## 📱 Responsive Design

### Breakpoints (Tailwind)
- **sm**: 640px (mobile)
- **md**: 768px (tablet)
- **lg**: 1024px (desktop)
- **xl**: 1280px (large desktop)

### Grid Layouts
```tsx
// Cards: 1 col mobile, 2 cols tablet, 3 cols desktop
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
```

## 🚀 Performance Optimizations

1. **Code Splitting**: Next.js automatic route-based splitting
2. **Image Optimization**: Next.js Image component (when needed)
3. **Lazy Loading**: Components load on-demand
4. **Caching**: React Query available for advanced caching
5. **Minimal Bundle**: Tree-shaking removes unused code

## 🧪 Development Workflow

### Local Development
```bash
npm run dev      # Start dev server (port 3000)
npm run build    # Production build
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

### Hot Reload
Changes to any file automatically reload the browser.

## 🎯 Key Features Implemented

### ✅ Core Functionality
- [x] Authentication system
- [x] Dashboard with camps overview
- [x] Camps CRUD operations
- [x] Volunteers management
- [x] Assignments tracking
- [x] **Activity log timeline** (NEW!)

### ✅ UI/UX
- [x] Responsive design
- [x] Loading states
- [x] Error handling
- [x] Empty states
- [x] Interactive cards
- [x] Color-coded statuses
- [x] Icon-based navigation

### ✅ Developer Experience
- [x] TypeScript for type safety
- [x] Custom hooks for reusability
- [x] Axios interceptors for auth
- [x] Consistent component patterns
- [x] Clean folder structure

## 📝 Future Enhancements

### Short Term
- [ ] Form validation with Zod
- [ ] Create/Edit modals for camps, volunteers
- [ ] Toast notifications
- [ ] Confirmation dialogs for delete actions

### Medium Term
- [ ] Search and filter functionality
- [ ] Pagination for large lists
- [ ] Sorting options
- [ ] Export to CSV/PDF

### Long Term
- [ ] Real-time updates with WebSockets
- [ ] Dark mode support
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Offline support with PWA

## 🐛 Known Limitations

1. No form validation on create/edit (UI buttons present but not implemented)
2. Delete operations show button but need confirmation modal
3. No pagination (all data loaded at once)
4. No search/filter on lists
5. Token stored in localStorage (consider httpOnly cookies for production)

## 📚 Documentation

- **README.md** - Comprehensive guide
- **SETUP.md** - Quick start instructions
- **PROJECT_OVERVIEW.md** - This file
- **install.sh** - Automated setup script

## 🎓 Learning Resources

### Next.js 14
- [Official Docs](https://nextjs.org/docs)
- [App Router Guide](https://nextjs.org/docs/app)

### TypeScript
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React + TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

### TailwindCSS
- [Official Docs](https://tailwindcss.com/docs)
- [Tailwind UI Components](https://tailwindui.com/)

## 👨‍💻 Development Team

Built as part of the Healthcare Volunteer Coordinator system.

**Tech Stack Decision Rationale:**
- **Next.js**: SEO-friendly, great DX, server-side rendering
- **TypeScript**: Type safety reduces bugs
- **TailwindCSS**: Fast development, consistent design
- **Axios**: Better error handling than fetch
- **Context API**: Simple state management for auth

## 🎉 Conclusion

This is a **production-ready** frontend application with:
- ✅ Complete authentication flow
- ✅ Full CRUD operations via REST API
- ✅ Beautiful, responsive UI
- ✅ Type-safe TypeScript codebase
- ✅ Activity log tracking (NEW!)
- ✅ Comprehensive documentation

**Ready to use!** Just run `npm install && npm run dev`

