"""Local JSON repositories for conversations and assistant memory."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from threading import Lock, RLock, local
from time import monotonic, sleep
from typing import BinaryIO

from modules.models import Conversation


class JsonStorageError(RuntimeError):
    """Raised when a local JSON file cannot be safely read or written."""


_PATH_LOCKS: dict[Path, RLock] = {}
_PATH_LOCKS_GUARD = Lock()
_LOCK_STATE = local()


def _lock_for_path(path: Path) -> RLock:
    key = path.resolve()
    with _PATH_LOCKS_GUARD:
        lock = _PATH_LOCKS.get(key)
        if lock is None:
            lock = RLock()
            _PATH_LOCKS[key] = lock
        return lock


def _acquire_file_lock(lock_file: BinaryIO, lock_path: Path) -> None:
    if os.name == "nt":
        import msvcrt

        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()

        deadline = monotonic() + 30
        while True:
            lock_file.seek(0)
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                if monotonic() >= deadline:
                    raise JsonStorageError(
                        f"Impossible de verrouiller '{lock_path}' : {exc}"
                    ) from exc
                sleep(0.05)
    else:
        import fcntl

        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise JsonStorageError(
                f"Impossible de verrouiller '{lock_path}' : {exc}"
            ) from exc


def _release_file_lock(lock_file: BinaryIO, lock_path: Path) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        raise JsonStorageError(
            f"Impossible de libérer le verrou '{lock_path}' : {exc}"
        ) from exc


@contextmanager
def _locked(path: Path, lock: RLock) -> Iterator[None]:
    with lock:
        key = path.resolve()
        active_paths = getattr(_LOCK_STATE, "active_paths", set())
        if key in active_paths:
            yield
            return

        lock_path = path.with_name(f"{path.name}.lock")
        try:
            lock_file = lock_path.open("a+b")
        except OSError as exc:
            raise JsonStorageError(
                f"Impossible d'ouvrir le verrou '{lock_path}' : {exc}"
            ) from exc

        try:
            _acquire_file_lock(lock_file, lock_path)
        except JsonStorageError:
            lock_file.close()
            raise

        active_paths.add(key)
        _LOCK_STATE.active_paths = active_paths
        try:
            yield
        finally:
            active_paths.remove(key)
            try:
                _release_file_lock(lock_file, lock_path)
            finally:
                lock_file.close()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Valeur JSON non standard : {value}")


def _read_json(path: Path, default: dict, lock: RLock) -> dict:
    with _locked(path, lock):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file, parse_constant=_reject_json_constant)
        except FileNotFoundError:
            return deepcopy(default)
        except json.JSONDecodeError as exc:
            raise JsonStorageError(
                f"JSON invalide dans '{path}' "
                f"(ligne {exc.lineno}, colonne {exc.colno})."
            ) from exc
        except UnicodeDecodeError as exc:
            raise JsonStorageError(
                f"Le fichier JSON '{path}' n'est pas encodé en UTF-8."
            ) from exc
        except ValueError as exc:
            raise JsonStorageError(f"JSON invalide dans '{path}' : {exc}") from exc
        except OSError as exc:
            raise JsonStorageError(
                f"Impossible de lire le fichier JSON '{path}' : {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise JsonStorageError(
                f"Le document JSON '{path}' doit être un objet."
            )
        return data


def _write_json(path: Path, data: dict, lock: RLock) -> None:
    temporary_path: Path | None = None
    with _locked(path, lock):
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=path.parent,
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, path)
        except (OSError, TypeError, ValueError) as exc:
            cleanup_message = ""
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError as cleanup_error:
                    cleanup_message = (
                        f" Le fichier temporaire '{temporary_path}' "
                        f"n'a pas pu être supprimé : {cleanup_error}"
                    )
            raise JsonStorageError(
                f"Impossible d'écrire le fichier JSON '{path}' : {exc}."
                f"{cleanup_message}"
            ) from exc


def _ensure_json_file(path: Path, default: dict, lock: RLock) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise JsonStorageError(
            f"Impossible de préparer le dossier '{path.parent}' : {exc}"
        ) from exc
    with _locked(path, lock):
        if not path.exists():
            _write_json(path, default, lock)


def _read_memory_data(path: Path, lock: RLock) -> dict:
    data = _read_json(path, {"facts": [], "preferences": {}}, lock)
    facts = data.setdefault("facts", [])
    preferences = data.setdefault("preferences", {})
    if not isinstance(facts, list) or not all(
        isinstance(fact, str) for fact in facts
    ):
        raise JsonStorageError(
            f"Le champ 'facts' du fichier JSON '{path}' doit être une liste "
            "de textes."
        )
    if not isinstance(preferences, dict):
        raise JsonStorageError(
            f"Le champ 'preferences' du fichier JSON '{path}' doit être un objet."
        )
    return data


def _validate_conversations(data: dict, path: Path) -> list[dict]:
    conversations = data.get("conversations")
    if not isinstance(conversations, list):
        raise JsonStorageError(
            f"Le champ 'conversations' du fichier JSON '{path}' doit être une liste."
        )

    for index, item in enumerate(conversations):
        location = f"conversations[{index}] dans '{path}'"
        if not isinstance(item, dict):
            raise JsonStorageError(f"{location} doit être un objet.")
        for field in ("id", "title"):
            if not isinstance(item.get(field), str):
                raise JsonStorageError(f"Le champ '{field}' de {location} est invalide.")
        for field in ("created_at", "updated_at"):
            if field in item and not isinstance(item[field], str):
                raise JsonStorageError(f"Le champ '{field}' de {location} est invalide.")

        messages = item.get("messages", [])
        if not isinstance(messages, list):
            raise JsonStorageError(f"Le champ 'messages' de {location} doit être une liste.")
        for message_index, message in enumerate(messages):
            message_location = f"{location}.messages[{message_index}]"
            if not isinstance(message, dict):
                raise JsonStorageError(f"{message_location} doit être un objet.")
            if message.get("role") not in ("user", "assistant", "system"):
                raise JsonStorageError(
                    f"Le champ 'role' de {message_location} est invalide."
                )
            if not isinstance(message.get("content"), str):
                raise JsonStorageError(
                    f"Le champ 'content' de {message_location} doit être un texte."
                )
            if "created_at" in message and not isinstance(
                message["created_at"], str
            ):
                raise JsonStorageError(
                    f"Le champ 'created_at' de {message_location} est invalide."
                )
    return conversations


class JsonConversationStore:
    """Persist conversations in a local JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self._lock = _lock_for_path(self.path)
        _ensure_json_file(self.path, {"conversations": []}, self._lock)
        self._read()

    def _read(self) -> dict:
        data = _read_json(self.path, {"conversations": []}, self._lock)
        _validate_conversations(data, self.path)
        return data

    def _write(self, data: dict) -> None:
        _write_json(self.path, data, self._lock)

    def create(self, title: str = "Nouvelle conversation") -> Conversation:
        with _locked(self.path, self._lock):
            conversation = Conversation.create(title)
            data = self._read()
            data["conversations"].insert(0, conversation.to_dict())
            self._write(data)
            return conversation

    def list(self) -> list[Conversation]:
        with _locked(self.path, self._lock):
            return [
                Conversation.from_dict(item)
                for item in self._read()["conversations"]
            ]

    def get(self, conversation_id: str) -> Conversation | None:
        with _locked(self.path, self._lock):
            for conversation in self.list():
                if conversation.id == conversation_id:
                    return conversation
        return None

    def save(self, conversation: Conversation) -> None:
        with _locked(self.path, self._lock):
            data = self._read()
            conversations = data["conversations"]
            for index, item in enumerate(conversations):
                if item["id"] == conversation.id:
                    conversations[index] = conversation.to_dict()
                    break
            else:
                conversations.insert(0, conversation.to_dict())
            self._write(data)

    def delete(self, conversation_id: str) -> bool:
        with _locked(self.path, self._lock):
            data = self._read()
            conversations = data["conversations"]
            filtered = [
                item for item in conversations if item["id"] != conversation_id
            ]
            if len(filtered) == len(conversations):
                return False
            data["conversations"] = filtered
            self._write(data)
            return True


class JsonMemoryStore:
    """Persist small local facts in a local JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self._lock = _lock_for_path(self.path)
        _ensure_json_file(
            self.path,
            {"facts": [], "preferences": {}},
            self._lock,
        )
        self._read()

    def _read(self) -> dict:
        return _read_memory_data(self.path, self._lock)

    def _write(self, data: dict) -> None:
        _write_json(self.path, data, self._lock)

    def list(self) -> list[str]:
        with _locked(self.path, self._lock):
            return self._read()["facts"]

    def add(self, fact: str) -> bool:
        fact = fact.strip()
        if not fact:
            return False
        with _locked(self.path, self._lock):
            data = self._read()
            facts = data["facts"]
            if fact in facts:
                return False
            facts.insert(0, fact)
            self._write(data)
            return True

    def remove(self, fact: str) -> bool:
        with _locked(self.path, self._lock):
            data = self._read()
            facts = data["facts"]
            if fact not in facts:
                return False
            facts.remove(fact)
            self._write(data)
            return True

    def clear(self) -> None:
        with _locked(self.path, self._lock):
            data = self._read()
            data["facts"] = []
            self._write(data)


class JsonPreferencesStore:
    """Persist and reload user preferences in the local memory file."""

    DEFAULT_PREFERENCES = {
        "display_name": "",
        "language": "Français",
        "response_tone": "Professionnel",
        "ollama_model": "phi3",
        "context_messages": 20,
    }

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self._lock = _lock_for_path(self.path)
        _ensure_json_file(
            self.path,
            {"facts": [], "preferences": dict(self.DEFAULT_PREFERENCES)},
            self._lock,
        )
        with _locked(self.path, self._lock):
            data = self._read()
            if not data["preferences"]:
                data["preferences"] = dict(self.DEFAULT_PREFERENCES)
                self._write(data)
            else:
                self._validate_preferences(data["preferences"])

    def _read(self) -> dict:
        return _read_memory_data(self.path, self._lock)

    def _write(self, data: dict) -> None:
        _write_json(self.path, data, self._lock)

    def _validate_preferences(self, saved: dict) -> None:
        for key, value in saved.items():
            if key not in self.DEFAULT_PREFERENCES:
                continue
            if key == "context_messages":
                valid = (
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and 1 <= value <= 100
                )
            elif key == "language":
                valid = value in ("Français", "English")
            elif key == "response_tone":
                valid = value in ("Professionnel", "Simple", "Technique")
            else:
                valid = isinstance(value, str)
            if not valid:
                raise JsonStorageError(
                    f"La préférence '{key}' du fichier JSON '{self.path}' est invalide."
                )

    def load(self) -> dict:
        with _locked(self.path, self._lock):
            saved = self._read()["preferences"]
            self._validate_preferences(saved)
            preferences = dict(self.DEFAULT_PREFERENCES)
            preferences.update(
                {key: value for key, value in saved.items() if key in preferences}
            )
            return preferences

    def save(self, preferences: dict) -> dict:
        saved = dict(self.DEFAULT_PREFERENCES)
        for key in saved:
            if key in preferences:
                saved[key] = preferences[key]

        saved["display_name"] = str(saved["display_name"]).strip()
        if saved["language"] not in ("Français", "English"):
            saved["language"] = "Français"
        if saved["response_tone"] not in ("Professionnel", "Simple", "Technique"):
            saved["response_tone"] = "Professionnel"
        saved["ollama_model"] = str(saved["ollama_model"]).strip() or "phi3"

        try:
            context_messages = int(saved["context_messages"])
        except (TypeError, ValueError):
            context_messages = 20
        saved["context_messages"] = max(1, min(context_messages, 100))

        with _locked(self.path, self._lock):
            data = self._read()
            stored_preferences = data["preferences"]
            stored_preferences.update(saved)
            data["preferences"] = stored_preferences
            self._write(data)
        return saved
