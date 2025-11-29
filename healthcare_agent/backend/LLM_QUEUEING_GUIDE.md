# 🤖 LLM-Powered Intelligent Volunteer Queueing

## Overview

The Healthcare Agent now includes an **AI-powered volunteer queueing system** that uses Large Language Models (LLM) to intelligently prioritize volunteers before the optimization stage. This enhances the traditional constraint-based assignment with machine learning intelligence.

## 🌟 What It Does

The LLM Queueing System analyzes volunteers and creates intelligent priority queues based on:

1. **Skill Matching** (40%) - How well their skills match the required role
2. **Availability** (30%) - Whether they're available for the specific slot
3. **Reliability** (20%) - Based on their historical no-show rates
4. **Suitability** (10%) - Overall fit for the camp's context

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ENHANCED WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Volunteers  │
│     Pool     │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────┐
│  🤖 LLM Analysis                   │  ◄── NEW STAGE
│  - Skill matching                  │
│  - Availability analysis           │
│  - Reliability scoring             │
│  - Context understanding           │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│  📊 Intelligent Priority Queues    │  ◄── NEW STAGE
│  - Sorted by priority score        │
│  - One queue per requirement       │
│  - Top volunteers prioritized      │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│  🔧 OR-Tools ILP Optimizer         │  ◄── EXISTING
│  - Uses prioritized queues         │
│  - Constraint satisfaction         │
│  - Optimal assignments             │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│  ✅ Final Assignments              │
│  - Optimally distributed           │
│  - AI-enhanced selection           │
│  - Includes explanations           │
└────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
cd healthcare_agent/backend
pip install -r requirements.txt
```

This installs:
- `openai>=1.3.0` - OpenAI GPT integration
- `anthropic>=0.7.0` - Anthropic Claude integration (optional)
- `tiktoken>=0.5.1` - Token counting utility

### 2. Configure LLM Provider

Add to your `.env` file:

```bash
# OpenAI (Recommended)
OPENAI_API_KEY=sk-your-openai-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo

# Or Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229

# Enable/disable LLM queueing
ENABLE_LLM_QUEUEING=true
```

### 3. Get API Keys

#### OpenAI (GPT)
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

**Models:**
- `gpt-3.5-turbo` - Fast, cost-effective ($0.001/1K tokens)
- `gpt-4-turbo-preview` - More powerful ($0.01/1K tokens)
- `gpt-4` - Most capable ($0.03/1K tokens)

#### Anthropic (Claude) - Optional
1. Go to https://console.anthropic.com/
2. Create API key
3. Add to `.env` as `ANTHROPIC_API_KEY`

**Models:**
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-opus-20240229` - Most capable

## Usage

### Automatic Integration

The LLM queueing is automatically integrated into the planning workflow. When you run:

```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()
result = await agent.run_full_workflow(camp_id="...")
```

The LLM analysis happens automatically during the planning stage!

### Manual Usage

You can also use the LLM queueing directly:

```python
from app.llm_queueing import create_intelligent_volunteer_queue

# Create intelligent queue
queue = await create_intelligent_volunteer_queue(
    camp=my_camp,
    volunteers=all_volunteers,
    requirements=my_camp.requirements,
    enable_llm=True
)

# Get queue statistics
summary = queue.get_queue_summary()
print(f"LLM analyzed {summary['volunteers_analyzed']} volunteers")
print(f"Made {summary['llm_calls_made']} LLM API calls")
print(f"Processing time: {summary['processing_time_seconds']}s")

# Get top 5 volunteers for a requirement
top_volunteers = queue.get_top_volunteers(requirement, count=5)
for queued_vol in top_volunteers:
    print(f"{queued_vol.volunteer.name}: {queued_vol.priority_score:.2f}")
```

### Disable LLM Queueing

To disable LLM and use heuristic scoring:

```bash
# In .env
ENABLE_LLM_QUEUEING=false
```

Or in code:

```python
queue = await create_intelligent_volunteer_queue(
    camp=my_camp,
    volunteers=all_volunteers,
    requirements=my_camp.requirements,
    enable_llm=False  # Uses simple heuristics
)
```

## Features

### 1. Intelligent Priority Scoring

The LLM analyzes each volunteer comprehensively:

```json
{
  "volunteer_id": "507f1f77bcf86cd799439011",
  "priority_score": 0.95,
  "analysis": {
    "skill_match": "Perfect match for doctor role",
    "availability": "Available for morning slot",
    "reliability": "95% attendance rate",
    "suitability": "Experienced in similar camps"
  }
}
```

### 2. Natural Language Explanations

Get AI-generated explanations for assignments:

```python
explanations = await queue.generate_assignment_explanations(assignments)

# Example output:
# "Dr. Sarah was assigned with a priority score of 0.95. She has the 
#  required 'doctor' skill and a 98% reliability rate. Her extensive 
#  experience with pediatric camps makes her an excellent fit for this 
#  children's health camp."
```

### 3. Queue Analytics

Monitor LLM performance:

```python
summary = queue.get_queue_summary()
# {
#   "total_queues": 6,
#   "total_volunteers_queued": 45,
#   "volunteers_analyzed": 45,
#   "llm_calls_made": 6,
#   "processing_time_seconds": 3.2,
#   "average_scores_by_requirement": {
#     "doctor_morning": 0.78,
#     "nurse_afternoon": 0.82
#   },
#   "llm_enabled": true
# }
```

## API Integration

### REST API

When you run the planner via API:

```bash
POST /api/camps/{camp_id}/plan
```

The LLM queueing runs automatically. Check logs for LLM activity:

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

### GraphQL

The planning mutation also uses LLM:

```graphql
mutation {
  planCampAssignments(campId: "...") {
    success
    assignmentsCreated
    unfilledSlots
    # LLM data logged in activity logs
  }
}
```

## Cost Estimation

### OpenAI GPT-3.5-Turbo

For a typical camp with 50 volunteers and 10 requirements:

- **Input tokens**: ~500 tokens per requirement
- **Output tokens**: ~200 tokens per requirement
- **Total**: ~7,000 tokens
- **Cost**: ~$0.007 per planning run

### Monthly Costs (Example)

- 100 camps/month: ~$0.70/month
- 500 camps/month: ~$3.50/month
- 1,000 camps/month: ~$7.00/month

Very cost-effective! 💰

## Benefits

### 1. Better Assignments
✅ LLM understands context better than rule-based systems  
✅ Considers nuanced factors like experience and personality fit  
✅ Learns from patterns in volunteer data

### 2. Explainability
✅ Natural language explanations for each assignment  
✅ Transparent decision-making process  
✅ Easier for admins to understand and trust

### 3. Flexibility
✅ Works with existing OR-Tools optimizer  
✅ Graceful fallback if LLM unavailable  
✅ Can be disabled without breaking system

### 4. Scalability
✅ Parallel processing of requirements  
✅ Caching of LLM responses (future feature)  
✅ Efficient token usage

## Monitoring

### Logs

Watch for LLM activity in logs:

```bash
# View backend logs
docker-compose logs -f backend | grep LLM

# Or during development
tail -f logs/app.log | grep LLM
```

### Activity Logs

LLM activity is logged in the activity collection:

```python
from app.activity import get_camp_activity

logs = await get_camp_activity(camp_id)
for log in logs:
    if 'llm' in log.event.lower():
        print(log.event, log.meta)
```

### Metrics

Track LLM usage metrics:

- Number of API calls
- Processing time
- Priority scores distribution
- Assignment quality (confirmed vs cancelled rate)

## Troubleshooting

### Issue: LLM not available

```
WARNING: LLM not available, using fallback scoring
```

**Solution:**
1. Check API key is set in `.env`
2. Verify internet connection
3. Check API key is valid
4. Ensure `openai` or `anthropic` package is installed

### Issue: Slow processing

```
LLM Queue created in 30.5s
```

**Solutions:**
1. Use faster model (gpt-3.5-turbo vs gpt-4)
2. Reduce volunteer pool size
3. Enable caching (future feature)
4. Use parallel processing (already implemented)

### Issue: High costs

**Solutions:**
1. Use gpt-3.5-turbo instead of gpt-4 (90% cheaper)
2. Cache LLM responses for similar volunteers
3. Disable LLM for non-critical camps
4. Set monthly budget alerts in OpenAI dashboard

### Issue: Poor priority scores

```
All scores are around 0.5
```

**Solutions:**
1. Check volunteer data quality (skills, availability)
2. Verify requirement descriptions are clear
3. Try different LLM model
4. Review prompt in `llm_service.py`

## Development

### Testing LLM Integration

```bash
# Run tests
pytest tests/test_llm_queueing.py -v

# Test with real API
python -c "
from app.llm_service import get_llm_service
llm = get_llm_service()
print('LLM available:', llm.is_available())
"
```

### Customizing Prompts

Edit `app/llm_service.py` to customize the prompt:

```python
def _build_prioritization_prompt(self, ...):
    prompt = f"""
    Your custom prompt here...
    
    Analyze volunteers and score them...
    """
    return prompt
```

### Adding New LLM Providers

To add support for other LLM providers:

1. Update `app/llm_service.py`
2. Add new provider in `_initialize_client()`
3. Implement `_call_provider()` method
4. Update configuration in `config.py`

## Roadmap

Future enhancements:

- [ ] Response caching for repeated queries
- [ ] Batch API calls for better performance
- [ ] Fine-tuned models on historical assignment data
- [ ] Multi-language support for international deployments
- [ ] A/B testing framework for comparing LLM vs non-LLM
- [ ] Real-time feedback loop from confirmed assignments
- [ ] Advanced analytics dashboard
- [ ] Cost optimization strategies

## FAQ

**Q: Is the LLM required?**  
A: No! The system works fine without it, using heuristic scoring.

**Q: Which model should I use?**  
A: Start with `gpt-3.5-turbo` for cost-effectiveness. Upgrade to `gpt-4` if you need better reasoning.

**Q: How much does it cost?**  
A: Very little! Typically $0.007 per planning run with gpt-3.5-turbo.

**Q: Is my data secure?**  
A: Yes. OpenAI and Anthropic don't use API data for training. Set appropriate data retention policies.

**Q: Can I use local LLMs?**  
A: Not yet, but it's on the roadmap! You could integrate Ollama or similar.

**Q: Does it work offline?**  
A: No, requires internet for LLM API calls. Falls back to heuristics if offline.

## Support

For questions or issues:

1. Check logs: `docker-compose logs backend | grep LLM`
2. Review this guide
3. Check OpenAI status: https://status.openai.com
4. Contact the development team

## Conclusion

The LLM-powered volunteer queueing system brings AI intelligence to volunteer assignment, making the process smarter, more transparent, and more effective. It's a **highlighted feature** that showcases the power of combining traditional optimization with modern machine learning! 🚀

---

**Last Updated**: November 29, 2025  
**Version**: 1.0.0

