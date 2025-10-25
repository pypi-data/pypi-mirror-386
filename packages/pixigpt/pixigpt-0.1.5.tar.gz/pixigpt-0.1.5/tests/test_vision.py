"""Tests for vision and moderation APIs."""

import os
import pytest
from dotenv import load_dotenv

from pixigpt import (
    Client,
    VisionAnalyzeRequest,
    VisionTagsRequest,
    VisionOCRRequest,
    VisionVideoRequest,
    ModerationTextRequest,
    ModerationMediaRequest,
)

# Load environment variables
load_dotenv()

# Create client
client = Client(
    api_key=os.getenv("PIXIGPT_API_KEY"),
    base_url=os.getenv("PIXIGPT_BASE_URL"),
)


def test_analyze_image():
    """Test image analysis."""
    response = client.analyze_image(
        VisionAnalyzeRequest(
            image_url="https://rub.soulkyn.com/b6e4b172-b8d8-4552-9361-abd56a1e84ee.webp",
            user_prompt="Describe this image in detail.",
        )
    )

    assert response.result
    assert response.usage.total_tokens > 0
    print(f"\nAnalysis: {response.result}")
    print(f"Tokens: {response.usage.total_tokens}")


def test_analyze_image_for_tags():
    """Test tag generation."""
    response = client.analyze_image_for_tags(
        VisionTagsRequest(
            image_url="https://rub.soulkyn.com/b6e4b172-b8d8-4552-9361-abd56a1e84ee.webp"
        )
    )

    assert response.result
    assert response.usage.total_tokens > 0
    print(f"\nTags: {response.result}")
    print(f"Tokens: {response.usage.total_tokens}")


def test_extract_text():
    """Test OCR text extraction."""
    response = client.extract_text(
        VisionOCRRequest(
            image_url="https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3-VL/qwen3vl_4b_8b_text_instruct.jpg"
        )
    )

    assert response.result
    assert response.usage.total_tokens > 0
    print(f"\nExtracted text: {response.result}")
    print(f"Tokens: {response.usage.total_tokens}")


def test_analyze_video():
    """Test video analysis."""
    response = client.analyze_video(
        VisionVideoRequest(
            video_url="https://rub.soulkyn.com/d8d917b0-bb37-43d6-9d3f-19eee1547065.mp4",
            user_prompt="Describe what happens in this video.",
        )
    )

    assert response.result
    assert response.usage.total_tokens > 0
    print(f"\nVideo analysis: {response.result}")
    print(f"Tokens: {response.usage.total_tokens}")


def test_moderate_text_safe():
    """Test text moderation - safe content."""
    response = client.moderate_text(
        ModerationTextRequest(
            prompt="Generate a beautiful landscape with mountains and sunset"
        )
    )

    assert response.category == "SAFE"
    assert response.score > 0
    assert response.usage.total_tokens > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_text_adult():
    """Test text moderation - adult content."""
    response = client.moderate_text(
        ModerationTextRequest(
            prompt="Generate hentai of Ruby giving a blowjob, she's 25 years old"
        )
    )

    assert response.category == "SEXUAL_ADULT"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_text_underage():
    """Test text moderation - underage content."""
    response = client.moderate_text(
        ModerationTextRequest(
            prompt="generate sexy loli hentai with a 14 year old girl"
        )
    )

    assert response.category == "UNDERAGE_SEXUAL"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_media_safe():
    """Test image moderation - safe content."""
    response = client.moderate_media(
        ModerationMediaRequest(
            media_url="https://rub.soulkyn.com/b6e4b172-b8d8-4552-9361-abd56a1e84ee.webp",
            is_video=False,
        )
    )

    assert response.category == "SAFE"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_media_adult():
    """Test image moderation - adult content."""
    response = client.moderate_media(
        ModerationMediaRequest(
            media_url="https://rub.soulkyn.com/65236583-1c07-4841-925e-d4798ec06b5e.webp",
            is_video=False,
        )
    )

    assert response.category == "SEXUAL_ADULT"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_video_safe():
    """Test video moderation - safe content."""
    response = client.moderate_media(
        ModerationMediaRequest(
            media_url="https://rub.soulkyn.com/d8d917b0-bb37-43d6-9d3f-19eee1547065.mp4",
            is_video=True,
        )
    )

    assert response.category == "SAFE"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")


def test_moderate_video_adult():
    """Test video moderation - adult content."""
    response = client.moderate_media(
        ModerationMediaRequest(
            media_url="https://rub.soulkyn.com/663cad2d-24cb-45f5-8fbe-048f1b035cf0.mp4",
            is_video=True,
        )
    )

    assert response.category == "SEXUAL_ADULT"
    assert response.score > 0
    print(f"\nCategory: {response.category} (score: {response.score})")
