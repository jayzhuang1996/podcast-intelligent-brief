"""
Claude API integration for generating intelligent briefings.

Why Claude?
- 200K context window (fits full 3-hour podcast transcripts)
- $3 per million tokens (cost-effective)
- Superior instruction following for personalized briefings

New Architecture:
- Two-stage prompting: SYSTEM_PROMPT (role) + USER_PROMPT (context)
- Speaker research: Extract context from transcript
- Dynamic prompt building: Map questionnaire answers to instructions
"""

from anthropic import Anthropic
from typing import Dict, Tuple
import os
import json
from loguru import logger

# Initialize Claude client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# System Prompt: Defines AI's role (static, playful voice)
SYSTEM_PROMPT = """You are an intelligent briefing assistant who transforms podcast conversations into rich, substantive briefings that save time while deepening understanding.

Your purpose is to help someone engage deeply with a podcast episode by:
- FILTERING: Extract what matters based on their listening intent
- CONTEXTUALIZING: Weave in who's speaking, what shapes their view, and what they might be missing
- CONNECTING: Draw threads between ideas, or challenge assumptions where needed
- PROVOKING: Surface questions and tensions that spark genuine thinking

Your voice should be:
- Playful but smart (never dumbed down)
- Low temperature (precise, not flowery)
- Human-readable (like a smart friend explaining, not an AI summarizing)
- Curious and slightly provocative (make them want to engage)

CRITICAL: You will receive specific length requirements based on the depth requested. Respect these requirements — your briefing must be substantive and thorough. Shallow summaries are unacceptable. Take your time to explore ideas properly.

Structure your output in EXACTLY 2 sections:
1. Key Takeaways (3-5 bullet points)
2. Main briefing (the rest of your analysis)

Do NOT create explicit sub-sections or headers within the main briefing. Instead, weave speaker context, user intent, and your analysis into a flowing narrative that naturally incorporates all the context you've been given."""


def generate_briefing(transcript: str, context: Dict) -> Tuple[str, int]:
    """
    Generate intelligent briefing with two-stage prompting.

    Args:
        transcript: Full episode transcript
        context: User's questionnaire answers {
            'motivation': str,
            'depth_level': str,
            'reasoning_mode': str,
            'narrative_tone': str,
            'curiosity_focus': str (optional)
        }

    Returns:
        (briefing_text, token_count)
    """
    logger.info(f"Generating briefing with context: {context}")

    # Step 1: Research speakers from transcript
    speakers = research_speakers(transcript)
    logger.info(f"Extracted speaker info: {speakers}")

    # Step 2: Build dynamic user prompt
    user_prompt = build_user_prompt(transcript, context, speakers)

    # Log the prompts for debugging
    logger.info("=" * 80)
    logger.info("SYSTEM PROMPT:")
    logger.info("-" * 80)
    logger.info(SYSTEM_PROMPT)
    logger.info("=" * 80)
    logger.info("USER PROMPT (first 2000 chars):")
    logger.info("-" * 80)
    logger.info(user_prompt[:2000])
    logger.info("..." if len(user_prompt) > 2000 else "")
    logger.info("=" * 80)

    # Step 3: Call Claude API with two-stage prompting
    # Increase max_tokens to support longer briefings (1500 words ~= 2000 tokens)
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,  # Increased for essay-length deep briefings
            system=SYSTEM_PROMPT,  # Explicit system prompt
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        briefing_text = response.content[0].text
        token_count = response.usage.input_tokens + response.usage.output_tokens

        logger.info(f"Briefing generated ({token_count} tokens)")

        return briefing_text, token_count

    except Exception as e:
        logger.error(f"Error generating briefing: {e}")
        raise


def research_speakers(transcript: str) -> Dict:
    """
    Extract speaker context from transcript.

    Looks for self-introductions and backgrounds mentioned in the first
    portion of the transcript (where introductions typically happen).

    Args:
        transcript: Full podcast transcript

    Returns:
        {
            'speaker_summary': str  # Brief context about speakers
        }
    """
    # Use first 5000 characters (where intros typically happen)
    intro_section = transcript[:10000]

    extraction_prompt = f"""From this podcast transcript excerpt, identify the speakers and extract:
1. Their names
2. Their roles/credentials (what they say about themselves)
3. Their potential perspectives or biases based on their backgrounds

Transcript excerpt:
{intro_section}

Provide a brief 2-3 sentence summary of who's speaking and what shapes their perspective.
Format: Just the summary text, no JSON."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": extraction_prompt
            }]
        )

        speaker_summary = response.content[0].text.strip()
        return {'speaker_summary': speaker_summary}

    except Exception as e:
        logger.warning(f"Failed to extract speaker info: {e}")
        return {'speaker_summary': 'Speaker information not available.'}


def build_user_prompt(transcript: str, context: Dict, speakers: Dict) -> str:
    """
    Build dynamic prompt based on user's questionnaire answers.

    Maps each question to specific instructions for the AI.

    Args:
        transcript: Full episode transcript
        context: Questionnaire answers
        speakers: Speaker research results

    Returns:
        Formatted user prompt
    """

    # Map motivation to focus area
    motivation_map = {
        'topic_interesting': 'Focus on the core ideas and why they matter.',
        'speaker_perspective': 'Focus on the speaker unique angle and background.',
        'personal_connection': 'Focus on connections to broader themes and how this relates to lived experience.',
        'cultural_relevance': 'Focus on why this conversation is happening now and what it reflects about current trends.'
    }

    # Map depth_level to instructions WITH word count requirements
    depth_map = {
        'essence': {
            'instruction': 'Be sharp and concise. Extract the core 3-5 insights with minimal elaboration. Get to the point.',
            'word_count': 600,
            'description': 'quick but substantive'
        },
        'balanced': {
            'instruction': 'Balance key points with enough context to understand the reasoning. Mix breadth and depth.',
            'word_count': 1000,
            'description': 'balanced and thorough'
        },
        'deep': {
            'instruction': 'Go deep. Explore the nuances, tensions, and reasoning behind claims. Take your time with ideas. This is an essay-length analysis.',
            'word_count': 1500,
            'description': 'comprehensive and essay-like'
        }
    }

    # Get depth settings
    depth_settings = depth_map.get(context['depth_level'], depth_map['balanced'])

    # Map reasoning_mode to lens
    lens_map = {
        'connect': 'Show how ideas connect - draw threads across the conversation. Highlight patterns and relationships.',
        'challenge': 'Point out gaps, contradictions, or assumptions worth questioning. Be critical but fair.',
        'apply': 'Show how this plays out in real contexts - make it concrete. Focus on practical implications.',
        'reflect': 'Step back - what does this reveal about broader trends or human nature? Think meta.'
    }

    # Map narrative_tone to voice
    tone_map = {
        'analytical': 'Direct and precise. Focus on logic and structure. Be systematic.',
        'conversational': 'Warm and curious. Like explaining to a smart friend over coffee.',
        'thoughtful': 'Contemplative and nuanced. Take your time with ideas. Be measured.',
        'provocative': 'Bold and challenging. Do not shy away from strong takes. Push thinking.'
    }

    # Truncate transcript to fit context window
    truncated_transcript = transcript[:100000]

    # Build prompt
    prompt = f"""TRANSCRIPT:
{truncated_transcript}

SPEAKER CONTEXT:
{speakers['speaker_summary']}

---

YOUR BRIEFING PARAMETERS:

Listener's intent: {motivation_map.get(context['motivation'], motivation_map['topic_interesting'])}

Depth & length: {depth_settings['instruction']} TARGET LENGTH: ~{depth_settings['word_count']} words ({depth_settings['description']})

Analytical lens: {lens_map.get(context['reasoning_mode'], lens_map['connect'])}

Voice/tone: {tone_map.get(context['narrative_tone'], tone_map['conversational'])}
"""

    # Add curiosity focus if provided
    if context.get('curiosity_focus'):
        prompt += f"\nSpecific curiosity to address: {context['curiosity_focus']}\n"

    prompt += f"""
---

INSTRUCTIONS:

Write a {depth_settings['description']} briefing of approximately {depth_settings['word_count']} words.

Structure EXACTLY as follows:

## Key Takeaways
- 3-5 bullet points capturing the core insights

## [Choose your own compelling title based on the conversation]

Write a well-structured newsletter-style article with:
- Use ### subheadings to break up the content (3-5 subheadings depending on depth)
- Each section should flow naturally and explore a distinct aspect
- Weave in who the speakers are and what shapes their perspectives
- Address the listener's intent and curiosity (if provided)
- Apply the analytical lens requested
- Use the voice/tone specified
- End with a "Final Thoughts" section containing 2-3 provocative questions

Newsletter formatting rules:
- Short paragraphs (2-4 sentences each)
- Clear section breaks with ### subheadings
- Readable, scannable structure
- Professional email newsletter aesthetic

CRITICAL: Your briefing must be substantive and well-organized. {depth_settings['word_count']} words is the TARGET — do not write shallow summaries. Use subheadings to create visual hierarchy and improve readability.

Begin your briefing:"""

    return prompt


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count for cost tracking.

    Rule of thumb: 1 token ≈ 4 characters
    Anthropic uses similar tokenization to GPT

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4
