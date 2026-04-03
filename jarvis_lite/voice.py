from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


@dataclass
class VoiceStatus:
    input_available: bool
    output_available: bool
    input_message: str = ""
    output_message: str = ""


class VoiceAssistant:
    """Handles speech recognition and text-to-speech with graceful fallback."""

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer() if sr else None
        self.tts_engine = None
        self.recognition_backend: str | None = None
        self.microphone_error_message = ""
        self.status = VoiceStatus(
            input_available=sr is not None,
            output_available=pyttsx3 is not None,
        )

        if sr is None:
            self.status.input_message = (
                "Voice input is unavailable because SpeechRecognition or PyAudio "
                "is not installed."
            )
        else:
            self.recognition_backend = self._detect_recognition_backend()
            if self.recognition_backend is None:
                self.status.input_available = False
                self.status.input_message = (
                    "Voice input is unavailable because no supported speech backend "
                    "was found. Install pocketsphinx, openai-whisper, or use "
                    "SpeechRecognition 3.8.1 for recognize_google support."
                )
            else:
                self.microphone_error_message = self._check_microphone_support()
                if self.microphone_error_message:
                    self.status.input_available = False
                    self.status.input_message = self.microphone_error_message

        if pyttsx3 is None:
            self.status.output_message = (
                "Voice output is unavailable because pyttsx3 is not installed."
            )
        else:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 180)
                self.tts_engine.setProperty("volume", 1.0)
            except Exception as exc:
                self.status.output_available = False
                self.status.output_message = f"Voice output could not start: {exc}"

    def speak(self, text: str) -> None:
        if not self.status.output_available or self.tts_engine is None:
            return

        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception:
            self.status.output_available = False
            self.status.output_message = (
                "Voice output stopped working. Responses will continue in text."
            )

    def listen(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 8,
    ) -> tuple[str | None, str | None]:
        if not self.status.input_available or self.recognizer is None or sr is None:
            message = self.status.input_message or "Voice input is unavailable."
            return None, message

        try:
            with sr.Microphone() as source:
                self.recognizer.pause_threshold = 0.8
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except OSError:
            return None, "I could not access the microphone on this system."
        except ModuleNotFoundError as exc:
            message = self._format_missing_module_message(exc)
            self.status.input_available = False
            self.status.input_message = message
            return None, message
        except sr.WaitTimeoutError:
            return None, "I did not hear anything before the listening timeout."
        except Exception as exc:
            return None, f"Microphone error: {exc}"

        try:
            text = self._recognize_audio(audio)
            return text, None
        except sr.UnknownValueError:
            return None, "I could not understand the audio clearly."
        except sr.RequestError:
            return None, (
                "Speech recognition is unavailable right now. "
                "Please check your internet connection."
            )
        except AttributeError as exc:
            self.status.input_available = False
            self.status.input_message = (
                "Voice input backend is not available in this SpeechRecognition "
                f"build: {exc}"
            )
            return None, self.status.input_message
        except ImportError as exc:
            self.status.input_available = False
            self.status.input_message = (
                "Voice input requires an extra package for the selected backend: "
                f"{exc}"
            )
            return None, self.status.input_message
        except Exception as exc:
            return None, f"Speech recognition error: {exc}"

    def startup_messages(self) -> list[str]:
        messages: list[str] = []

        if self.status.input_message:
            messages.append(self.status.input_message)

        if self.status.output_message:
            messages.append(self.status.output_message)

        return messages

    def _detect_recognition_backend(self) -> str | None:
        if self.recognizer is None:
            return None

        if hasattr(self.recognizer, "recognize_google"):
            return "google"

        if hasattr(self.recognizer, "recognize_whisper") and find_spec("whisper"):
            return "whisper"

        if hasattr(self.recognizer, "recognize_sphinx") and find_spec("pocketsphinx"):
            return "sphinx"

        if hasattr(self.recognizer, "recognize_vosk") and find_spec("vosk"):
            return "vosk"

        return None

    def _check_microphone_support(self) -> str:
        if sr is None:
            return ""

        try:
            sr.Microphone.get_pyaudio()
            return ""
        except ModuleNotFoundError as exc:
            return self._format_missing_module_message(exc)
        except Exception:
            return ""

    def _recognize_audio(self, audio: "sr.AudioData") -> str:
        if self.recognizer is None or self.recognition_backend is None:
            raise AttributeError("No voice recognition backend is configured.")

        if self.recognition_backend == "google":
            return self.recognizer.recognize_google(audio)

        if self.recognition_backend == "whisper":
            return self.recognizer.recognize_whisper(audio, model="base")

        if self.recognition_backend == "sphinx":
            return self.recognizer.recognize_sphinx(audio)

        if self.recognition_backend == "vosk":
            return self.recognizer.recognize_vosk(audio)

        raise AttributeError(f"Unsupported recognition backend: {self.recognition_backend}")

    @staticmethod
    def _format_missing_module_message(exc: ModuleNotFoundError) -> str:
        if getattr(exc, "name", "") == "distutils":
            return (
                "Voice input is unavailable because Python 3.12 needs setuptools "
                "for microphone support. Run 'pip install setuptools'."
            )

        return f"Voice input is unavailable because a required module is missing: {exc}"
