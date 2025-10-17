"""
Summarize API endpoints.

Main endpoints:
- POST /api/summarize - Generate intelligent briefing for YouTube video
- GET /api/search - Search YouTube by name
- GET /api/history - View previously generated briefings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import time

from src.db.database import get_db
from src.db.models import Episode, Summary, GenerationContext, UserInteraction
from src.services.youtube import extract_video_id, get_video_metadata, download_captions, search_youtube
from src.services.summarize import generate_briefing
from loguru import logger

router = APIRouter()


# Request/Response models
class GenerationContextRequest(BaseModel):
    """User's questionnaire answers"""
    motivation: str  # Q1: Why listening
    depth_level: str  # Q2: How deep
    reasoning_mode: str  # Q3: What lens
    narrative_tone: str  # Q4: What voice
    curiosity_focus: Optional[str] = None  # Q5: Optional steering


class SummarizeRequest(BaseModel):
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    context: GenerationContextRequest  # Required context


class EpisodeResponse(BaseModel):
    video_id: str
    title: str
    channel_name: str
    duration: int
    published_at: str
    thumbnail_url: str
    video_url: str


class BriefingResponse(BaseModel):
    briefing_text: str
    context_used: dict
    cached: bool


class SummarizeResponse(BaseModel):
    episode: EpisodeResponse
    briefing: BriefingResponse
    cost: dict


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_video(
    request: SummarizeRequest,
    db: Session = Depends(get_db)
):
    """
    Generate intelligent briefing for a YouTube video.

    User flow:
    1. User fills questionnaire (context)
    2. Backend extracts video_id
    3. Check cache (already generated with same context?)
    4. If not cached: Download captions → Generate briefing → Store context
    5. Return briefing

    Takes 60 seconds on first request, instant on cache hit.
    """
    start_time = time.time()

    # Extract video ID
    if request.video_url:
        video_id = extract_video_id(request.video_url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    elif request.video_id:
        video_id = request.video_id
    else:
        raise HTTPException(status_code=400, detail="Must provide video_url or video_id")

    logger.info(f"Briefing request for video: {video_id}")

    # Validate context (all required fields present)
    context = request.context
    if not all([context.motivation, context.depth_level, context.reasoning_mode, context.narrative_tone]):
        raise HTTPException(status_code=400, detail="All context fields are required except curiosity_focus")

    user_id = 1  # MVP: single user

    logger.info(f"Using context: {context.dict()}")

    # Check cache
    episode = db.query(Episode).filter_by(video_id=video_id).first()

    if episode:
        # Check if we have a briefing with same context
        cached_context = find_cached_context(db, episode.id, context.dict())
        if cached_context:
            logger.info(f"Cache hit! Returning cached briefing")

            cached_summary = db.query(Summary).filter_by(id=cached_context.summary_id).first()

            return SummarizeResponse(
                episode=EpisodeResponse(
                    video_id=episode.video_id,
                    title=episode.title,
                    channel_name=episode.channel_name,
                    duration=episode.duration,
                    published_at=str(episode.published_at),
                    thumbnail_url=episode.thumbnail_url,
                    video_url=episode.video_url
                ),
                briefing=BriefingResponse(
                    briefing_text=cached_summary.summary_text,
                    context_used=context.dict(),
                    cached=True
                ),
                cost={
                    "tokens_used": 0,
                    "estimated_cost_usd": 0.0,
                    "note": "Cached briefing (free)"
                }
            )

    # Not cached - generate new briefing
    logger.info("Cache miss - generating new briefing")

    # Fetch metadata if needed
    if not episode:
        logger.info("Fetching video metadata...")
        metadata = get_video_metadata(video_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found or unavailable")

        episode = Episode(
            video_id=metadata['video_id'],
            channel_name=metadata['channel_name'],
            title=metadata['title'],
            description=metadata['description'],
            published_at=datetime.now(),  # Simplified for MVP
            duration=metadata['duration'],
            thumbnail_url=metadata['thumbnail_url'],
            video_url=metadata['video_url']
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)

    # Download captions if needed
    if not episode.transcript:
        logger.info("Downloading captions...")
        transcript = download_captions(video_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="No captions available for this video")

        episode.transcript = transcript
        db.commit()

    # Generate briefing
    logger.info("Generating briefing with Claude...")
    briefing_text, token_count = generate_briefing(
        transcript=episode.transcript,
        context=context.dict()
    )

    # Save summary
    summary_obj = Summary(
        episode_id=episode.id,
        user_id=user_id,
        summary_text=briefing_text,
        key_topics=[],  # No longer extracting topics separately
        preferences_used=context.dict(),
        token_count=token_count,
        generation_time=time.time() - start_time
    )
    db.add(summary_obj)
    db.commit()
    db.refresh(summary_obj)

    # Save generation context
    gen_context = GenerationContext(
        user_id=user_id,
        episode_id=episode.id,
        summary_id=summary_obj.id,
        motivation=context.motivation,
        depth_level=context.depth_level,
        reasoning_mode=context.reasoning_mode,
        narrative_tone=context.narrative_tone,
        curiosity_focus=context.curiosity_focus
    )
    db.add(gen_context)

    # Track interaction
    interaction = UserInteraction(
        user_id=user_id,
        episode_id=episode.id,
        action_type="briefing",
        interaction_metadata=context.dict()
    )
    db.add(interaction)

    db.commit()

    # Calculate cost
    input_cost = (token_count * 0.003) / 1000  # $3 per million input tokens
    output_cost = (1000 * 0.015) / 1000  # Estimate 1K output tokens
    total_cost = input_cost + output_cost

    logger.info(f"Briefing generated in {time.time() - start_time:.1f}s")

    return SummarizeResponse(
        episode=EpisodeResponse(
            video_id=episode.video_id,
            title=episode.title,
            channel_name=episode.channel_name,
            duration=episode.duration,
            published_at=str(episode.published_at),
            thumbnail_url=episode.thumbnail_url,
            video_url=episode.video_url
        ),
        briefing=BriefingResponse(
            briefing_text=briefing_text,
            context_used=context.dict(),
            cached=False
        ),
        cost={
            "tokens_used": token_count,
            "estimated_cost_usd": round(total_cost, 4),
            "note": "First generation cost"
        }
    )


def find_cached_context(db: Session, episode_id: int, context: dict) -> Optional[GenerationContext]:
    """
    Find cached briefing with matching context.

    Strategy:
    - Exact match on all context fields → return immediately
    - No partial matching (contexts are specific to user needs)
    """
    return db.query(GenerationContext).filter_by(
        episode_id=episode_id,
        motivation=context['motivation'],
        depth_level=context['depth_level'],
        reasoning_mode=context['reasoning_mode'],
        narrative_tone=context['narrative_tone'],
        curiosity_focus=context.get('curiosity_focus')
    ).first()


@router.get("/search")
async def search_videos(q: str, limit: int = 5):
    """
    Search YouTube by name.

    Args:
        q: Search query (e.g., "joe rogan")
        limit: Number of results (default 5)

    Returns:
        List of video results with metadata
    """
    logger.info(f"Search request: {q}")

    videos = search_youtube(q, limit=limit)

    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")

    return {"results": videos}


@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    """
    Get user's briefing history.

    Returns episodes they've previously generated briefings for.
    """
    user_id = 1  # MVP: single user

    summaries = (
        db.query(Summary)
        .filter_by(user_id=user_id)
        .order_by(Summary.created_at.desc())
        .limit(50)
        .all()
    )

    results = []
    for summary in summaries:
        episode = db.query(Episode).filter_by(id=summary.episode_id).first()
        if episode:
            # Get the generation context for this briefing
            gen_context = db.query(GenerationContext).filter_by(summary_id=summary.id).first()

            results.append({
                "id": episode.id,
                "video_id": episode.video_id,
                "title": episode.title,
                "channel_name": episode.channel_name,
                "thumbnail_url": episode.thumbnail_url,
                "generated_at": str(summary.created_at),
                "context": {
                    "motivation": gen_context.motivation if gen_context else None,
                    "depth_level": gen_context.depth_level if gen_context else None,
                    "reasoning_mode": gen_context.reasoning_mode if gen_context else None,
                    "narrative_tone": gen_context.narrative_tone if gen_context else None
                } if gen_context else None
            })

    return {"episodes": results}
