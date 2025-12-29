import time
import sys
import logging
import threading
from config import Config
from models.brain_manager import BrainManager
from tools.system_ctrl import SystemTools
from tools.web_search import WebSearch
from tools.messaging import MessagingTools
from tools.voice_io import VoiceIO

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bhumi-Main")

def main():
    logger.info("Initializing Bhumi...")

    # Initialize Modules
    brain = BrainManager()
    sys_tools = SystemTools()
    web_tools = WebSearch()
    msg_tools = MessagingTools()
    voice = VoiceIO()

    def process_command(user_input=None):
        """
        1. Listen (if no input provided)
        2. Recognize intent
        3. Execute tool or generate chat
        4. Speak response
        """
        # 1. Listen
        if user_input is None:
            # Voice Mode
            logger.info("Listening via VoiceIO...")
            user_input = voice.listen_chunk()
            if not user_input or user_input == "Whisper not loaded.":
                logger.warning("No audio captured or Whisper missing.")
                return

        logger.info(f"User Input: {user_input}")

        # 2. Intent / Processing
        # Simple keyword checks for tools (Production-grade would use LLM tool calling)
        response_text = ""

        lower_input = user_input.lower()

        if "switch mode" in lower_input:
            # Toggle Brain
            new_mode = "gemini" if brain.mode == "ollama" else "ollama"
            response_text = brain.switch_mode(new_mode)

        elif "compile" in lower_input and "rom" in lower_input:
            response_text = sys_tools.compile_rom("haydn_build.sh")

        elif "check health" in lower_input:
            response_text = sys_tools.check_health()

        elif "search" in lower_input:
            query = user_input.replace("search", "").strip()
            response_text = web_tools.search_web(query)

        elif "tech news" in lower_input:
            response_text = web_tools.fetch_tech_news()

        elif "email" in lower_input:
            response_text = msg_tools.check_emails()

        elif "whatsapp" in lower_input:
            response_text = "I need you to implement the detailed parsing for WhatsApp, darling. 😘"

        else:
            # 3. Chat with Brain
            response_text = brain.chat(user_input)

        # 4. Speak
        print(f"Bhumi: {response_text}")
        voice.speak(response_text)

    # Start Main Loop
    logger.info("Bhumi is ready! Press Ctrl+C to exit.")

    if Config.CLI_MODE:
        logger.info("Running in CLI Mode. Type your commands.")
        try:
            while True:
                user_input = input("You: ")
                process_command(user_input)
        except KeyboardInterrupt:
            logger.info("Shutting down. Bye handsome! 💋")
    else:
        logger.info(f"Running in Voice Mode. Press {Config.HOTKEY} to talk.")
        # Start Hotkey Listener
        # Note: listen_chunk in process_command is blocking for duration.
        # Ideally, hotkey triggers start recording, release stops.
        # Here we trigger a fixed recording window on keypress.
        listener = voice.start_hotkey_listener(lambda: process_command(user_input=None))
        if listener:
            listener.join()
        else:
            logger.error("Could not start hotkey listener. Exiting.")

if __name__ == "__main__":
    main()
