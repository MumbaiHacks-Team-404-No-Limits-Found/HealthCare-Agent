# 🤖 Quick Start: LLM-Powered Volunteer Queueing

## 🚀 Get AI-Enhanced Assignments in 5 Minutes!

---

## Step 1: Get OpenAI API Key (2 minutes)

1. Visit: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)

**That's it!** The key is free to create. You pay only for usage (~$0.007 per camp planning).

---

## Step 2: Configure (1 minute)

Edit your `.env` file:

```bash
# Add this line (replace with your actual key)
OPENAI_API_KEY=sk-your-actual-api-key-here

# Optionally configure model (default is gpt-3.5-turbo)
LLM_MODEL=gpt-3.5-turbo
ENABLE_LLM_QUEUEING=true
```

---

## Step 3: Rebuild Docker (2 minutes)

```bash
# Rebuild with new dependencies
docker-compose down
docker-compose up -d --build
```

Wait for services to start (~2 minutes)...

---

## Step 4: Test It! (30 seconds)

```bash
# Run the test script
docker-compose exec backend python test_llm_queueing.py
```

You should see:

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  🤖 LLM-Powered Volunteer Queueing Test Suite  🚀     ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

✅ LLM Service is ready!
🤖 Calling LLM for priority scoring...
✅ Priority scoring completed successfully!
✅ Intelligent queue created successfully!
✅ Explanation generated successfully!

🎉 All tests PASSED!
```

---

## Step 5: Use It! (It's automatic!)

Create a camp and run planning as usual:

```bash
curl -X POST http://localhost:8000/api/camps/{camp_id}/plan
```

**The LLM queueing happens automatically!** No code changes needed.

---

## 📊 See It In Action

Watch the logs:

```bash
docker-compose logs -f backend | grep LLM
```

You'll see:
```
🤖 Starting LLM-powered volunteer queueing...
   🧠 LLM analyzed 15 volunteers for doctor/morning
   🧠 LLM analyzed 12 volunteers for nurse/afternoon
✅ LLM Queue created:
   - Volunteers analyzed: 45
   - LLM calls made: 6
   - Processing time: 3.2s
   - LLM enabled: true
📝 Generated LLM explanations for 8 assignments
```

---

## 🎉 Done!

Your Healthcare Agent is now **AI-powered**! 

### What Happens Now:

1. ✅ Volunteers are analyzed by AI
2. ✅ Intelligent priority queues are created
3. ✅ Assignments are optimized with AI insights
4. ✅ Natural language explanations are generated

### Zero Code Changes Required!

It just works automatically in your existing workflow.

---

## 💰 Cost

**Typical cost per planning run**: ~$0.007 (less than 1 cent!)

**Monthly cost (100 camps)**: ~$0.70

**Very affordable!** 💰

---

## 📚 Learn More

- **Feature Showcase**: `LLM_FEATURE_HIGHLIGHT.md`
- **Complete Guide**: `LLM_QUEUEING_GUIDE.md`
- **Full Summary**: `LLM_INTEGRATION_SUMMARY.md`

---

## 🔧 Troubleshooting

### Not working?

```bash
# Check if API key is set
docker-compose exec backend python -c "
from app.llm_service import get_llm_service
llm = get_llm_service()
print('LLM Available:', llm.is_available())
"
```

Should show: `LLM Available: True`

### Still having issues?

1. Verify API key is correct in `.env`
2. Check internet connection
3. Restart containers: `docker-compose restart backend`
4. View logs: `docker-compose logs backend`

---

## 🚀 You're All Set!

Enjoy your **AI-powered volunteer coordination system**! 🎉

---

**Total Setup Time**: 5 minutes  
**Complexity**: Super Easy  
**Impact**: Huge! 🌟

