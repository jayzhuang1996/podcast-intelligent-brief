# Technical Specification - Intelligent Briefing System v2.0

## Overview

**System:** Context-aware podcast briefing generation
**Architecture:** FastAPI backend + React frontend + SQLite database + Claude 3.5 Sonnet
**Core Feature:** User provides context via questionnaire → Get personalized, intelligent briefing

**Key Philosophy:**
- Not summaries (compression) → Briefings (curation + filtering)
- Not generic options → Specific questions about user's goals
- Not one-size-fits-all → Context drives everything
- Speaker research → Understand perspectives and biases

---

## User Flow (v2.0)

### New Flow with Questionnaire

```
User searches OR pastes URL
  ↓
User clicks "Generate Briefing"
  ↓
Questionnaire modal appears (5 questions):
  1. What draws you to this episode? (4 choices)
  2. How deep should we go? (3 choices)
  3. What lens should we bring? (4 choices)
  4. What voice feels right? (4 choices)
  5. Anything you're curious about? (optional text)
  ↓
User fills questionnaire (pre-filled from last time)
  ↓
Backend checks cache (same episode + same context?)
  ↓
If NO:
  - Extract video metadata
  - Download captions (if needed)
  - Research speakers from transcript
  - Generate briefing with context
  - Store generation_context + briefing
If YES:
  - Return cached briefing (instant)
  ↓
Display intelligent briefing with:
  - Speaker context
  - Filtered content (relevant to user's goal)
  - Applied lens (connect/challenge/apply/reflect)
  - Provocative discussion questions
```

---

## Database Schema (v2.0)

### Tables (4 tables)

```
users (1)
  ↓
generation_contexts (many) ← stores questionnaire answers
  ↓
summaries (many) ← one briefing per context
  ↓
episodes (many) ← video metadata + transcripts

users (1) → user_interactions (many) ← episodes (many)
```

**Key Changes from v1.0:**
- ❌ Removed `user_preferences` table
- ✅ Added `generation_contexts` table
- ✅ Context drives everything (no global preferences)

---

### Table: `users`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| email | VARCHAR(255) UNIQUE | For future multi-user |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**MVP:** Single user (id=1)

---

### Table: `generation_contexts` (NEW)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK→users.id | |
| episode_id | INTEGER FK→episodes.id | |
| summary_id | INTEGER FK→summaries.id | Links to generated briefing |
| motivation | VARCHAR(50) | Q1: Why listening |
| depth_level | VARCHAR(50) | Q2: How deep |
| reasoning_mode | VARCHAR(50) | Q3: What lens |
| narrative_tone | VARCHAR(50) | Q4: What voice |
| curiosity_focus | TEXT NULL | Q5: Optional steering |
| created_at | TIMESTAMP | |

**Valid Values:**
- `motivation`: "topic_interesting", "speaker_perspective", "personal_connection", "cultural_relevance"
- `depth_level`: "essence", "balanced", "deep"
- `reasoning_mode`: "connect", "challenge", "apply", "reflect"
- `narrative_tone`: "analytical", "conversational", "thoughtful", "provocative"

**Purpose:** Enables experimentation (same episode, different contexts = different briefings)

---

### Table: `episodes`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| video_id | VARCHAR(255) UNIQUE | YouTube video ID |
| channel_name | VARCHAR(255) | Extracted from YouTube |
| title | VARCHAR(500) | |
| description | TEXT | |
| published_at | TIMESTAMP | |
| duration | INTEGER | Seconds |
| thumbnail_url | VARCHAR(500) | |
| video_url | VARCHAR(500) | |
| transcript | TEXT | Full caption text |
| created_at | TIMESTAMP | When first summarized |

**Note:** No `channel_id` FK because we don't track channels in MVP.

---

### Table: `summaries`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| episode_id | INTEGER FK→episodes.id | |
| user_id | INTEGER FK→users.id | |
| summary_text | TEXT | Markdown |
| key_topics | JSON | `["AI", "regulation"]` |
| preferences_used | JSON | Snapshot of preferences |
| token_count | INTEGER | Cost tracking |
| generation_time | FLOAT | Seconds |
| created_at | TIMESTAMP | |

**Caching Strategy:**
- Same episode + same interests → reuse summary (instant)
- Same episode + different interests → generate new summary

---

### Table: `user_interactions`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK→users.id | |
| episode_id | INTEGER FK→episodes.id | |
| action_type | VARCHAR(50) | "search"/"view"/"read" |
| metadata | JSON | `{"search_query": "joe rogan", "time_spent": 120}` |
| created_at | TIMESTAMP | |

**Purpose:** Track searches to identify popular podcasts (for future monitoring feature)

---

## API Endpoints (Simplified MVP)

### Search & Summarize

#### `GET /api/search?q=joe+rogan`
Search YouTube for podcasts by name.

**Request:**
```
GET /api/search?q=joe+rogan&limit=5
```

**Response (200):**
```json
{
  "results": [
    {
      "video_id": "abc123",
      "title": "Joe Rogan Experience #2049 - Elon Musk",
      "channel_name": "PowerfulJRE",
      "thumbnail_url": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
      "duration": 10800,
      "published_at": "2024-10-10T08:00:00Z",
      "already_summarized": true  // Check if in cache
    },
    {
      "video_id": "def456",
      "title": "Joe Rogan Experience #2048 - Neil deGrasse Tyson",
      "already_summarized": false
    }
  ]
}
```

**Implementation:**
```python
import subprocess
import json

def search_youtube(query: str, limit: int = 5):
    """
    Use yt-dlp to search YouTube.

    Why yt-dlp instead of YouTube Data API?
    - No API key required (free)
    - No quota limits
    - Returns same data
    """
    cmd = [
        'yt-dlp',
        f'ytsearch{limit}:{query}',
        '--dump-json',
        '--skip-download'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    videos = []

    for line in result.stdout.strip().split('\n'):
        data = json.loads(line)
        videos.append({
            'video_id': data['id'],
            'title': data['title'],
            'channel_name': data['uploader'],
            'thumbnail_url': data['thumbnail'],
            'duration': data['duration'],
            'published_at': data['upload_date']
        })

    return videos
```

---

#### `POST /api/summarize`
Generate summary for a YouTube video (by URL or video_id).

**Request:**
```json
{
  "video_url": "https://youtube.com/watch?v=abc123",
  // OR
  "video_id": "abc123",

  // Optional: override user's default preferences
  "interests": ["tech", "ai"]  // If not provided, use user's saved preferences
}
```

**Response (200) - 60 seconds on first call:**
```json
{
  "episode": {
    "video_id": "abc123",
    "title": "Joe Rogan Experience #2049 - Elon Musk",
    "channel_name": "PowerfulJRE",
    "duration": 10800,
    "published_at": "2024-10-10T08:00:00Z"
  },
  "summary": {
    "summary_text": "## Tech-Focused Summary\n\n### Key Insights\n...",
    "key_topics": ["AI", "SpaceX", "Tesla", "Twitter/X"],
    "preferences_used": {"interests": ["tech", "ai"]},
    "cached": false  // true if returned from cache
  },
  "cost": {
    "tokens_used": 25000,
    "estimated_cost_usd": 0.075
  }
}
```

**Response (200) - Instant on cache hit:**
```json
{
  // ... same as above
  "summary": {
    "cached": true  // ⚡ Instant!
  }
}
```

**Implementation Flow:**
```python
@router.post("/summarize")
async def summarize_video(request: SummarizeRequest, db: Session = Depends(get_db)):
    # 1. Extract video_id from URL or use provided video_id
    video_id = extract_video_id(request.video_url) if request.video_url else request.video_id

    # 2. Get user preferences (use provided or fetch from DB)
    interests = request.interests or get_user_preferences(db, user_id=1).interests

    # 3. Check cache: Do we have a summary with same/similar preferences?
    cached_summary = find_cached_summary(db, video_id, interests)
    if cached_summary:
        return {"cached": True, "summary": cached_summary, ...}

    # 4. Check if episode metadata exists (avoid re-fetching)
    episode = db.query(Episode).filter_by(video_id=video_id).first()
    if not episode:
        # Fetch metadata from YouTube
        metadata = get_video_metadata(video_id)
        episode = Episode(**metadata)
        db.add(episode)
        db.commit()

    # 5. Download captions if not already downloaded
    if not episode.transcript:
        transcript = download_captions(video_id)  # 30 seconds
        episode.transcript = transcript
        db.commit()

    # 6. Generate personalized summary with Claude
    summary_text = generate_summary(
        transcript=episode.transcript,
        interests=interests,
        summary_length="medium"
    )  # 30 seconds

    # 7. Extract key topics from summary
    key_topics = extract_topics(summary_text)

    # 8. Save summary to database (for future caching)
    summary = Summary(
        episode_id=episode.id,
        user_id=1,
        summary_text=summary_text,
        key_topics=key_topics,
        preferences_used={"interests": interests},
        token_count=count_tokens(episode.transcript, summary_text)
    )
    db.add(summary)
    db.commit()

    # 9. Track user interaction (for analytics)
    interaction = UserInteraction(
        user_id=1,
        episode_id=episode.id,
        action_type="summarize",
        metadata={"interests": interests}
    )
    db.add(interaction)
    db.commit()

    return {"cached": False, "summary": summary_text, ...}
```

**Why this is smart:**
- First user requesting episode pays full cost (60s)
- Subsequent users with same interests get instant results (cached)
- Different interests = new summary generated
- Transcript cached separately (only download once)

---

### Preferences

#### `GET /api/preferences`
Get current user preferences.

**Response (200):**
```json
{
  "interests": ["tech", "ai", "business"],
  "summary_length": "medium",
  "available_interests": ["tech", "ai", "business", "health", "science", "culture", "politics", "philosophy"]
}
```

---

#### `PUT /api/preferences`
Update preferences.

**Request:**
```json
{
  "interests": ["tech", "ai"],
  "summary_length": "long"
}
```

**Response (200):**
```json
{
  "message": "Preferences updated",
  "preferences": {"interests": ["tech", "ai"], "summary_length": "long"}
}
```

---

### History

#### `GET /api/history`
View previously summarized episodes (user's history).

**Response (200):**
```json
{
  "episodes": [
    {
      "id": 42,
      "title": "Joe Rogan Experience #2049",
      "channel_name": "PowerfulJRE",
      "thumbnail_url": "...",
      "summarized_at": "2024-10-12T15:30:00Z",
      "key_topics": ["AI", "SpaceX"]
    }
  ]
}
```

**Implementation:** `SELECT * FROM episodes JOIN summaries WHERE user_id=1 ORDER BY created_at DESC`

---

## Frontend Design (MVP)

### Main Page: Search Interface

```jsx
// frontend/src/pages/Dashboard.jsx

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function Dashboard() {
  const [searchMode, setSearchMode] = useState('search'); // 'search' or 'url'
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);

  // Search YouTube
  const handleSearch = async () => {
    setLoading(true);
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=5`);
    const data = await response.json();
    setSearchResults(data.results);
    setLoading(false);
  };

  // Summarize episode
  const handleSummarize = async (videoId) => {
    setLoading(true);
    setSummary(null);

    const response = await fetch('/api/summarize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ video_id: videoId })
    });

    const data = await response.json();
    setSummary(data);
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Podcast Summarizer</h1>

      {/* Toggle: Search vs Paste URL */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setSearchMode('search')}
          className={searchMode === 'search' ? 'font-bold' : ''}
        >
          🔍 Search
        </button>
        <button
          onClick={() => setSearchMode('url')}
          className={searchMode === 'url' ? 'font-bold' : ''}
        >
          🔗 Paste URL
        </button>
      </div>

      {/* Input */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          placeholder={searchMode === 'search' ? 'Search: "Joe Rogan"' : 'Paste YouTube URL'}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 px-4 py-2 border rounded"
        />
        <button
          onClick={searchMode === 'search' ? handleSearch : () => handleSummarize(extractVideoId(query))}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Loading...' : searchMode === 'search' ? 'Search' : 'Summarize'}
        </button>
      </div>

      {/* Search Results */}
      {searchMode === 'search' && searchResults.length > 0 && (
        <div className="space-y-4 mb-6">
          <h2 className="text-xl font-semibold">Results:</h2>
          {searchResults.map((result) => (
            <div key={result.video_id} className="border p-4 rounded flex gap-4">
              <img src={result.thumbnail_url} alt="" className="w-40 h-24 object-cover rounded" />
              <div className="flex-1">
                <h3 className="font-semibold">{result.title}</h3>
                <p className="text-sm text-gray-600">{result.channel_name}</p>
                <p className="text-sm text-gray-500">{formatDuration(result.duration)} • {formatDate(result.published_at)}</p>
                <button
                  onClick={() => handleSummarize(result.video_id)}
                  className="mt-2 px-4 py-1 bg-green-600 text-white rounded text-sm"
                >
                  {result.already_summarized ? '⚡ View Summary (cached)' : '📝 Generate Summary (60s)'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading State */}
      {loading && !summary && (
        <div className="text-center py-12">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-lg">
            {summary?.cached ? 'Loading from cache...' : 'Generating personalized summary (60 seconds)...'}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Downloading captions → Sending to Claude → Extracting key topics
          </p>
        </div>
      )}

      {/* Summary Display */}
      {summary && (
        <div className="border rounded p-6">
          {summary.summary.cached && (
            <div className="bg-green-100 border border-green-400 rounded p-2 mb-4 text-sm">
              ⚡ Loaded from cache (instant)
            </div>
          )}

          <div className="flex gap-4 mb-4">
            <img src={summary.episode.thumbnail_url} alt="" className="w-60 h-36 object-cover rounded" />
            <div>
              <h2 className="text-2xl font-bold">{summary.episode.title}</h2>
              <p className="text-gray-600">{summary.episode.channel_name}</p>
              <p className="text-sm text-gray-500">
                {formatDuration(summary.episode.duration)} • {formatDate(summary.episode.published_at)}
              </p>
            </div>
          </div>

          {/* Key Topics */}
          <div className="mb-4">
            <h3 className="font-semibold mb-2">Key Topics:</h3>
            <div className="flex flex-wrap gap-2">
              {summary.summary.key_topics.map((topic) => (
                <span key={topic} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                  {topic}
                </span>
              ))}
            </div>
          </div>

          {/* Summary Text */}
          <div className="prose max-w-none">
            <ReactMarkdown>{summary.summary.summary_text}</ReactMarkdown>
          </div>

          {/* Cost Info (for your tracking) */}
          <div className="mt-4 text-xs text-gray-500">
            Tokens used: {summary.cost.tokens_used.toLocaleString()} •
            Cost: ${summary.cost.estimated_cost_usd.toFixed(3)}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
function extractVideoId(url) {
  // Extract video ID from URL
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
  return match ? match[1] : url;
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString();
}

export default Dashboard;
```

---

## Backend Implementation Guide

### File Structure (Simplified)

```
src/
├── main.py              # FastAPI app
├── api/
│   ├── search.py        # Search endpoint
│   ├── summarize.py     # Summarize endpoint
│   └── preferences.py   # Preferences endpoints
├── services/
│   ├── youtube.py       # yt-dlp wrapper (search, metadata, captions)
│   ├── summarize.py     # Claude API integration
│   └── cache.py         # Smart caching logic
├── db/
│   ├── database.py      # SQLAlchemy setup
│   └── models.py        # 4 tables: users, preferences, episodes, summaries
└── utils/
    └── helpers.py       # Video ID extraction, token counting
```

---

### Key Services

#### `src/services/youtube.py`

```python
import subprocess
import json
from typing import List, Dict, Optional

def search_youtube(query: str, limit: int = 5) -> List[Dict]:
    """
    Search YouTube using yt-dlp.

    Why this works:
    - yt-dlp has built-in search: ytsearch{N}:{query}
    - Returns JSON with all metadata
    - No API key required
    """
    cmd = [
        'yt-dlp',
        f'ytsearch{limit}:{query}',
        '--dump-json',
        '--skip-download',
        '--no-warnings'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    videos = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        data = json.loads(line)
        videos.append({
            'video_id': data['id'],
            'title': data['title'],
            'channel_name': data['uploader'],
            'thumbnail_url': data['thumbnail'],
            'duration': data['duration'],
            'published_at': data['upload_date'],
            'video_url': data['webpage_url']
        })

    return videos


def get_video_metadata(video_id: str) -> Dict:
    """Fetch metadata for single video."""
    cmd = [
        'yt-dlp',
        f'https://youtube.com/watch?v={video_id}',
        '--dump-json',
        '--skip-download'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)

    return {
        'video_id': data['id'],
        'title': data['title'],
        'channel_name': data['uploader'],
        'description': data.get('description', ''),
        'thumbnail_url': data['thumbnail'],
        'duration': data['duration'],
        'published_at': data['upload_date'],
        'video_url': data['webpage_url']
    }


def download_captions(video_id: str) -> Optional[str]:
    """
    Download and clean auto-generated captions.

    Returns plain text transcript (30 seconds).
    """
    cmd = [
        'yt-dlp',
        f'https://youtube.com/watch?v={video_id}',
        '--skip-download',
        '--write-auto-sub',
        '--sub-lang', 'en',
        '--sub-format', 'vtt',
        '--output', f'/tmp/{video_id}',
        '--no-warnings'
    ]

    subprocess.run(cmd, capture_output=True, timeout=60)

    # Read VTT file
    vtt_path = f'/tmp/{video_id}.en.vtt'
    try:
        with open(vtt_path, 'r') as f:
            content = f.read()

        # Clean VTT format (remove timestamps, formatting)
        transcript = clean_vtt(content)
        return transcript
    except FileNotFoundError:
        return None  # No captions available


def clean_vtt(vtt_content: str) -> str:
    """Remove VTT timestamps and formatting."""
    lines = []
    for line in vtt_content.split('\n'):
        # Skip timestamps (00:00:00.000 --> 00:00:05.000)
        if '-->' in line:
            continue
        # Skip WEBVTT header
        if line.startswith('WEBVTT') or line.startswith('Kind:'):
            continue
        # Skip empty lines
        if not line.strip():
            continue
        lines.append(line.strip())

    return ' '.join(lines)
```

---

#### `src/services/summarize.py`

```python
from anthropic import Anthropic
from typing import List

client = Anthropic(api_key="your-api-key")

def generate_summary(
    transcript: str,
    interests: List[str],
    summary_length: str = "medium"
) -> str:
    """
    Generate personalized summary with Claude.

    Takes 30 seconds, costs ~$0.05 per 3-hour podcast.
    """

    # Build personalized prompt
    prompt = build_prompt(transcript, interests, summary_length)

    # Call Claude API
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    summary_text = response.content[0].text

    return summary_text


def build_prompt(transcript: str, interests: List[str], length: str) -> str:
    """
    Build personalized prompt emphasizing user interests.

    Why this matters:
    - Same transcript + different interests = different summaries
    - Personalization happens in prompt, not post-processing
    """

    interest_str = ", ".join(interests)

    length_guidance = {
        "short": "500-800 words",
        "medium": "1000-1500 words",
        "long": "2000-3000 words"
    }[length]

    prompt = f"""You are summarizing a podcast episode for someone interested in: {interest_str}.

TRANSCRIPT:
{transcript[:100000]}  # Truncate to fit context window

INSTRUCTIONS:
1. Write a {length_guidance} summary focusing on aspects related to: {interest_str}
2. Structure:
   - Brief overview (2-3 sentences)
   - Key insights (focus on {interest_str} topics)
   - Notable quotes or examples
   - Takeaways relevant to someone interested in {interest_str}

3. Format as Markdown with headers (##, ###)

4. At the end, list 5-7 key topics as a JSON array:
   KEY_TOPICS: ["topic1", "topic2", ...]

Begin your summary:"""

    return prompt


def extract_topics(summary_text: str) -> List[str]:
    """Extract key topics from summary (looks for KEY_TOPICS: [...] in text)."""
    import re
    match = re.search(r'KEY_TOPICS:\s*(\[.*?\])', summary_text, re.DOTALL)
    if match:
        import json
        return json.loads(match.group(1))
    return []
```

---

#### `src/services/cache.py`

```python
from sqlalchemy.orm import Session
from src.db.models import Summary, Episode
from typing import List, Optional

def find_cached_summary(
    db: Session,
    video_id: str,
    interests: List[str]
) -> Optional[dict]:
    """
    Check if we have a cached summary matching these preferences.

    Strategy:
    - Exact match: Same video + same interests → return immediately
    - Partial match: Same video + overlapping interests (80%+) → return (good enough)
    - No match: Return None (need to generate new summary)
    """

    # Get episode
    episode = db.query(Episode).filter_by(video_id=video_id).first()
    if not episode:
        return None

    # Find summaries for this episode
    summaries = db.query(Summary).filter_by(episode_id=episode.id).all()

    if not summaries:
        return None

    # Check for exact match
    for summary in summaries:
        cached_interests = summary.preferences_used.get('interests', [])
        if set(cached_interests) == set(interests):
            return {
                'summary_text': summary.summary_text,
                'key_topics': summary.key_topics,
                'preferences_used': summary.preferences_used
            }

    # Check for partial match (80%+ overlap)
    for summary in summaries:
        cached_interests = summary.preferences_used.get('interests', [])
        overlap = len(set(cached_interests) & set(interests))
        if overlap / len(interests) >= 0.8:
            return {
                'summary_text': summary.summary_text,
                'key_topics': summary.key_topics,
                'preferences_used': summary.preferences_used,
                'partial_match': True  # Let user know it's not exact
            }

    return None
```

---

## Milestones (Revised for On-Demand MVP)

### Milestone 1: Basic Backend + UI (Week 1)

**Goal:** Paste URL → Get summary

**Tasks:**
- [ ] Set up FastAPI + SQLite (4 tables: users, preferences, episodes, summaries)
- [ ] Implement `/api/summarize` endpoint
- [ ] Integrate yt-dlp (download captions)
- [ ] Integrate Claude API (generate summary)
- [ ] Build simple React UI (input box + summary display)

**Success:** Paste Joe Rogan URL → See summary in 60 seconds

---

### Milestone 2: Search + Caching (Week 2)

**Goal:** Search "Joe Rogan" → Pick episode → Get summary (with caching)

**Tasks:**
- [ ] Implement `/api/search` endpoint (yt-dlp search)
- [ ] Add caching logic (check DB before generating)
- [ ] Update UI (toggle search vs URL, show search results)
- [ ] Add "cached" indicator in UI

**Success:**
- Search works, returns 5 results
- First user: 60s to generate
- Second user (same episode): instant (cached)

---

### Milestone 3: Personalization + Polish (Week 3)

**Goal:** Different interests → Different summaries

**Tasks:**
- [ ] Add preferences page (select interests)
- [ ] Update prompt to emphasize interests
- [ ] Extract key topics, display as tags
- [ ] Add history page (previously summarized episodes)
- [ ] Mobile responsive design

**Success:**
- Tech interests → tech-focused summary
- Business interests → business-focused summary
- History shows all my summaries

---

## Cost Analysis (On-Demand MVP)

### Scenario 1: You Testing (1 User, 20 Episodes)

**Assumptions:**
- You summarize 20 different episodes
- No caching benefit (all unique)

**Cost:**
- 20 episodes × $0.05/episode = **$1.00**

---

### Scenario 2: 100 Users (80/20 Rule)

**Assumptions:**
- 100 users request 500 total summaries
- 80% concentrate on 20 popular podcasts (Rogan, Lex, Huberman)
- 20% are long-tail (unique episodes)

**Calculation:**
- 80% (400 summaries) → ~50 unique episodes (80/20 within popular podcasts)
- 20% (100 summaries) → 100 unique episodes

**Total unique episodes:** 150
**Total API cost:** 150 × $0.05 = **$7.50/month**

**Without caching:** 500 × $0.05 = $25/month
**Savings:** $17.50/month (70% reduction!)

---

### Scenario 3: 10K Users (Your Vision)

**Assumptions:**
- 10K users request 50K summaries/month
- 80/20 rule applies (80% focus on ~200 popular episodes)

**Calculation:**
- 80% (40K summaries) → ~500 unique episode-interest combinations
- 20% (10K summaries) → 10K unique episodes

**Total unique generations:** 10,500
**Total API cost:** 10,500 × $0.05 = **$525/month**

**Without caching:** 50K × $0.05 = $2,500/month
**Savings:** $1,975/month (79% reduction!)

---

## When to Add Background Monitoring

**Watch your analytics:** Track user_interactions table

```sql
-- Find most-requested podcasts
SELECT channel_name, COUNT(*) as request_count
FROM episodes e
JOIN summaries s ON e.id = s.episode_id
GROUP BY channel_name
ORDER BY request_count DESC
LIMIT 20;
```

**Add monitoring when:**
- Same channel requested 50+ times
- Same episode requested by multiple users within 24 hours

**How to add (Week 5-6):**
1. Add "favorite channels" feature
2. Background job checks favorites daily (not every 6 hours!)
3. Precomputes summaries overnight
4. Users see instant results next morning

**Cost benefit:** Precompute top 20 podcasts = $1/day, saves 200 user-initiated requests = $10/day saved

---

## Next Steps

Ready to start building? Your next actions:

1. ✅ **Setup environment** (5 minutes)
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. ✅ **Create database** (2 minutes)
   ```bash
   python scripts/init_db.py
   ```

3. ✅ **Test yt-dlp** (1 minute)
   ```bash
   yt-dlp "ytsearch1:joe rogan" --dump-json --skip-download
   ```

4. ✅ **Build `/api/summarize` endpoint** (2 hours)
   - See `src/services/youtube.py` above
   - See `src/services/summarize.py` above

5. ✅ **Build simple UI** (2 hours)
   - See frontend code above

**Total time to working MVP: 1 week**

Want me to help you start with any of these steps?

---

**Last Updated:** 2024-10-12
