"""Tests for the MEGA ULTRA SUPREME V11 Hello World endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app


@pytest.fixture
def client():
    """Create a test client with mocked database."""
    # Mock the database initialization to avoid connection errors
    with patch("local_newsifier.database.engine.create_db_and_tables"):
        with patch("local_newsifier.api.main.register_app"):
            return TestClient(app)


def test_hello_world_json(client):
    """Test the JSON hello world endpoint."""
    response = client.get("/hello/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "V11" in data["message"]
    assert "MEGA ULTRA SUPREME" in data["message"]
    assert data["version"] == "11.0.0-MEGA-ULTRA-SUPREME"
    assert "timestamp" in data
    assert "theme" in data
    assert "greeting_language" in data
    assert "ascii_art" in data
    assert "fun_fact" in data
    assert "snazziness_level" in data
    assert data["snazziness_level"] >= 11000
    assert "emojis" in data
    assert len(data["emojis"]) == 4
    assert "sound_effect" in data
    assert "achievement_unlocked" in data
    assert "power_level" in data
    assert data["power_level"] == "OVER 9000!!!"
    assert "v11_features" in data
    assert data["v11_features"]["mega_mode"] == "ACTIVATED"
    assert data["v11_features"]["ultra_boost"] == "ENGAGED"
    assert data["v11_features"]["supreme_status"] == "ACHIEVED"


def test_hello_world_web(client):
    """Test the web hello world endpoint."""
    response = client.get("/hello/web")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    content = response.text
    assert "HELLO WORLD V11" in content
    assert "MEGA ULTRA SUPREME" in content
    assert "Snazziness Meter" in content
    assert "Fun Fact:" in content
    assert "V11 EXCLUSIVE FEATURES" in content
    assert "<style>" in content
    assert "animation" in content
    assert "hueRotate" in content


def test_get_all_languages(client):
    """Test the languages endpoint."""
    response = client.get("/hello/languages")
    assert response.status_code == 200

    data = response.json()
    assert "languages" in data
    assert isinstance(data["languages"], dict)
    assert len(data["languages"]) > 15  # V11 has more languages!
    assert "en" in data["languages"]
    assert data["languages"]["en"] == "Hello World"
    assert "pirate" in data["languages"]
    assert "alien" in data["languages"]
    assert "dinosaur" in data["languages"]
    assert data["total"] == len(data["languages"])
    assert data["snazzy_factor"] == "MAXIMUM"


def test_get_emoji_themes(client):
    """Test the themes endpoint."""
    response = client.get("/hello/themes")
    assert response.status_code == 200

    data = response.json()
    assert "themes" in data
    assert isinstance(data["themes"], dict)
    assert "space" in data["themes"]
    assert "party" in data["themes"]
    assert "nature" in data["themes"]
    assert "tech" in data["themes"]
    assert "food" in data["themes"]
    assert "epic" in data["themes"]  # V11 new themes
    assert "animals" in data["themes"]
    assert "magical" in data["themes"]
    assert "cosmic" in data["themes"]
    assert "extreme" in data["themes"]
    assert data["total"] == len(data["themes"])
    assert "current_vibe" in data


def test_hello_world_specific_language(client):
    """Test hello world in specific languages."""
    # Test English
    response = client.get("/hello/en")
    assert response.status_code == 200
    data = response.json()
    assert "Hello World" in data["message"]
    assert data["language"] == "en"
    assert data["version"] == "11.0.0-MEGA-ULTRA-SUPREME"
    assert "sound_effect" in data
    assert "v11_bonus" in data

    # Test Spanish
    response = client.get("/hello/es")
    assert response.status_code == 200
    data = response.json()
    assert "Hola Mundo" in data["message"]
    assert data["language"] == "es"

    # Test Japanese
    response = client.get("/hello/ja")
    assert response.status_code == 200
    data = response.json()
    assert "こんにちは世界" in data["message"]
    assert data["language"] == "ja"

    # Test emoji language
    response = client.get("/hello/emoji")
    assert response.status_code == 200
    data = response.json()
    assert "👋🌍" in data["message"]
    assert data["language"] == "emoji"

    # Test V11 exclusive languages
    response = client.get("/hello/pirate")
    assert response.status_code == 200
    data = response.json()
    assert "Ahoy, World!" in data["message"]
    assert data["language"] == "pirate"

    response = client.get("/hello/dinosaur")
    assert response.status_code == 200
    data = response.json()
    assert "RAWR WORLD!" in data["message"]
    assert data["language"] == "dinosaur"


def test_hello_world_unknown_language(client):
    """Test hello world with unknown language falls back to English."""
    response = client.get("/hello/xyz")
    assert response.status_code == 200
    data = response.json()
    assert "Hello World" in data["message"]
    assert data["language"] == "xyz"


def test_ascii_art_variety(client):
    """Test that different ASCII arts are returned."""
    ascii_arts = set()
    for _ in range(10):
        response = client.get("/hello/")
        data = response.json()
        ascii_arts.add(data["ascii_art"])

    # Should have at least 2 different ASCII arts in 10 tries
    assert len(ascii_arts) >= 2


def test_random_elements(client):
    """Test that random elements change between requests."""
    themes = set()
    greetings = set()
    snazziness_levels = set()

    for _ in range(10):
        response = client.get("/hello/")
        data = response.json()
        themes.add(data["theme"])
        greetings.add(data["greeting_language"])
        snazziness_levels.add(data["snazziness_level"])

    # Should have some variety in random elements
    assert len(themes) >= 2
    assert len(greetings) >= 2
    assert len(snazziness_levels) >= 2


def test_mega_ultra_supreme_endpoint(client):
    """Test the V11 exclusive mega-ultra-supreme endpoint."""
    response = client.get("/hello/mega-ultra-supreme")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert data["version"] == "11.0.0-MEGA-ULTRA-SUPREME-MAXIMUM-OVERDRIVE"
    assert "mega_features" in data
    assert data["mega_features"]["power_level"] == "∞"
    assert data["mega_features"]["snazziness"] == "MAXIMUM OVERDRIVE"
    assert data["mega_features"]["special_message"] == "YOU HAVE ACHIEVED PEAK HELLO WORLD!"
    assert "ascii_art" in data
    assert len(data["ascii_art"]) > 100  # Combined ASCII arts
    assert "timestamp" in data
    assert "fun_fact" in data
