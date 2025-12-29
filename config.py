import os
import platform
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # OS Detection
    OS_NAME = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'

    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Default Rachel voice

    # Email
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
    EMAIL_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", 993))

    # Preferences
    DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "ollama")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

    # Interface Mode
    # If True, runs a text-based loop. If False, attempts to load Hotkey/Voice Listener.
    # Defaults to True in this sandbox environment, but user can set to False in .env
    CLI_MODE = os.getenv("CLI_MODE", "True").lower() == "true"

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUILD_SCRIPTS_DIR = os.path.join(BASE_DIR, "build_scripts")

    # Constants
    HOTKEY = os.getenv("WAKE_WORD_HOTKEY", "<ctrl>+<shift>+b")

    @staticmethod
    def is_windows():
        return Config.OS_NAME == "Windows"

    @staticmethod
    def is_macos():
        return Config.OS_NAME == "Darwin"
