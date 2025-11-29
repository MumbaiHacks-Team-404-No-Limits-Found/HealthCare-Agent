# 🚀 Quick Start Guide

Get the Healthcare Volunteer Coordinator frontend running in 3 minutes!

## Step 1: Install Dependencies (1 min)

```bash
cd frontend
npm install
```

Or use the automated installer:

```bash
./install.sh
```

## Step 2: Configure Environment (30 sec)

Create `.env.local`:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## Step 3: Start the App (30 sec)

```bash
npm run dev
```

## Step 4: Access the Application (30 sec)

1. Open: **http://localhost:3000**
2. You'll be redirected to login
3. Use credentials:
   - **Email**: `admin@healthcare.org`
   - **Password**: `admin123`

## 🎉 You're Ready!

After login, you'll see the **Dashboard** with all medical camps.

### Available Pages:

- 📊 **Dashboard** - http://localhost:3000/dashboard
- 🏕️ **Camps** - http://localhost:3000/camps
- 👥 **Volunteers** - http://localhost:3000/volunteers
- 📋 **Assignments** - http://localhost:3000/assignments
- 📜 **Activity Log** - http://localhost:3000/camps/{camp_id}/activity

### Test the Activity Log Feature:

1. Go to Dashboard
2. Click on any camp card
3. Click **"Activity Log"** button
4. View the timeline of all activities for that camp!

## 🔧 Troubleshooting

### "Cannot GET /api/camps"
**Problem**: Backend not running  
**Solution**: Start backend first
```bash
cd ../healthcare_agent/backend
source ../venv/bin/activate
uvicorn app.main:app --reload
```

### Port 3000 in use
**Solution**: Use different port
```bash
npm run dev -- -p 3001
```

### Module not found errors
**Solution**: Reinstall dependencies
```bash
rm -rf node_modules .next
npm install
```

## 📚 Next Steps

- Read [README.md](./README.md) for full documentation
- Check [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) for architecture details
- See [SETUP.md](./SETUP.md) for detailed setup instructions

## ✨ Key Features to Try

1. **View Camps** - See all medical camps with requirements
2. **Camp Details** - Click any camp to see full details
3. **Activity Timeline** - View activity logs with visual indicators
4. **Volunteers** - Browse volunteer database with skills
5. **Assignments** - Track all volunteer assignments

## 🎯 Demo Workflow

1. **Login** with admin credentials
2. **Dashboard**: View all camps
3. **Camp Details**: Click on a camp → See requirements
4. **Activity Log**: Click "Activity Log" → See timeline
5. **Volunteers**: Browse volunteer list
6. **Assignments**: View all assignments

## 💡 Tips

- All pages auto-redirect to login if not authenticated
- Token is stored in localStorage
- Logout button in top-right navbar
- Refresh button on each page to reload data
- Error messages appear in red banners

## 🐛 Common Issues

**Q: I see "Loading..." forever**  
A: Check browser console for API errors, ensure backend is running

**Q: Login fails**  
A: Verify backend `/auth/login` endpoint is working, check credentials

**Q: No data showing**  
A: Ensure database has data, check backend logs

**Q: Activity log is empty**  
A: No activities recorded yet for that camp. Try creating assignments.

## 📞 Need Help?

- Check browser console (F12) for errors
- Review backend logs
- Verify `.env.local` configuration
- Ensure all dependencies installed

---

**Happy coding! 🎉**

