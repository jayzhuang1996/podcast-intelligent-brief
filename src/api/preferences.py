"""
User preferences API.

Endpoints:
- GET /api/preferences - Get current preferences
- PUT /api/preferences - Update preferences
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from src.db.database import get_db
from src.db.models import UserPreferences
from loguru import logger

router = APIRouter()


# Available interest options
AVAILABLE_INTERESTS = [
    "tech",
    "ai",
    "business",
    "startups",
    "health",
    "science",
    "culture",
    "politics",
    "philosophy"
]


class PreferencesResponse(BaseModel):
    interests: List[str]
    summary_length: str
    available_interests: List[str]


class UpdatePreferencesRequest(BaseModel):
    interests: List[str]
    summary_length: str


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(db: Session = Depends(get_db)):
    """
    Get current user preferences.

    Returns interests and summary_length settings.
    """
    user_id = 1  # MVP: single user

    prefs = db.query(UserPreferences).filter_by(user_id=user_id).first()

    if not prefs:
        raise HTTPException(
            status_code=404,
            detail="Preferences not found. Run scripts/init_db.py to create default user."
        )

    logger.info(f"Fetched preferences: {prefs.interests}")

    return PreferencesResponse(
        interests=prefs.interests,
        summary_length=prefs.summary_length,
        available_interests=AVAILABLE_INTERESTS
    )


@router.put("/preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    db: Session = Depends(get_db)
):
    """
    Update user preferences.

    Args:
        interests: List of interest tags
        summary_length: "short", "medium", or "long"

    Returns:
        Updated preferences
    """
    user_id = 1  # MVP: single user

    # Validate interests
    invalid_interests = [i for i in request.interests if i not in AVAILABLE_INTERESTS]
    if invalid_interests:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interests: {invalid_interests}. Available: {AVAILABLE_INTERESTS}"
        )

    # Validate summary_length
    if request.summary_length not in ["short", "medium", "long"]:
        raise HTTPException(
            status_code=400,
            detail="summary_length must be 'short', 'medium', or 'long'"
        )

    # Update preferences
    prefs = db.query(UserPreferences).filter_by(user_id=user_id).first()

    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")

    prefs.interests = request.interests
    prefs.summary_length = request.summary_length
    db.commit()

    logger.info(f"Updated preferences: {prefs.interests}")

    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "interests": prefs.interests,
            "summary_length": prefs.summary_length
        },
        "note": "New summaries will use these preferences. Existing summaries unchanged."
    }
