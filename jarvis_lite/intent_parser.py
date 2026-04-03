from __future__ import annotations

import re
from dataclasses import dataclass


KNOWN_WEBSITE_NAMES = {
    "chatgpt",
    "facebook",
    "github",
    "gmail",
    "google",
    "instagram",
    "linkedin",
    "netflix",
    "reddit",
    "stackoverflow",
    "wikipedia",
    "youtube",
}

SPECIAL_FOLDER_WORDS = {
    "desktop",
    "documents",
    "downloads",
    "music",
    "pictures",
    "videos",
}


@dataclass
class CommandIntent:
    intent: str
    target: str = ""
    value: str = ""
    raw_text: str = ""


def parse_command(text: str) -> CommandIntent:
    raw_text = text.strip()
    prepared = _prepare_text(raw_text)
    simplified = prepared.lower()

    if not simplified:
        return CommandIntent(intent="empty", raw_text=raw_text)

    memory_store = _parse_memory_store(prepared)
    if memory_store:
        return CommandIntent(
            intent="remember",
            target=memory_store["key"],
            value=memory_store["value"],
            raw_text=raw_text,
        )

    memory_recall = _parse_memory_recall(simplified)
    if memory_recall:
        return CommandIntent(
            intent="recall",
            target=memory_recall,
            raw_text=raw_text,
        )

    memory_forget = _parse_memory_forget(simplified)
    if memory_forget:
        return CommandIntent(
            intent="forget",
            target=memory_forget,
            raw_text=raw_text,
        )

    if simplified in {"exit", "quit", "goodbye", "bye", "stop"}:
        return CommandIntent(intent="exit", raw_text=raw_text)

    if simplified in {"help", "what can you do", "show help", "commands"}:
        return CommandIntent(intent="help", raw_text=raw_text)

    close_match = re.match(r"^(?:close|terminate|end)\s+(.+)$", prepared, flags=re.IGNORECASE)
    if close_match:
        target = _clean_target(close_match.group(1))
        return CommandIntent(intent="close_app", target=target, raw_text=raw_text)

    search_patterns = [
        r"^(?:search(?: for)?|google|look up|find)\s+(.+)$",
        r"^(?:search google for|open google and search for)\s+(.+)$",
    ]
    for pattern in search_patterns:
        match = re.match(pattern, prepared, flags=re.IGNORECASE)
        if match:
            return CommandIntent(
                intent="search_web",
                target=match.group(1).strip(),
                raw_text=raw_text,
            )

    open_match = re.match(r"^(?:open|launch|start|run)\s+(.+)$", prepared, flags=re.IGNORECASE)
    if open_match:
        target = _clean_target(open_match.group(1))

        if _looks_like_path(target):
            return CommandIntent(intent="open_path", target=target, raw_text=raw_text)

        if _looks_like_website(target):
            return CommandIntent(
                intent="open_website",
                target=target,
                raw_text=raw_text,
            )

        return CommandIntent(intent="open_app", target=target, raw_text=raw_text)

    conversation_map = {
        "hello": "greeting",
        "hi": "greeting",
        "hey": "greeting",
        "thanks": "thanks",
        "thank you": "thanks",
        "how are you": "how_are_you",
        "who are you": "identity",
    }
    if simplified in conversation_map:
        return CommandIntent(
            intent="conversation",
            target=conversation_map[simplified],
            raw_text=raw_text,
        )

    return CommandIntent(intent="unknown", raw_text=raw_text)


def _prepare_text(text: str) -> str:
    prepared = text.strip()
    prepared = re.sub(r"[?!.,]", "", prepared)
    prepared = re.sub(
        r"\b(jarvis|please|kindly|for me)\b",
        "",
        prepared,
        flags=re.IGNORECASE,
    )
    prepared = re.sub(
        r"\b(can you|could you|would you|will you)\b",
        "",
        prepared,
        flags=re.IGNORECASE,
    )
    prepared = re.sub(r"\s+", " ", prepared)
    return prepared.strip()


def _clean_target(target: str) -> str:
    target = target.strip().strip('"').strip("'")
    target = re.sub(r"\b(app|application|program)\b", "", target).strip()
    target = re.sub(r"\s+", " ", target)

    folder_match = re.match(r"^(?:folder|file)\s+(.+)$", target)
    if folder_match:
        target = folder_match.group(1).strip()

    return target


def _looks_like_website(target: str) -> bool:
    normalized = target.lower().strip()
    if normalized in KNOWN_WEBSITE_NAMES:
        return True

    if normalized.startswith(("http://", "https://", "www.")):
        return True

    if re.search(r"\.(com|org|net|io|ai|in|dev)\b", normalized):
        return True

    if normalized.endswith("website") or normalized.endswith("site"):
        return True

    return False


def _looks_like_path(target: str) -> bool:
    normalized = target.lower().strip()

    if normalized in SPECIAL_FOLDER_WORDS:
        return True

    if normalized.endswith(" folder") or normalized.endswith(" file"):
        return True

    if re.match(r"^[a-z]:\\", target, flags=re.IGNORECASE):
        return True

    if "/" in target or "\\" in target:
        return True

    return False


def _parse_memory_store(text: str) -> dict[str, str] | None:
    patterns = [
        r"^my (.+?) is (.+)$",
        r"^remember that my (.+?) is (.+)$",
        r"^remember my (.+?) is (.+)$",
        r"^save my (.+?) as (.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            if key and value:
                return {"key": key, "value": value}

    return None


def _parse_memory_recall(text: str) -> str | None:
    patterns = [
        r"^what(?: is|'s) my (.+)$",
        r"^tell me my (.+)$",
        r"^do you remember my (.+)$",
    ]

    if text == "who am i":
        return "name"

    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return match.group(1).strip()

    return None


def _parse_memory_forget(text: str) -> str | None:
    patterns = [
        r"^forget my (.+)$",
        r"^delete my (.+)$",
        r"^remove my (.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return match.group(1).strip()

    return None
