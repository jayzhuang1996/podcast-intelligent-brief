"""
YouTube integration using yt-dlp.

Why yt-dlp instead of YouTube Data API?
- No API key required (free!)
- No quota limits
- Can search, get metadata, and download captions
- Returns same data as official API
"""

import subprocess
import json
from typing import List, Dict, Optional
from loguru import logger


def search_youtube(query: str, limit: int = 5) -> List[Dict]:
    """
    Search YouTube for videos.

    Args:
        query: Search term (e.g., "joe rogan")
        limit: Number of results to return

    Returns:
        List of video metadata dicts

    Example:
        results = search_youtube("joe rogan", limit=5)
        # Returns: [{"video_id": "abc123", "title": "JRE #2049", ...}, ...]
    """
    logger.info(f"Searching YouTube: '{query}' (limit={limit})")

    cmd = [
        'yt-dlp',
        f'ytsearch{limit}:{query}',
        '--dump-json',
        '--skip-download',
        '--no-warnings'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            data = json.loads(line)
            videos.append({
                'video_id': data['id'],
                'title': data['title'],
                'channel_name': data.get('uploader', 'Unknown'),
                'thumbnail_url': data.get('thumbnail', ''),
                'duration': data.get('duration', 0),
                'published_at': data.get('upload_date', ''),
                'video_url': data.get('webpage_url', f"https://youtube.com/watch?v={data['id']}")
            })

        logger.info(f"Found {len(videos)} videos")
        return videos

    except subprocess.TimeoutExpired:
        logger.error(f"YouTube search timed out for query: {query}")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp error: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error searching YouTube: {e}")
        return []


def get_video_metadata(video_id: str) -> Optional[Dict]:
    """
    Fetch metadata for a single video.

    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")

    Returns:
        Video metadata dict or None if error
    """
    logger.info(f"Fetching metadata for video: {video_id}")

    cmd = [
        'yt-dlp',
        f'https://youtube.com/watch?v={video_id}',
        '--dump-json',
        '--skip-download',
        '--no-warnings'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        data = json.loads(result.stdout)

        return {
            'video_id': data['id'],
            'title': data['title'],
            'channel_name': data.get('uploader', 'Unknown'),
            'description': data.get('description', ''),
            'thumbnail_url': data.get('thumbnail', ''),
            'duration': data.get('duration', 0),
            'published_at': data.get('upload_date', ''),
            'video_url': data.get('webpage_url', f"https://youtube.com/watch?v={video_id}")
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Metadata fetch timed out for video: {video_id}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp error: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching metadata: {e}")
        return None


def download_captions(video_id: str) -> Optional[str]:
    """
    Download and clean auto-generated captions.

    Args:
        video_id: YouTube video ID

    Returns:
        Plain text transcript or None if no captions available

    Note: Takes ~30 seconds for long videos
    """
    logger.info(f"Downloading captions for video: {video_id}")

    import tempfile
    import os

    # Use temp directory
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"yt_{video_id}")

    cmd = [
        'yt-dlp',
        f'https://youtube.com/watch?v={video_id}',
        '--skip-download',
        '--write-auto-sub',
        '--sub-lang', 'en',
        '--sub-format', 'vtt',
        '--output', output_path,
        '--no-warnings'
    ]

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            timeout=60,
            check=True
        )

        # Read VTT file
        vtt_path = f'{output_path}.en.vtt'
        if not os.path.exists(vtt_path):
            logger.warning(f"No captions file found for video: {video_id}")
            return None

        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Clean VTT format
        transcript = clean_vtt(content)

        # Clean up temp file
        try:
            os.remove(vtt_path)
        except:
            pass

        logger.info(f"Downloaded transcript ({len(transcript)} chars)")
        return transcript

    except subprocess.TimeoutExpired:
        logger.error(f"Caption download timed out for video: {video_id}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp error downloading captions: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading captions: {e}")
        return None


def clean_vtt(vtt_content: str) -> str:
    """
    Remove VTT timestamps and formatting, return plain text.

    Args:
        vtt_content: Raw VTT caption file content

    Returns:
        Plain text transcript
    """
    lines = []
    for line in vtt_content.split('\n'):
        # Skip timestamps (00:00:00.000 --> 00:00:05.000)
        if '-->' in line:
            continue
        # Skip WEBVTT header
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        # Skip cue identifiers (numbers)
        if line.strip().isdigit():
            continue
        # Skip empty lines
        if not line.strip():
            continue

        lines.append(line.strip())

    return ' '.join(lines)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.

    Supports formats:
    - https://youtube.com/watch?v=abc123
    - https://youtu.be/abc123
    - https://www.youtube.com/watch?v=abc123&feature=share
    - abc123 (already an ID)

    Args:
        url: YouTube URL or video ID

    Returns:
        Video ID or None if invalid format
    """
    import re

    # Already a video ID (11 chars, alphanumeric + underscore/dash)
    if re.match(r'^[A-Za-z0-9_-]{11}$', url):
        return url

    # Extract from URL
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]{11})',
        r'youtube\.com\/embed\/([A-Za-z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    logger.warning(f"Could not extract video ID from: {url}")
    return None
