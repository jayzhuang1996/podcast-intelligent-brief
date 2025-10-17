# AI Podcast - Intelligent Briefing System

Transform podcast episodes into personalized, context-aware briefings powered by Claude AI.

**Not just summaries** - intelligent curation that filters content based on your specific goals, applies different analytical lenses, and provokes deeper thinking.

**Tech:** FastAPI + React + SQLite + Claude 3.5 Sonnet
**Status:** Backend complete, Frontend questionnaire needed

---

## Quick Start

### Backend Setup (2 minutes)

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add ANTHROPIC_API_KEY from console.anthropic.com

# Initialize database
python scripts/init_db.py

# Run server
uvicorn src.main:app --reload
```

**API Running:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Frontend Setup (2 minutes)

```bash
cd frontend
npm install
npm run dev
```

**UI Running:** http://localhost:3000

---

## How It Works

1. **User provides context** via 5-question questionnaire:
   - Why are you listening to this?
   - How deep should we go?
   - What lens should we apply? (connect/challenge/apply/reflect)
   - What voice/tone do you prefer?
   - Any specific curiosity?

2. **AI researches speakers** from transcript (backgrounds, perspectives, biases)

3. **Generates intelligent briefing** that:
   - Filters content relevant to user's specific goal
   - Applies chosen analytical lens
   - Uses requested narrative tone
   - Ends with provocative discussion questions

---

## Current Status

✅ **Backend Complete**
- New database schema with `generation_contexts` table
- Two-stage prompting (system + dynamic user prompts)
- Speaker research from transcripts
- Context-aware caching
- API ready to accept questionnaire data

❌ **Frontend Needed**
- 5-question questionnaire modal (before generation)
- Context submission to API
- Remember last context (localStorage)

---

## Documentation

| File | Purpose |
|------|---------|
| **[spec.md](spec.md)** | Technical specs: API endpoints, database schema, prompt system |
| **[claude.md](claude.md)** | AI assistant context (how to help you learn) |
| **[todo.md](todo.md)** | Current task status and next steps |
| **[CHANGELOG.md](CHANGELOG.md)** | History of major changes |

---

## API Example

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=VIDEO_ID",
    "context": {
      "motivation": "topic_interesting",
      "depth_level": "balanced",
      "reasoning_mode": "connect",
      "narrative_tone": "conversational",
      "curiosity_focus": "What makes this perspective unique?"
    }
  }'
```

---

## Development

```bash
# Run backend (terminal 1)
source .venv/bin/activate && uvicorn src.main:app --reload

# Run frontend (terminal 2)
cd frontend && npm run dev

# Test
pytest                        # Backend tests
black src/ && flake8 src/    # Lint Python
```

---

## Next Steps

1. **Read [spec.md](spec.md)** → Understand the new prompt system & API
2. **Build questionnaire** → Frontend component that collects 5 answers
3. **Test API** → Use Swagger docs at http://localhost:8000/docs

---

**License:** MIT
