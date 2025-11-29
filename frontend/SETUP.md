# Quick Setup Guide

## Prerequisites

- Node.js 18+ installed
- Backend API running on http://localhost:8000
- npm or yarn package manager

## Installation Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env.local` file:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at: **http://localhost:3000**

### 4. Login

Navigate to http://localhost:3000/login and use:

```
Email: admin@healthcare.org
Password: admin123
```

## Verify Backend Connection

Make sure your backend is running:

```bash
cd ../healthcare_agent/backend
source ../venv/bin/activate
uvicorn app.main:app --reload
```

Backend should be accessible at http://localhost:8000

## Troubleshooting

### Port 3000 already in use?

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

### API connection errors?

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `.env.local` has correct API URL
3. Check browser console for CORS errors

### Build errors?

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run dev
```

## Directory Structure

After installation, you should have:

```
frontend/
├── node_modules/          # Dependencies (auto-generated)
├── .next/                 # Next.js build output (auto-generated)
├── app/                   # Application pages
├── components/            # Reusable components
├── hooks/                 # Custom hooks
├── context/               # State management
├── lib/                   # Utilities
├── styles/                # Global styles
├── public/                # Static assets
├── .env.local            # Environment variables (create this)
├── package.json          # Dependencies
└── README.md             # Documentation
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment
3. ✅ Start dev server
4. ✅ Login to the app
5. 🎉 Start managing camps and volunteers!

For more details, see [README.md](./README.md)

