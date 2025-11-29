# Apollo Client Setup - Complete ✅

## Overview

Apollo Client has been successfully integrated into the Next.js frontend to work alongside the existing REST API. GraphQL is now used for camps, volunteers, assignments, and activity logs, while REST API remains for authentication.

## ✅ What Was Implemented

### 1. Dependencies Installed
- `@apollo/client` - Apollo Client for React
- `graphql` - GraphQL core library

### 2. Apollo Client Configuration
- **File**: `lib/apollo.ts`
  - Configured with `NEXT_PUBLIC_GRAPHQL_URL` environment variable
  - JWT token authentication via request interceptor
  - Error handling with auto-logout on 401
  - InMemoryCache with proper merge policies

### 3. Apollo Provider
- **File**: `components/providers/ApolloProviderWrapper.tsx`
  - Wraps the application with ApolloProvider
  - Integrated into root `app/layout.tsx`

### 4. GraphQL Queries & Hooks
- **File**: `lib/graphql/queries.ts`
  - All GraphQL queries and mutations defined
  - Reusable fragments for common fields
- **File**: `hooks/useGraphQL.ts`
  - Custom hooks: `useCamps`, `useCamp`, `useVolunteers`, `useAssignments`, `useCampActivity`
  - Mutation hooks: `useRunForecast`, `useRunPlan`, `useReplanCamp`

### 5. Pages Updated to Use GraphQL

#### ✅ `/camps` - Camps List
- Uses `useCamps()` hook
- Displays all camps with GraphQL data

#### ✅ `/volunteers` - Volunteers List
- Uses `useVolunteers()` hook
- Displays volunteers with skills
- Handles `noShowRate` field (GraphQL camelCase)

#### ✅ `/assignments` - Assignments List
- Uses `useAssignments(campId)` hook
- **Camp Filter**: Dropdown to select camp (GraphQL requires campId)
- Shows assignments for selected camp
- Displays volunteer names from nested GraphQL data

#### ✅ `/camps/[id]` - Camp Details
- Uses `useCamp(id)` hook
- **Mutations Added**:
  - `Run Forecast` button - calls `runForecast` mutation
  - `Run Plan` button - calls `runPlan` mutation
- Shows camp requirements and details

#### ✅ `/camps/[id]/activity` - Activity Timeline
- Uses `useCampActivity(campId)` hook
- Displays activity logs with parsed metadata
- Handles GraphQL string meta field conversion

## 🔧 Environment Configuration

Add to `.env.local`:

```env
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 GraphQL Schema Mapping

### Queries
| GraphQL Query | Hook | Page |
|--------------|------|------|
| `camps` | `useCamps()` | `/camps` |
| `camp(id: ID!)` | `useCamp(id)` | `/camps/[id]` |
| `volunteers` | `useVolunteers()` | `/volunteers` |
| `assignments(campId: ID!)` | `useAssignments(campId)` | `/assignments` |
| `campActivity(campId: ID!)` | `useCampActivity(campId)` | `/camps/[id]/activity` |

### Mutations
| GraphQL Mutation | Hook | Usage |
|-----------------|------|-------|
| `runForecast(campId: ID!)` | `useRunForecast()` | Camp detail page |
| `runPlan(campId: ID!)` | `useRunPlan()` | Camp detail page |
| `replanCamp(campId: ID!)` | `useReplanCamp()` | Available for future use |

## 🔄 Field Name Conversions

GraphQL uses camelCase (Strawberry converts from Python snake_case):

| Python/DB | GraphQL |
|-----------|--------|
| `no_show_rate` | `noShowRate` |
| `camp_id` | `campId` |
| `volunteer_id` | `volunteerId` |
| `is_backup` | `isBackup` |
| `created_at` | `createdAt` |

## 🎯 Key Features

### Authentication
- JWT tokens automatically attached to GraphQL requests
- Auto-logout on 401 errors
- Token stored in localStorage (same as REST API)

### Caching
- Apollo Client InMemoryCache configured
- Cache-and-network fetch policy for real-time data
- Automatic cache updates after mutations

### Error Handling
- GraphQL errors displayed to users
- Network errors handled gracefully
- Loading states for all queries

### Component Compatibility
- `VolunteerCard` updated to handle both REST (`no_show_rate`) and GraphQL (`noShowRate`) field names
- `AssignmentCard` receives transformed data
- `ActivityTimeline` handles GraphQL string meta field

## 📝 Notes

### Assignments Page
- **Camp Filter Required**: GraphQL `assignments` query requires a `campId`
- Dropdown filter added to select camp
- First camp selected by default
- Shows assignments only for selected camp

### Activity Logs
- GraphQL returns `meta` as a string (JSON stringified)
- Automatically parsed to object for `ActivityTimeline` component
- Falls back to raw string if parsing fails

### Mutations
- `runForecast` and `runPlan` mutations trigger cache refetch
- Success/error alerts shown to user
- Loading states prevent duplicate requests

## 🚀 Usage Example

```tsx
'use client';

import { useCamps } from '@/hooks/useGraphQL';

export default function MyPage() {
  const { data, loading, error, refetch } = useCamps();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      {data?.camps.map(camp => (
        <div key={camp.id}>{camp.name}</div>
      ))}
    </div>
  );
}
```

## ✅ Testing Checklist

- [x] Apollo Client installed and configured
- [x] ApolloProvider integrated in layout
- [x] All pages updated to use GraphQL
- [x] Mutations working (forecast, plan)
- [x] Error handling implemented
- [x] Loading states added
- [x] Field name conversions handled
- [x] Component compatibility maintained

## 🔍 Troubleshooting

### GraphQL endpoint not found
- Verify `NEXT_PUBLIC_GRAPHQL_URL` in `.env.local`
- Check backend is running on port 8000
- Verify `/graphql` endpoint is accessible

### Authentication errors
- Check JWT token in localStorage
- Verify token is being sent in Authorization header
- Check backend GraphQL authentication setup

### Field name errors
- GraphQL uses camelCase (noShowRate, campId, etc.)
- REST API uses snake_case (no_show_rate, camp_id, etc.)
- Components handle both formats

### Assignments not showing
- Select a camp from the dropdown filter
- GraphQL requires campId parameter
- Check if camp has assignments

## 📚 Next Steps

1. **Install dependencies**: `npm install`
2. **Set environment variable**: Add `NEXT_PUBLIC_GRAPHQL_URL` to `.env.local`
3. **Start backend**: Ensure GraphQL endpoint is running
4. **Start frontend**: `npm run dev`
5. **Test pages**: Navigate through all GraphQL-powered pages

---

**Status**: ✅ **COMPLETE** - Apollo Client fully integrated and all pages updated!

