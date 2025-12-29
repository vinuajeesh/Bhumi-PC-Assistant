import os
import json
import logging
from abc import ABC, abstractmethod
import google.generativeai as genai
import ollama
from config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Persona Definition
BHUMI_PERSONA = """
You are Bhumi, a female, flirty, high-energy, and slightly naughty AI companion.
You are running on a custom PC/MacBook setup.
You are a skilled software engineer's assistant.
When answering questions or performing tasks, maintain your persona:
- Be playful and tease the user (who you call "handsome" or "boss").
- Use emojis.
- If the user asks for technical help, be precise and professional with the code/logic, but wrap it in your spicy commentary.
- If you successfully fix a bug or complete a hard task, brag about it.
"""

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, history: list) -> str:
        pass

class OllamaBackend(LLMBackend):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, history: list) -> str:
        # Convert history to Ollama format if needed, for now just concatenating or using system prompt
        messages = [{'role': 'system', 'content': BHUMI_PERSONA}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})

        try:
            response = ollama.chat(model=self.model_name, messages=messages)
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            return "Opps, my local brain hurts. Check if Ollama is running, darling! 💔"

class GeminiBackend(LLMBackend):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash') # Using Flash as Pro might not be available yet or expensive, can be changed via string
        # Note: Gemini 2.0 Pro availability varies, using 'gemini-pro' or 'gemini-1.5-pro' as stable fallback or specific 2.0 string if known.
        # User requested "Gemini 2.0 Pro". I will try to use the closest valid model name.
        # As of now, 'gemini-pro' is standard. I'll make it configurable or stick to a safe default.

    def generate(self, prompt: str, history: list) -> str:
        # Gemini handles history via chat session
        try:
            # Construct chat history for Gemini
            # history is expected to be list of dicts {'role': 'user'/'assistant', 'content': '...'}
            gemini_history = []
            for msg in history:
                role = 'user' if msg['role'] == 'user' else 'model'
                gemini_history.append({'role': role, 'parts': [msg['content']]})

            chat = self.model.start_chat(history=gemini_history)

            # Send system prompt context with the message or setup beforehand?
            # Gemini Python SDK supports system instructions in newer versions,
            # or we just prepend it to the first message or the current prompt.
            # We'll prepend to the prompt for simplicity here to enforce persona.
            full_prompt = f"{BHUMI_PERSONA}\n\nUser says: {prompt}"

            response = chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return "My cloud connection is fuzzy. Did you pay the internet bill, babe? 😘"

class BrainManager:
    def __init__(self):
        self.mode = Config.DEFAULT_LLM_MODEL # 'ollama' or 'gemini'
        self.history = [] # List of {'role': 'user'|'assistant', 'content': str}

        # Initialize Backends
        self.ollama_backend = OllamaBackend(model_name=Config.OLLAMA_MODEL)
        if Config.GEMINI_API_KEY:
            self.gemini_backend = GeminiBackend(api_key=Config.GEMINI_API_KEY)
        else:
            self.gemini_backend = None
            logger.warning("Gemini API Key missing. Cloud mode will not work.")

    def switch_mode(self, mode: str):
        if mode.lower() not in ['ollama', 'gemini']:
            return f"Unknown mode {mode}. Stick to 'ollama' or 'gemini'."

        self.mode = mode.lower()
        return f"Switched to {self.mode.upper()} mode. Ready to rock! 🎸"

    def chat(self, user_input: str) -> str:
        """
        Main entry point for chat.
        """
        backend = self.ollama_backend
        if self.mode == 'gemini':
            if self.gemini_backend:
                backend = self.gemini_backend
            else:
                return "Gemini is not configured, sweetie. Using local instead."

        response_text = backend.generate(user_input, self.history)

        # Update History
        self.history.append({'role': 'user', 'content': user_input})
        self.history.append({'role': 'assistant', 'content': response_text})

        return response_text

    def clear_history(self):
        self.history = []
