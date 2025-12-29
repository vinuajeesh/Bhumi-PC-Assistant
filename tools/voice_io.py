import os
import platform
import logging
import subprocess
import threading
import wave
import time

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save, play
except ImportError:
    ElevenLabs = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from config import Config

logger = logging.getLogger(__name__)

class VoiceIO:
    def __init__(self):
        self.is_listening = False
        self.elevenlabs_client = None
        self.audio_format = pyaudio.paInt16 if pyaudio else None
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024

        # Initialize ElevenLabs
        if Config.ELEVENLABS_API_KEY and ElevenLabs:
            self.elevenlabs_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)

        # Initialize Whisper
        if WhisperModel:
             try:
                # 'cpu' int8 for broad compatibility as requested
                self.whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
             except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
                self.whisper = None
        else:
             self.whisper = None

        # Fallback TTS
        if Config.is_windows() and pyttsx3:
            self.engine = pyttsx3.init()
            # Set female voice if available
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        else:
            self.engine = None

    def speak(self, text):
        """Synthesizes speech."""
        logger.info(f"Bhumi says: {text}")

        # Try ElevenLabs first
        if self.elevenlabs_client:
            try:
                audio = self.elevenlabs_client.generate(
                    text=text,
                    voice=Config.ELEVENLABS_VOICE_ID,
                    model="eleven_monolingual_v1"
                )
                play(audio)
                return
            except Exception as e:
                logger.warning(f"ElevenLabs failed: {e}. Switching to fallback.")

        # Fallback
        if Config.is_macos():
            subprocess.run(["say", "-v", "Samantha", text])
        elif Config.is_windows() and self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            logger.warning("No TTS engine available.")

    def record_audio_to_file(self, filename="input.wav", duration=5):
        """
        Records audio for a fixed duration or until stop signal (mocked here as fixed duration).
        In a real hotkey scenario, we would start recording on press and stop on release.
        For simplicity with pynput global hotkeys (which trigger once), we can listen for a set time,
        or implement start/stop logic.
        """
        if not pyaudio:
            logger.error("PyAudio not installed.")
            return False

        p = pyaudio.PyAudio()
        stream = p.open(format=self.audio_format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        logger.info("Recording...")
        frames = []

        # Record for 'duration' seconds
        for i in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        logger.info("Finished recording.")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.audio_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return True

    def listen_chunk(self):
        """
        Records audio and returns text.
        """
        if not self.whisper:
            return "Whisper not loaded."

        filename = "temp_voice_input.wav"

        # Record
        success = self.record_audio_to_file(filename, duration=5) # 5 seconds fixed for this POC

        if not success:
            return "Error recording audio."

        # Transcribe
        try:
            segments, info = self.whisper.transcribe(filename, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            os.remove(filename)
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def start_hotkey_listener(self, callback):
        """
        Starts a background listener for the hotkey.
        """
        if not keyboard:
            logger.error("pynput not available")
            return

        def on_activate():
            logger.info("Hotkey activated!")
            callback()

        hotkey_str = Config.HOTKEY

        try:
            listener = keyboard.GlobalHotKeys({
                hotkey_str: on_activate
            })
            listener.start()
            return listener
        except Exception as e:
            logger.error(f"Failed to bind hotkey: {e}")
