# Claude.md - Project Context

## About Me

**Background:** Business professional with Python/LLM experience
**Learning Goal:** Build real project to understand full-stack + ML/AI integration deeply
**Coding Style Preference:** Explanatory - I want to know WHY, not just WHAT

## How to Help Me

### 1. Use "Explanatory Output Style"

**Add insights explaining design decisions:**

```python
# ✅ GOOD - Explains WHY
async def check_channel(channel_id: str):
    """
    Why async? We'll check 10+ channels concurrently.
    Async lets Python check multiple channels simultaneously
    without blocking, making this 10x faster than sequential calls.
    """
    pass

# ❌ BAD - Just shows WHAT
async def check_channel(channel_id: str):
    """Check a channel for new videos."""
    pass
```

### 2. Explain Architecture Decisions

Before code, tell me:
- **What** we're building
- **Why** this approach over alternatives
- **Trade-offs** (simplicity vs scalability, cost vs quality)
- **How** it enables future ML features

**Example:**
> **Why SQLite instead of PostgreSQL now?**
>
> SQLite = zero config, perfect for MVP (<10K records). When we add ML (embeddings, recommendations), we'll migrate to PostgreSQL + pgvector extension. Migration is 1 day of work via SQLAlchemy (just change DATABASE_URL). For now, SQLite lets you focus on learning SQL without DevOps complexity.

### 3. Teach Me to Debug

When I hit errors:
1. Explain what error means
2. Show how to read stack trace
3. Suggest debug steps (logging, breakpoints)
4. Link to docs

**Example:**
> **Error:** `sqlalchemy.exc.IntegrityError: FOREIGN KEY constraint failed`
>
> **Meaning:** You're inserting an Episode with channel_id=5, but no channel with id=5 exists. Foreign keys enforce referential integrity.
>
> **Debug:**
> 1. Check: `SELECT * FROM channels WHERE id=5`
> 2. Fix: Create channel first, then episode
>
> **Learn more:** https://www.sqlitetutorial.net/sqlite-foreign-key/

### 4. Suggest Best Practices

Point out when code could be improved:
- Security (never hardcode secrets)
- Performance (N+1 queries, missing indexes)
- Code organization (when to extract functions)
- ML-readiness (track data for future models)

## Project Goals

###MVP (6 Weeks)
1. Monitor 5-10 YouTube channels
2. Auto-transcribe with free captions
3. Generate personalized summaries (Claude API)
4. Track user behavior (for future ML)

### Post-MVP (Future)
1. **ML Recommendations** (Month 3-6)
   - Collaborative filtering ("users like you also read...")
   - Content-based ("similar to episodes you liked")
   - See [TECH_DECISIONS.md](TECH_DECISIONS.md) for implementation plan

2. **Multi-User** (Month 7-9)
   - Auth, teams, public collections

3. **Advanced Features** (Month 10+)
   - Real-time recommendations
   - Email digests
   - Mobile app

## Technology Stack

**See [TECH_DECISIONS.md](TECH_DECISIONS.md) for full rationale.**

**TL;DR:**
- **FastAPI** → Async (ML-ready), type-safe, auto API docs
- **React** → Component reuse (many ML UI variations), largest ecosystem
- **SQLite→PostgreSQL** → Easy now, pgvector for embeddings later
- **Claude** → 200K context, $3/million tokens (10x cheaper than GPT-4)
- **APScheduler→Celery** → Simple now, distributed GPU workers later

## Coding Standards

### Python
- Type hints on all functions
- Async for I/O operations (DB, API calls)
- Docstrings with "Why" explanations
- Black formatter, Flake8 linter

### React
- Functional components + hooks (no classes)
- One component per file
- Extract reusable logic to custom hooks

### Database
- Foreign keys for referential integrity
- JSON columns for evolvable schemas (preferences, metadata)
- Design for future: user_id FKs everywhere (even in single-user MVP)

## ML-First Design Principles

**Key Insight:** Build for ML from day 1, even though we won't train models for 6 months.

1. **Track Everything** → user_interactions table logs all behavior
   - ML needs 6+ months of data
   - Start collecting NOW for models LATER

2. **Flexible Schemas** → JSON columns evolve without migrations
   ```python
   # NOW
   preferences = {"interests": ["tech", "ai"]}

   # LATER (no migration needed)
   preferences = {"interests": {"tech": 0.8, "ai": 0.95}, "vector": [...]}
   ```

3. **Embedding-Ready** → key_topics array → easily convert to vectors
   ```python
   # Add column later
   ALTER TABLE episodes ADD COLUMN embedding vector(768);
   ```

4. **Version Everything** → preferences_used field tracks what generated summaries
   - A/B testing ready
   - ML training labels

## Questions to Ask Before Implementing

1. **Scope:** MVP or save for later?
2. **Learning:** Should I implement or guide you through it?
3. **Design:** Approach A (simple) or B (scalable)?
4. **Debugging:** What have you tried? What's your hypothesis?

## Success Criteria

**I've learned enough when:**
- ✅ Can explain REST API design
- ✅ Can modify Claude prompts for different outputs
- ✅ Can add new API endpoints without help
- ✅ Can debug using logs + DevTools
- ✅ Can deploy to cloud

**MVP is complete when:**
- ✅ Add real YouTube channel → system auto-detects new episodes
- ✅ Summaries emphasize MY selected interests
- ✅ Can track which episodes I've read
- ✅ UI responsive on mobile
- ✅ Runs autonomously (no manual steps)

## Important Reminders for Claude

1. **Always explain WHY** - not just show code
2. **Encourage experimentation** - "Try changing X, see what happens"
3. **Celebrate progress** - "You just built your first async endpoint!"
4. **Ask before deciding** - "Do you want simple or scalable approach?"
5. **Reference docs** - Point to [TECH_DECISIONS.md](TECH_DECISIONS.md), [spec.md](spec.md), [todo.md](todo.md)

## Let's Build! 🚀

When in doubt, refer to:
- **[TECH_DECISIONS.md](TECH_DECISIONS.md)** → Why each technology
- **[spec.md](spec.md)** → API/DB technical details
- **[todo.md](todo.md)** → What to build next

Happy coding! 🎉
