from pathlib import Path

from jarvis_lite.assistant import JarvisAssistant


def main() -> None:
    project_root = Path(__file__).resolve().parent
    memory_path = project_root / "data" / "memory.json"

    assistant = JarvisAssistant(memory_path=memory_path)
    assistant.run()


if __name__ == "__main__":
    main()
