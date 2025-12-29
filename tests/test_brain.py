import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.brain_manager import BrainManager, OllamaBackend, GeminiBackend
from config import Config

def test_brain_manager_init():
    with patch("config.Config.GEMINI_API_KEY", "fake_key"):
        brain = BrainManager()
        assert brain.mode == "ollama"
        assert brain.gemini_backend is not None

def test_brain_switch_mode():
    brain = BrainManager()
    resp = brain.switch_mode("gemini")
    assert brain.mode == "gemini"
    assert "Switched to GEMINI" in resp

def test_ollama_backend():
    with patch("ollama.chat") as mock_chat:
        mock_chat.return_value = {'message': {'content': 'Hello from local'}}

        backend = OllamaBackend("llama3")
        response = backend.generate("Hi", [])

        assert response == "Hello from local"
        mock_chat.assert_called_once()

def test_gemini_backend_missing_key():
    # If key is missing, BrainManager handles it, but let's test Backend directly
    # or BrainManager behavior
    with patch("config.Config.GEMINI_API_KEY", None):
        brain = BrainManager()
        assert brain.gemini_backend is None

        brain.switch_mode("gemini")
        response = brain.chat("Hi")
        assert "Gemini is not configured" in response
