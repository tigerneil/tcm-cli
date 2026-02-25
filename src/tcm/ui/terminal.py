
"""
Interactive terminal for tcm.

Provides a REPL-style interface for continuous research sessions.
"""

import random
import re
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from pathlib import Path

from tcm.agent.config import CONFIG_DIR

# Slash commands
SLASH_COMMANDS = {
    "/help": "Show command reference with examples",
    "/tools": "List all tools with status",
    "/model": "Switch LLM model/provider",
    "/lang": "Set response language: en | zh | bi",
    "/config": "Show active runtime configuration",
    "/keys": "Show API key setup status",
    "/doctor": "Run readiness diagnostics",
    "/usage": "Show session token/cost usage",
    "/copy": "Copy the last answer to clipboard",
    "/export": "Export session transcript to markdown",
    "/clear": "Clear the screen",
    "/exit": "Exit the terminal",
}

PT_STYLE = Style.from_dict({
    "prompt": "bold #c8a85c",
    "placeholder": "#555555",
    "bottom-toolbar": "#888888 bg:#1a1a2e",
    "completion-menu": "bg:#1a1a2e #cccccc",
    "completion-menu.completion": "bg:#1a1a2e #cccccc",
    "completion-menu.completion.current": "bg:#333355 #ffffff bold",
})


class SlashCompleter(Completer):
    """Autocomplete slash commands."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            for cmd, desc in SLASH_COMMANDS.items():
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text), display_meta=desc)


class InteractiveTerminal:
    """Interactive REPL for tcm research sessions."""

    def __init__(self, session):
        self.session = session
        self.console = Console()
        self.history_file = CONFIG_DIR / "history"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.prompt_session = PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=SlashCompleter(),
            style=PT_STYLE,
        )
        self._last_answer = ""
        self._transcript = []

    def run(self):
        """Run the interactive terminal loop."""
        from tcm.ui.suggestions import DEFAULT_SUGGESTIONS

        suggestion = random.choice(DEFAULT_SUGGESTIONS)
        self.console.print()
        self.console.print(f"  [dim]Try: {suggestion}[/dim]")
        self.console.print()

        while True:
            try:
                user_input = self.prompt_session.prompt(
                    [("class:prompt", "tcm> ")],
                    placeholder="Ask a TCM research question...",
                ).strip()

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    if self._handle_slash(user_input):
                        continue
                    else:
                        break  # /exit

                # Process query
                self._transcript.append(("user", user_input))
                self._process_query(user_input)

            except KeyboardInterrupt:
                self.console.print("\n  [dim]Use /exit to quit.[/dim]")
                continue
            except EOFError:
                break

        self.console.print("\n  [dim]Goodbye![/dim]")

    def _handle_slash(self, command: str) -> bool:
        """Handle slash command. Returns True to continue, False to exit."""
        cmd = command.split()[0].lower()

        if cmd == "/exit":
            return False
        elif cmd == "/clear":
            self.console.clear()
        elif cmd == "/help":
            self._show_help()
        elif cmd == "/tools":
            from tcm.tools import registry, ensure_loaded
            ensure_loaded()
            self.console.print(registry.list_tools_table())
        elif cmd == "/lang":
            self._lang_switch(command)
        elif cmd == "/config":
            self.console.print(self.session.config.to_table())
        elif cmd == "/keys":
            self.console.print(self.session.config.keys_table())
        elif cmd == "/usage":
            llm = self.session.get_llm()
            self.console.print(f"  {llm.usage.summary()}")
        elif cmd == "/model":
            self._model_picker(command)
        elif cmd == "/doctor":
            from tcm.agent.doctor import run_checks, to_table
            checks = run_checks(self.session.config)
            self.console.print(to_table(checks))
        elif cmd == "/copy":
            if self._last_answer:
                try:
                    import subprocess
                    subprocess.run(["pbcopy"], input=self._last_answer.encode(), check=True)
                    self.console.print("  [green]Copied to clipboard.[/green]")
                except Exception:
                    self.console.print("  [yellow]Clipboard copy not available.[/yellow]")
            else:
                self.console.print("  [dim]No answer to copy yet.[/dim]")
        elif cmd == "/export":
            self._export_transcript()
        else:
            self.console.print(f"  [yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("  Type /help for available commands.")

        return True

    def _show_help(self):
        """Show help panel."""
        lines = ["[bold]Available Commands[/bold]\n"]
        for cmd, desc in SLASH_COMMANDS.items():
            lines.append(f"  [cyan]{cmd:15}[/cyan] {desc}")
        lines.append("\n[bold]Tips[/bold]")
        lines.append("  • Use @tool.name to request specific tools")
        lines.append("  • Use @tcmsp or @pubmed to request specific databases")
        lines.append("  • Ask questions in English or Chinese")
        self.console.print(Panel("\n".join(lines), title="[bold]tcm help[/bold]", border_style="cyan"))

    def _lang_switch(self, command: str):
        """Show or set the response language (en, zh, bi)."""
        parts = command.split(maxsplit=1)
        cfg = self.session.config
        current = cfg.get("ui.language", "en")
        if len(parts) == 1:
            self.console.print(f"  Language: [cyan]{current}[/cyan] (set with /lang en|zh|bi)")
            return
        choice = parts[1].strip().lower()
        if choice not in {"en", "zh", "bi"}:
            self.console.print("  [yellow]Invalid language.[/yellow] Use: en | zh | bi")
            return
        try:
            cfg.set("ui.language", choice)
            cfg.save()
            self.console.print(f"  [green]Language set to[/green] [cyan]{choice}[/cyan]")
        except ValueError as exc:
            self.console.print(f"[red]{exc}[/red]")

    def _model_picker(self, command: str):
        """Interactive model picker.

        Usage:
            /model           — show list and prompt for selection
            /model <name>    — switch directly to a model by ID or number
        """
        from tcm.models.llm import list_models, MODEL_CATALOG, resolve_provider

        parts = command.split(maxsplit=1)
        models = list_models()
        current = self.session.current_model

        # Direct switch: /model gpt-4o  or  /model 4
        if len(parts) > 1:
            choice = parts[1].strip()
            self._apply_model_choice(choice, models, current)
            return

        # Show numbered list grouped by provider
        self.console.print()
        self.console.print(f"  Current model: [cyan]{current}[/cyan]")
        self.console.print()

        last_provider = None
        for i, m in enumerate(models, 1):
            if m.provider != last_provider:
                label = m.provider.upper()
                self.console.print(f"  [bold]{label}[/bold]")
                last_provider = m.provider
            marker = "●" if m.id == current else " "
            ctx = f"{m.context_window // 1000}k"
            self.console.print(
                f"    [dim]{i:>2}[/dim]  {marker} [cyan]{m.id:36}[/cyan] "
                f"[dim]{ctx:>5}[/dim]  {m.description}"
            )

        self.console.print()
        try:
            choice = input("  Enter number or model ID (empty to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return

        if not choice:
            return

        self._apply_model_choice(choice, models, current)

    def _apply_model_choice(self, choice: str, models: list, current: str):
        """Apply a model selection by number or name."""
        from tcm.models.llm import MODEL_CATALOG, resolve_provider

        # Try as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                self.session.set_model(selected.id)
                self.console.print(
                    f"  [green]Switched to[/green] [cyan]{selected.id}[/cyan] "
                    f"[dim]({selected.provider})[/dim]"
                )
                return
            else:
                self.console.print(f"  [yellow]Invalid number. Choose 1–{len(models)}.[/yellow]")
                return
        except ValueError:
            pass

        # Try as model ID
        model_id = choice.strip()
        provider = resolve_provider(model_id)
        if provider:
            self.session.set_model(model_id)
            in_catalog = model_id in MODEL_CATALOG
            note = f"({provider})" if in_catalog else f"({provider}, not in catalog)"
            self.console.print(
                f"  [green]Switched to[/green] [cyan]{model_id}[/cyan] [dim]{note}[/dim]"
            )
        else:
            self.console.print(
                f"  [yellow]Unknown model '{model_id}'.[/yellow] "
                f"Use a model ID from the list or a name with a recognized prefix (claude-*, gpt-*)."
            )

    def _process_query(self, query: str):
        """Process a research query through the agent pipeline."""
        from tcm.agent.planner import create_plan
        from tcm.agent.executor import execute_plan
        from tcm.agent.synthesizer import synthesize_streaming

        self.console.print()

        # Plan
        try:
            with self.console.status("[bold cyan]Planning research...[/bold cyan]"):
                plan = create_plan(self.session, query)
        except Exception as exc:
            if self._is_auth_error(exc):
                if self._handle_auth_error():
                    # Retry once
                    try:
                        with self.console.status("[bold cyan]Planning research...[/bold cyan]"):
                            plan = create_plan(self.session, query)
                    except Exception as exc2:
                        if self._is_auth_error(exc2):
                            self._handle_auth_error(prompt=False)
                            return
                        raise
                else:
                    return
            raise

        steps = plan.get("steps", [])
        if steps:
            self.console.print(f"  [dim]Plan: {len(steps)} step(s)[/dim]")

        # Execute
        with self.console.status("[bold cyan]Executing tools...[/bold cyan]"):
            results = execute_plan(self.session, plan, verbose=True)

        # Synthesize (streaming)
        self.console.print()
        answer_parts = []
        for chunk in synthesize_streaming(self.session, query, plan, results):
            answer_parts.append(chunk)
            print(chunk, end="", flush=True)
        print()

        self._last_answer = "".join(answer_parts)
        self._transcript.append(("assistant", self._last_answer))
        self.console.print()

    def _is_auth_error(self, exc: Exception) -> bool:
        err = str(exc).lower()
        return "authentication" in err or "401" in err or "invalid x-api-key" in err or "invalid api key" in err

    def _handle_auth_error(self, prompt: bool = True) -> bool:
        """Handle auth error in interactive terminal. Returns True if updated."""
        provider = self.session.config.get("llm.provider", "anthropic")
        self.console.print(f"  [red]Authentication failed[/red] for [bold]{provider}[/bold].")
        self.console.print("  Your API key is missing or invalid.")

        if prompt:
            try:
                choice = input("  Enter a new API key now? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n  [dim]Cancelled.[/dim]")
                return False
            if choice in ("y", "yes"):
                from tcm.agent.config import PROVIDER_SPECS
                label = PROVIDER_SPECS.get(provider, {}).get("label", provider.title())
                try:
                    import getpass
                    new_key = getpass.getpass(f"  Enter your {label} API key: ").strip()
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n  [dim]Cancelled.[/dim]")
                    return False
                try:
                    self.session.config.set_llm_api_key(provider, new_key)
                    self.session.config.save()
                    # Refresh LLM client
                    self.session.refresh_llm()
                    self.console.print("  [green]API key saved.[/green]")
                    return True
                except ValueError as exc:
                    self.console.print(f"[red]{exc}[/red]")
                    return False

        # Manual guidance
        if provider == "anthropic":
            self.console.print("  Fix: [cyan]tcm config set llm.api_key YOUR_KEY[/cyan]")
        elif provider == "openai":
            self.console.print("  Fix: [cyan]tcm config set llm.openai_api_key YOUR_KEY[/cyan]")
        else:
            self.console.print(f"  Fix: [cyan]tcm keys set -p {provider} --api-key YOUR_KEY[/cyan]")
        self.console.print()
        return False

    def _export_transcript(self):
        """Export session transcript to markdown file."""
        if not self._transcript:
            self.console.print("  [dim]No transcript to export.[/dim]")
            return
        path = Path.cwd() / "tcm_session.md"
        lines = ["# TCM Research Session\n"]
        for role, content in self._transcript:
            if role == "user":
                lines.append(f"\n## Query\n{content}\n")
            else:
                lines.append(f"\n## Answer\n{content}\n")
        path.write_text("\n".join(lines))
        self.console.print(f"  [green]Exported to {path}[/green]")
