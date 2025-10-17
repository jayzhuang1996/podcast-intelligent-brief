# Changelog

All notable changes to the AI Podcast Intelligent Briefing System.

## [2.0.0] - 2025-10-14

### 🎯 Major Overhaul: From "Summaries" to "Intelligent Briefings"

**Breaking Changes:**
- Removed `UserPreferences` table entirely
- `/api/preferences` endpoints removed
- API now requires `context` object (5 questions) for all briefing generation

### Added
- **GenerationContext Table** - Stores user's questionnaire answers per briefing
- **Two-Stage Prompting** - Separate system prompt + dynamic user prompt
- **Speaker Research** - Automatically extracts speaker backgrounds from transcripts
- **5-Question Questionnaire System:**
  - Q1: Motivation (why listening)
  - Q2: Depth level (how deep to go)
  - Q3: Reasoning mode (what lens: connect/challenge/apply/reflect)
  - Q4: Narrative tone (what voice)
  - Q5: Curiosity focus (optional steering)
- **Playful AI Voice** - Low-temperature, conversational briefing style
- **Context-Aware Caching** - Exact matching on all context fields

### Changed
- Renamed `generate_summary()` to `generate_briefing()`
- Updated all "summary" terminology to "briefing" throughout codebase
- API response now includes `briefing` instead of `summary`
- History endpoint now returns generation context with each briefing

### Removed
- `UserPreferences` model and table
- Static interests list
- Summary length option (short/medium/long)
- `/api/preferences` GET and PUT endpoints
- Generic dropdown options replaced with specific questions

### Technical Details
- **Model:** Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Max Tokens:** Increased to 4000 for comprehensive briefings
- **Prompt System:** ~100K char transcript + speaker context + user instructions
- **Database:** SQLite (production-ready for PostgreSQL migration)

### Files Modified
- `src/db/models.py` - New GenerationContext model
- `src/services/summarize.py` - Complete rewrite
- `src/api/summarize.py` - Context validation and storage
- `src/main.py` - Removed preferences router
- `scripts/init_db.py` - Simplified initialization

### Migration Guide

**If upgrading from v1.x:**
1. Backup your database: `cp data/podcast.db data/podcast.db.backup`
2. Run database migration: `python scripts/init_db.py`
3. Old summaries remain in database but won't have generation contexts
4. Frontend must be updated to collect and send context object

---

## [1.0.0] - 2025-10-12

### Initial Release - On-Demand Summarization

**Features:**
- Search YouTube by name
- Paste URL to summarize
- Interest-based personalization (tech, ai, business, etc.)
- Summary length control (short, medium, long)
- Smart caching (transcript + summary)
- User preferences storage

**Tech Stack:**
- FastAPI backend
- React frontend
- SQLite database
- Claude 3 Sonnet
- yt-dlp for YouTube integration

**Database Tables:**
- users
- user_preferences (interests, summary_length)
- episodes (videos with transcripts)
- summaries (generated outputs)
- user_interactions (behavior tracking)

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Types of Changes
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements
