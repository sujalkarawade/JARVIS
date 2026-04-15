from __future__ import annotations

import os
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus


class SystemController:
    """Windows-focused helpers for opening and closing apps, files, and websites."""

    KNOWN_WEBSITES = {
        "chatgpt": "https://chat.openai.com/",
        "chess": "https://www.chess.com/",
        "chess.com": "https://www.chess.com/",
        "classroom": "https://classroom.google.com/",
        "facebook": "https://www.facebook.com/",
        "github": "https://github.com/",
        "gmail": "https://mail.google.com/",
        "google": "https://www.google.com/",
        "google classroom": "https://classroom.google.com/",
        "google drive": "https://drive.google.com/",
        "instagram": "https://www.instagram.com/",
        "linkedin": "https://www.linkedin.com/",
        "netflix": "https://www.netflix.com/",
        "reddit": "https://www.reddit.com/",
        "stackoverflow": "https://stackoverflow.com/",
        "wikipedia": "https://www.wikipedia.org/",
        "youtube": "https://www.youtube.com/",
    }

    APP_COMMANDS = {
        "calculator": ["calc.exe"],
        "chrome": ["chrome.exe", "chrome"],
        "command prompt": ["cmd.exe"],
        "edge": ["msedge.exe", "msedge"],
        "explorer": ["explorer.exe"],
        "file explorer": ["explorer.exe"],
        "notepad": ["notepad.exe"],
        "paint": ["mspaint.exe"],
        "powershell": ["powershell.exe"],
        "spotify": ["spotify.exe", "spotify"],
        "terminal": ["wt.exe", "WindowsTerminal.exe"],
        "vs code": ["code", "Code.exe"],
        "visual studio code": ["code", "Code.exe"],
    }

    PROCESS_NAMES = {
        "calculator": "CalculatorApp.exe",
        "chrome": "chrome.exe",
        "command prompt": "cmd.exe",
        "edge": "msedge.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "powershell": "powershell.exe",
        "spotify": "spotify.exe",
        "terminal": "WindowsTerminal.exe",
        "vs code": "Code.exe",
        "visual studio code": "Code.exe",
    }

    SPECIAL_FOLDERS = {
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "downloads": Path.home() / "Downloads",
        "music": Path.home() / "Music",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
    }

    def open_website(self, target: str) -> tuple[bool, str]:
        url = self._resolve_website(target)
        if not url:
            return False, f"I could not figure out a valid website for '{target}'."

        try:
            webbrowser.open(url)
            return True, f"Opening {target}."
        except OSError as exc:
            return False, f"I could not open that website: {exc}"

    def search_web(self, query: str) -> tuple[bool, str]:
        if not query:
            return False, "Please tell me what you want to search for."

        url = f"https://www.google.com/search?q={quote_plus(query)}"
        try:
            webbrowser.open(url)
            return True, f"Searching Google for '{query}'."
        except OSError as exc:
            return False, f"I could not start the browser search: {exc}"

    def open_path(self, target: str) -> tuple[bool, str]:
        resolved_path = self._resolve_path(target)
        if resolved_path is None:
            return False, f"I could not find the file or folder '{target}'."

        try:
            os.startfile(str(resolved_path))
            item_type = "folder" if resolved_path.is_dir() else "file"
            return True, f"Opening {item_type}: {resolved_path}"
        except OSError as exc:
            return False, f"I found it, but could not open it: {exc}"

    def open_application(self, app_name: str) -> tuple[bool, str]:
        normalized = self._normalize(app_name)

        # Step 1: check known websites
        url = self._resolve_website(app_name)
        if url:
            try:
                webbrowser.open(url)
                return True, f"Opening {app_name}."
            except OSError as exc:
                return False, f"I could not open that: {exc}"

        # Step 2: try installed app commands and Start Menu
        for candidate in self._candidate_commands(app_name):
            if self._launch_command(candidate):
                return True, f"Opening {app_name}."

        shortcut = self._find_start_menu_match(normalized)
        if shortcut is not None:
            try:
                os.startfile(str(shortcut))
                return True, f"Opening {app_name} from the Start Menu."
            except OSError as exc:
                return False, f"I found {app_name}, but could not open it: {exc}"

        # Step 3: fall back to https://www.<name>.com
        guessed_url = self._guess_url(app_name)
        try:
            webbrowser.open(guessed_url)
            return True, f"Could not find '{app_name}' locally, opening {guessed_url} instead."
        except OSError as exc:
            return False, f"I could not open anything for '{app_name}': {exc}"

    def close_application(self, app_name: str) -> tuple[bool, str]:
        normalized = self._normalize(app_name)
        candidate_processes = []

        mapped_process = self.PROCESS_NAMES.get(normalized)
        if mapped_process:
            candidate_processes.append(mapped_process)

        compact_name = normalized.replace(" ", "")
        if compact_name:
            candidate_processes.append(f"{compact_name}.exe")

        if normalized and " " not in normalized:
            candidate_processes.append(f"{normalized}.exe")

        for process_name in dict.fromkeys(candidate_processes):
            result = subprocess.run(
                ["taskkill", "/IM", process_name, "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True, f"Closed {app_name}."

        powershell_name = normalized.replace("'", "''")
        powershell_command = (
            f"$name = '{powershell_name}'; "
            "$compact = $name.Replace(' ', ''); "
            "$matches = Get-Process | Where-Object { "
            " $_.ProcessName -like ('*' + $name + '*') -or "
            " $_.ProcessName -like ('*' + $compact + '*') "
            "}; "
            "if (-not $matches) { exit 1 } "
            "$matches | Stop-Process -Force"
        )

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", powershell_command],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return True, f"Closed {app_name}."

        return False, f"I could not find a running application called '{app_name}'."

    def _resolve_website(self, target: str) -> str | None:
        normalized = self._normalize(target)

        if normalized in self.KNOWN_WEBSITES:
            return self.KNOWN_WEBSITES[normalized]

        if normalized.endswith(" website") or normalized.endswith(" site"):
            normalized = re.sub(r"\s+(website|site)$", "", normalized).strip()
            if normalized in self.KNOWN_WEBSITES:
                return self.KNOWN_WEBSITES[normalized]

        if target.startswith(("http://", "https://")):
            return target

        if target.startswith("www."):
            return f"https://{target}"

        if re.search(r"\.(com|org|net|io|ai|in|dev)\b", target, flags=re.IGNORECASE):
            return f"https://{target}"

        return None

    def _guess_url(self, app_name: str) -> str:
        """Build a best-guess .com URL from an app/site name."""
        slug = self._normalize(app_name).replace(" ", "")
        # strip any existing .com/.org etc. so we don't double-up
        slug = re.sub(r"\.(com|org|net|io|ai|in|dev)$", "", slug)
        return f"https://www.{slug}.com"

    def _resolve_path(self, target: str) -> Path | None:
        cleaned = re.sub(r"\b(folder|file)\b", "", target, flags=re.IGNORECASE).strip()
        normalized = self._normalize(cleaned)

        special_folder = self.SPECIAL_FOLDERS.get(normalized)
        if special_folder and special_folder.exists():
            return special_folder

        expanded = Path(os.path.expandvars(os.path.expanduser(cleaned.strip('"'))))
        if expanded.exists():
            return expanded

        if not expanded.is_absolute():
            home_candidate = Path.home() / expanded
            if home_candidate.exists():
                return home_candidate

        return None

    def _candidate_commands(self, app_name: str) -> list[str]:
        normalized = self._normalize(app_name)
        candidates = list(self.APP_COMMANDS.get(normalized, []))

        raw_variations = [
            app_name.strip(),
            app_name.strip().replace(" ", ""),
            f"{app_name.strip()}.exe",
            f"{app_name.strip().replace(' ', '')}.exe",
        ]

        for value in raw_variations:
            if value and value not in candidates:
                candidates.append(value)

        return candidates

    def _launch_command(self, candidate: str) -> bool:
        expanded = os.path.expandvars(candidate)
        existing_path = Path(expanded)

        if existing_path.exists():
            os.startfile(str(existing_path))
            return True

        executable_path = shutil.which(expanded)
        if executable_path:
            subprocess.Popen([executable_path])
            return True

        return False

    def _find_start_menu_match(self, app_name: str) -> Path | None:
        start_menu_roots = [
            Path(os.environ.get("ProgramData", ""))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
        ]

        best_match: Path | None = None
        best_score = 0
        query_tokens = [token for token in app_name.split() if token]

        for root in start_menu_roots:
            if not root.exists():
                continue

            for path in root.rglob("*"):
                if path.suffix.lower() not in {".lnk", ".url", ".exe", ".appref-ms"}:
                    continue

                score = self._match_score(app_name, query_tokens, path.stem)
                if score > best_score:
                    best_score = score
                    best_match = path

        if best_score >= max(20, len(query_tokens) * 10):
            return best_match

        return None

    def _match_score(
        self,
        query: str,
        query_tokens: list[str],
        candidate_name: str,
    ) -> int:
        candidate = self._normalize(candidate_name)

        if not candidate:
            return 0

        if candidate == query:
            return 100

        score = 0
        if query in candidate:
            score += 40

        token_matches = sum(1 for token in query_tokens if token in candidate)
        score += token_matches * 15

        if candidate.startswith(query):
            score += 20

        return score

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.strip().lower().split())
