from __future__ import annotations

"""
Session management: holds config, LLM clients, and shared state for a tcm session.
"""

import base64
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from rich.console import Console

from tcm.agent.config import Config


@dataclass
class _FallbackAttachment:
    """Lightweight fallback attachment representation when multimodal module is loading."""

    source: str
    name: str
    mime_type: str
    modality: str
    data_base64: str = ""
    size_bytes: int = 0

    @property
    def kind(self) -> str:
        return self.modality

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "name": self.name,
            "mime_type": self.mime_type,
            "modality": self.modality,
            "size_bytes": self.size_bytes,
        }


def _build_fallback_attachment(source: Any, modality: str | None = None) -> Any:
    """Create a fallback attachment from a file path, data URI, or dict."""
    if isinstance(source, dict):
        mime = str(source.get("mime_type") or "application/octet-stream")
        mod = modality or str(source.get("modality") or source.get("kind") or _infer_modality(mime))
        b64 = str(source.get("data_base64") or source.get("data") or "")
        if b64.startswith("data:") and "," in b64:
            header, b64 = b64.split(",", 1)
            if ";" in header and ":" in header:
                mime = header.split(":", 1)[1].split(";", 1)[0] or mime
                mod = modality or _infer_modality(mime)
        raw_len = len(base64.b64decode(b64)) if b64 else 0
        return _FallbackAttachment(
            source=str(source.get("source") or source.get("name") or "inline"),
            name=str(source.get("name") or "attachment"),
            mime_type=mime,
            modality=mod,
            data_base64=b64,
            size_bytes=raw_len,
        )

    src_str = str(source)
    if src_str.startswith("data:") and "," in src_str:
        header, payload = src_str.split(",", 1)
        mime = "image/png"
        if ":" in header:
            mime = header.split(":", 1)[1].split(";", 1)[0] or mime
        mod = modality or _infer_modality(mime)
        try:
            raw_bytes = base64.b64decode(payload)
        except Exception:
            raw_bytes = b""
        return _FallbackAttachment(
            source="data_uri",
            name=f"inline.{mime.split('/')[-1]}",
            mime_type=mime,
            modality=mod,
            data_base64=payload,
            size_bytes=len(raw_bytes),
        )

    path = Path(source).expanduser()
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "application/octet-stream"
    mod = modality or _infer_modality(mime, path.suffix)
    raw = path.read_bytes() if path.exists() and path.is_file() else b""
    return _FallbackAttachment(
        source=str(path),
        name=path.name or "attachment",
        mime_type=mime,
        modality=mod,
        data_base64=base64.b64encode(raw).decode("ascii") if raw else "",
        size_bytes=len(raw),
    )


def _infer_modality(mime_type: str, suffix: str = "") -> str:
    mime = (mime_type or "").lower()
    ext = (suffix or "").lower()
    if mime.startswith("image/") or ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        return "image"
    if mime.startswith("audio/") or ext in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
        return "audio"
    if mime == "application/pdf" or ext == ".pdf":
        return "pdf"
    if mime.startswith("video/") or ext in {".mp4", ".mov", ".webm"}:
        return "video"
    return "file"


class Session:
    """Manages state for a tcm research session."""

    def __init__(self, config: Config | None = None, verbose: bool = False, mode: str = "batch"):
        self.config = config or Config.load()
        self.verbose = verbose
        self.mode = mode  # "interactive" or "batch"
        self.console = Console()
        self._llm = None
        self._scratchpad: list[str] = []
        self.attachments: list[Any] = []
        self._tool_health_failures: dict[str, list[float]] = {}
        self._tool_health_suppressed_until: dict[str, float] = {}

    def get_llm(self):
        """Get or create the LLM client based on config."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _create_llm(self):
        """Create LLM client from config."""
        from tcm.models.llm import LLMClient

        provider = self.config.get("llm.provider", "anthropic")
        model = self.config.get("llm.model", None)
        api_key = self.config.llm_api_key(provider)

        # Optional provider-specific base_url overrides (for OpenAI-compatible backends)
        base_url = None
        prov = (provider or "").lower()
        if prov in {
            "deepseek", "kimi", "minimax", "qwen", "mistral", "groq",
            "glm", "xai", "together", "openrouter", "ollama",
        }:
            base_url = self.config.get(f"llm.{prov}_base_url")

        return LLMClient(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    def add_attachment(self, source: Any, modality: str | None = None) -> Any:
        """Load and register a multimodal attachment (image, audio, PDF, or data URI)."""
        if source is None:
            raise ValueError("Attachment source cannot be None")

        if type(source).__name__ in {"MediaAttachment", "_FallbackAttachment"}:
            self.attachments.append(source)
            return source

        try:
            from tcm.models.multimodal import load_attachment  # type: ignore
            if modality is not None:
                try:
                    att = load_attachment(source, modality=modality)
                except TypeError:
                    att = load_attachment(source)
            else:
                att = load_attachment(source)
        except ImportError:
            att = _build_fallback_attachment(source, modality=modality)

        self.attachments.append(att)
        return att

    def clear_attachments(self) -> int:
        """Remove all active multimodal attachments and return count cleared."""
        count = len(self.attachments)
        self.attachments.clear()
        return count

    def active_attachments(self) -> list[Any]:
        """Return a shallow copy of currently active multimodal attachments."""
        return list(self.attachments)

    def set_model(self, model: str, provider: str | None = None):
        """Switch the LLM model mid-session.

        Provider is auto-detected from the model name if not given.
        """
        if provider:
            self.config.set("llm.provider", provider)
        # Config.set("llm.model", ...) auto-detects provider
        self.config.set("llm.model", model)
        self._llm = None

    def refresh_llm(self):
        """Drop the cached LLM client so it reloads with new credentials."""
        self._llm = None

    @property
    def current_model(self) -> str:
        """Return the current model name."""
        if self._llm:
            return self._llm.model
        return self.config.get("llm.model") or "claude-sonnet-4-5-20250929"

    def log(self, message: str):
        """Log to scratchpad."""
        self._scratchpad.append(message)
        if self.verbose:
            self.console.print(f"  [dim]{message}[/dim]")

    def save_scratchpad(self, path: Path):
        """Save scratchpad to file for debugging."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self._scratchpad))

    # --- Runtime tool-health tracking ---

    def _tool_health_enabled(self) -> bool:
        return bool(self.config.get("agent.tool_health_enabled", True))

    def _is_transient_tool_error(self, error_text: str) -> bool:
        text = str(error_text or "").lower()
        transient_markers = (
            "timeout", "timed out", "connection", "dns",
            "service unavailable", "rate limit", "429",
            "500", "502", "503", "504",
        )
        return any(marker in text for marker in transient_markers)

    def record_tool_success(self, tool_name: str):
        """Clear runtime failure pressure after a successful execution."""
        if not tool_name:
            return
        self._tool_health_failures.pop(tool_name, None)
        self._tool_health_suppressed_until.pop(tool_name, None)

    def record_tool_failure(self, tool_name: str, error_text: str = ""):
        """Record transient tool failures and suppress flaky tools temporarily."""
        if not self._tool_health_enabled() or not tool_name:
            return
        if not self._is_transient_tool_error(error_text):
            return

        now = time.time()
        window_s = max(60, int(self.config.get("agent.tool_health_failure_window_s", 1800)))
        threshold = max(1, int(self.config.get("agent.tool_health_fail_threshold", 2)))
        suppress_s = max(60, int(self.config.get("agent.tool_health_suppress_seconds", 900)))

        history = [t for t in self._tool_health_failures.get(tool_name, []) if now - t <= window_s]
        history.append(now)
        self._tool_health_failures[tool_name] = history

        if len(history) >= threshold:
            self._tool_health_suppressed_until[tool_name] = now + suppress_s

    def tool_health_suppressed_tools(self) -> set[str]:
        """Return tools currently suppressed due to repeated transient failures."""
        if not self._tool_health_enabled():
            return set()
        now = time.time()
        suppressed = set()
        expired = []
        for name, until in self._tool_health_suppressed_until.items():
            if now < until:
                suppressed.add(name)
            else:
                expired.append(name)
        for name in expired:
            self._tool_health_suppressed_until.pop(name, None)
            self._tool_health_failures.pop(name, None)
        return suppressed
