# Healthcare Volunteer Coordinator - Frontend

A modern Next.js 14+ frontend application for managing medical camp volunteers and assignments.

## 🚀 Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **HTTP Client**: Axios
- **State Management**: React Context API
- **Date Handling**: date-fns
- **React Query**: @tanstack/react-query (optional for advanced data fetching)

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout with AuthProvider
│   ├── page.tsx             # Home page (redirects to dashboard/login)
│   ├── login/               # Login page
│   ├── dashboard/           # Dashboard page (camps overview)
│   ├── camps/               # Camps management
│   │   ├── [id]/           # Dynamic camp details
│   │   │   ├── page.tsx    # Camp detail page
│   │   │   └── activity/   # Activity timeline for camp
│   │   └── page.tsx        # All camps list
│   ├── volunteers/          # Volunteers management
│   └── assignments/         # Assignments management
├── components/              # Reusable React components
│   ├── Navbar.tsx          # Top navigation bar
│   ├── Sidebar.tsx         # Side navigation
│   ├── CampCard.tsx        # Camp display card
│   ├── VolunteerCard.tsx   # Volunteer display card
│   ├── AssignmentCard.tsx  # Assignment display card
│   └── ActivityTimeline.tsx # Activity log timeline
├── hooks/                   # Custom React hooks
│   ├── useAuth.ts          # Authentication hook
│   ├── useFetch.ts         # Generic data fetching hook
│   └── useApi.ts           # API abstraction hook
├── context/                 # React Context providers
│   └── AuthContext.tsx     # Auth state management
├── lib/                     # Utilities and configurations
│   ├── api.ts              # Axios instance with interceptors
│   └── types.ts            # TypeScript type definitions
└── styles/                  # Global styles
    └── globals.css         # Tailwind imports and custom styles
```

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Environment Configuration

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
# or
yarn dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
# or
yarn build
yarn start
```

## 🔐 Authentication

The app uses JWT-based authentication:

1. Login at `/login` with credentials
2. Token is stored in localStorage
3. Token is automatically attached to API requests via Axios interceptor
4. Protected routes redirect to `/login` if not authenticated

### Demo Credentials

```
Email: admin@healthcare.org
Password: admin123
```

## 📊 Pages & Routes

| Route | Description | Protected |
|-------|-------------|-----------|
| `/` | Home (redirects) | No |
| `/login` | Login page | No |
| `/dashboard` | Dashboard with camps overview | Yes |
| `/camps` | All camps list | Yes |
| `/camps/[id]` | Camp details | Yes |
| `/camps/[id]/activity` | Activity timeline for camp | Yes |
| `/volunteers` | Volunteers list | Yes |
| `/assignments` | Assignments list | Yes |

## 🔌 API Integration

The frontend integrates with the following backend endpoints:

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Camps
- `GET /api/camps` - List all camps
- `GET /api/camps/{id}` - Get camp details
- `POST /api/camps` - Create new camp
- `PUT /api/camps/{id}` - Update camp
- `DELETE /api/camps/{id}` - Delete camp

### Volunteers
- `GET /api/volunteers` - List all volunteers
- `GET /api/volunteers/{id}` - Get volunteer details
- `POST /api/volunteers` - Create new volunteer
- `PUT /api/volunteers/{id}` - Update volunteer
- `DELETE /api/volunteers/{id}` - Delete volunteer

### Assignments
- `GET /api/assignments` - List all assignments
- `GET /api/assignments/{id}` - Get assignment details
- `POST /api/assignments` - Create new assignment
- `PUT /api/assignments/{id}` - Update assignment
- `DELETE /api/assignments/{id}` - Delete assignment

### Activity Logs
- `GET /api/activity/{camp_id}` - Get activity logs for a camp

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Loading States**: Spinner animations during data fetching
- **Error Handling**: User-friendly error messages
- **Auth Guards**: Automatic redirect to login for protected routes
- **Modern UI**: Clean, professional design with primary blue theme
- **Interactive Cards**: Hover effects and action buttons
- **Timeline View**: Visual activity log with icons and colors

## 🛠️ Custom Hooks

### `useAuth()`
Manages authentication state and provides login/logout functions.

```typescript
const { user, token, isAuthenticated, isLoading, login, logout } = useAuth();
```

### `useFetch(url, options)`
Generic data fetching hook with loading and error states.

```typescript
const { data, loading, error, refetch } = useFetch<Camp[]>('/api/camps');
```

### `useApi()`
Manual API call execution hook.

```typescript
const { data, loading, error, execute } = useApi();
await execute('/api/camps', 'POST', campData);
```

## 📦 Components

### Cards
- **CampCard**: Displays camp summary with details and actions
- **VolunteerCard**: Shows volunteer info with skills and availability
- **AssignmentCard**: Displays assignment with status badges

### Navigation
- **Navbar**: Top navigation with auth status and logout
- **Sidebar**: Side navigation menu (optional, not in use currently)

### Special Components
- **ActivityTimeline**: Visual timeline of camp activity logs with icons and colors

## 🎯 Features

✅ JWT Authentication with auto-redirect  
✅ Protected routes for authenticated users  
✅ Complete CRUD operations for camps, volunteers, and assignments  
✅ Activity log timeline with visual indicators  
✅ Responsive design for mobile and desktop  
✅ Real-time error handling and loading states  
✅ Statistics dashboard with counts and metrics  
✅ Clean, modern UI with TailwindCSS  

## 🔒 Security

- JWT tokens stored in localStorage
- Automatic token attachment to API requests
- 401 response handling (auto-logout and redirect)
- CORS configuration handled by backend
- No sensitive data in frontend code

## 🧪 Development Tips

1. **Hot Reload**: Changes auto-reload in dev mode
2. **Type Safety**: Use TypeScript types from `lib/types.ts`
3. **API Debugging**: Check browser console for API errors
4. **Styling**: Use Tailwind utility classes for consistency
5. **State Management**: Extend AuthContext for global state needs

## 📝 Future Enhancements

- [ ] Add form validation with Zod or Yup
- [ ] Implement create/edit forms for camps and volunteers
- [ ] Add pagination for large datasets
- [ ] Implement search and filtering
- [ ] Add notifications/toast messages
- [ ] Dark mode support
- [ ] Export data to CSV/PDF
- [ ] Real-time updates with WebSockets

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Failed to fetch" errors  
**Solution**: Ensure backend is running on port 8000 and NEXT_PUBLIC_API_URL is correct

**Issue**: Redirect loop on login  
**Solution**: Clear localStorage and cookies, then try logging in again

**Issue**: TypeScript errors  
**Solution**: Run `npm install` to ensure all types are installed

**Issue**: Tailwind styles not working  
**Solution**: Check `tailwind.config.js` paths and restart dev server

## 📄 License

This project is part of the Healthcare Volunteer Coordinator system.

## 👥 Support

For issues or questions, please contact the development team.

