from __future__ import annotations

from pathlib import Path

from jarvis_lite.intent_parser import CommandIntent, parse_command
from jarvis_lite.memory import MemoryStore
from jarvis_lite.system_control import SystemController
from jarvis_lite.voice import VoiceAssistant


class JarvisAssistant:
    """Main assistant that coordinates parsing, memory, voice, and system actions."""

    def __init__(self, memory_path: Path) -> None:
        self.memory = MemoryStore(memory_path)
        self.voice = VoiceAssistant()
        self.system = SystemController()
        self.running = True

    def run(self) -> None:
        self._print_welcome()

        input_mode = self._choose_input_mode()
        use_voice_output = self._choose_voice_output()

        while self.running:
            user_text = self._collect_input(input_mode)

            if not user_text:
                continue

            response = self._handle_input(user_text)
            self._respond(response, speak=use_voice_output)

    def _print_welcome(self) -> None:
        print("=" * 60)
        print("Jarvis - AI Personal Assistant")
        print("=" * 60)
        print("Type 'help' to see example commands.")

        for message in self.voice.startup_messages():
            print(f"Notice: {message}")

    def _choose_input_mode(self) -> str:
        print("\nChoose input mode:")
        print("1. Hybrid (type or speak)")
        print("2. Voice only")
        print("3. Text only")

        choice = input("Select an option [1]: ").strip() or "1"
        mapping = {"1": "hybrid", "2": "voice", "3": "text"}
        return mapping.get(choice, "hybrid")

    def _choose_voice_output(self) -> bool:
        if not self.voice.status.output_available:
            return False

        choice = input("Enable spoken responses? [Y/n]: ").strip().lower()
        return choice in {"", "y", "yes"}

    def _collect_input(self, input_mode: str) -> str:
        if input_mode == "text":
            return input("\nYou: ").strip()

        if input_mode == "voice":
            input("\nPress Enter to speak...")
            spoken_text, error = self.voice.listen()

            if spoken_text:
                print(f"You said: {spoken_text}")
                return spoken_text.strip()

            print(f"Jarvis: {error}")
            return input("Type a command instead (or press Enter to skip): ").strip()

        typed_text = input("\nYou (type a command or press Enter to speak): ").strip()
        if typed_text:
            return typed_text

        spoken_text, error = self.voice.listen()
        if spoken_text:
            print(f"You said: {spoken_text}")
            return spoken_text.strip()

        print(f"Jarvis: {error}")
        return input("Type a command instead (or press Enter to skip): ").strip()

    def _handle_input(self, user_text: str) -> str:
        intent = parse_command(user_text)

        if intent.intent == "empty":
            return "I did not receive a command. Please try again."

        if intent.intent == "help":
            return self._help_text()

        if intent.intent == "remember":
            self.memory.remember(intent.target, intent.value)
            return f"Okay, I will remember that your {intent.target} is {intent.value}."

        if intent.intent == "recall":
            value = self.memory.recall(intent.target)
            if value is None:
                return (
                    f"I do not have your {intent.target} saved yet. "
                    f"You can say 'My {intent.target} is ...'."
                )
            return f"Your {intent.target} is {value}."

        if intent.intent == "forget":
            removed = self.memory.forget(intent.target)
            if removed:
                return f"I removed your {intent.target} from memory."
            return f"I could not find any saved memory for {intent.target}."

        if intent.intent == "open_website":
            _, message = self.system.open_website(intent.target)
            return message

        if intent.intent == "search_web":
            _, message = self.system.search_web(intent.target)
            return message

        if intent.intent == "open_path":
            _, message = self.system.open_path(intent.target)
            return message

        if intent.intent == "open_app":
            _, message = self.system.open_application(intent.target)
            return message

        if intent.intent == "close_app":
            _, message = self.system.close_application(intent.target)
            return message

        if intent.intent == "screenshot":
            _, message = self.system.take_screenshot()
            return message

        if intent.intent == "lock_screen":
            _, message = self.system.lock_screen()
            return message

        if intent.intent == "shutdown":
            _, message = self.system.shutdown_pc()
            return message

        if intent.intent == "cancel_shutdown":
            _, message = self.system.cancel_shutdown()
            return message

        if intent.intent == "conversation":
            return self._conversation_reply(intent)

        if intent.intent == "exit":
            self.running = False
            return "Goodbye. Jarvis is shutting down."

        return (
            "I am not sure how to help with that yet. "
        )

    def _conversation_reply(self, intent: CommandIntent) -> str:
        stored_name = self.memory.recall("name")

        if intent.target == "greeting":
            if stored_name:
                return f"Hello Jarvis, {stored_name}. How can I help you today?"
            return "Hello. How can I help you today?"

        if intent.target == "thanks":
            return "You are welcome."

        if intent.target == "how_are_you":
            return "I am doing well and ready to help."

        if intent.target == "identity":
            return "I am Jarvis, your Python-based personal assistant."

        return "I am here and ready to help."

    def _respond(self, message: str, speak: bool) -> None:
        print(f"Jarvis: {message}")
        if speak:
            self.voice.speak(message)

    @staticmethod
    def _help_text() -> str:
        return (
            "Here are some example commands:\n"
            "- Open VS Code\n"
            "- Can you open Chrome?\n"
            "- Open YouTube\n"
            "- Open AWS Console\n"
            "- Search AI projects\n"
            "- Open downloads folder\n"
            "- Open C:\\Users\\YourName\\Documents\n"
            "- Close Chrome\n"
            "- Take a screenshot\n"
            "- Lock the screen\n"
            "- Shut down\n"
            "- Cancel shutdown\n"
            "- My name is Sujal\n"
            "- What is my name?\n"
            "- Forget my name\n"
            "- Hello\n"
            "- Exit"
        )
