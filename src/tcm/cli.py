"""
tcm CLI entry point.

Usage:
    tcm                              # Interactive mode
    tcm "your question"              # Single query
    tcm config set key value         # Configuration
    tcm data pull tcmsp              # Data management
"""

import os
import sys
import getpass
from typing import Any, Optional
from pathlib import Path

import click
import typer
from rich.console import Console
from rich.panel import Panel

from tcm import __version__
from tcm.agent.session import Session


class TCMGroup(typer.core.TyperGroup):
    """Custom group that treats unrecognized commands as query text."""

    def invoke(self, ctx: click.Context) -> Any:
        # If the first positional arg is not a known subcommand,
        # move everything into ctx.args so the callback handles it as a query.
        if ctx._protected_args:
            cmd_name = click.utils.make_str(ctx._protected_args[0])
            if self.get_command(ctx, cmd_name) is None:
                ctx.args = [*ctx._protected_args, *ctx.args]
                ctx._protected_args = []
        return super().invoke(ctx)

BANNER = """
[bold #c8a85c]████████╗ ██████╗███╗   ███╗[/]
[bold #d4b56a]╚══██╔══╝██╔════╝████╗ ████║[/]
[bold #e0c278]   ██║   ██║     ██╔████╔██║[/]
[bold #ccae66]   ██║   ██║     ██║╚██╔╝██║[/]
[bold #b89a54]   ██║   ╚██████╗██║ ╚═╝ ██║[/]
[bold #a48642]   ╚═╝    ╚═════╝╚═╝     ╚═╝[/]
"""

app = typer.Typer(
    name="tcm",
    cls=TCMGroup,
    help=(
        "TCM CLI — An autonomous agent for Traditional Chinese Medicine research.\n\n"
        "Common usage:\n"
        '  tcm "your research question"\n'
        "  tcm config show\n"
        "  tcm tool list"
    ),
    no_args_is_help=False,
    context_settings={"allow_extra_args": True, "allow_interspersed_args": False},
)
console = Console()


# ─── Config subcommand ────────────────────────────────────────

config_app = typer.Typer(help="Manage tcm configuration")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(key: str, value: str):
    """Set a configuration value."""
    from tcm.agent.config import Config
    cfg = Config.load()
    try:
        cfg.set(key, value)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2)
    cfg.save()
    console.print(f"  [green]Set[/green] {key} = {value}")


@config_app.command("get")
def config_get(key: str):
    """Get a configuration value."""
    from tcm.agent.config import Config
    cfg = Config.load()
    val = cfg.get(key)
    console.print(f"  {key} = {val}")


@config_app.command("show")
def config_show():
    """Show all configuration."""
    from tcm.agent.config import Config
    cfg = Config.load()
    console.print(cfg.to_table())


@config_app.command("validate")
def config_validate():
    """Validate configuration and report issues."""
    from tcm.agent.config import Config
    cfg = Config.load()
    issues = cfg.validate()
    if not issues:
        console.print("[green]Configuration is valid.[/green]")
        return
    console.print(f"[yellow]Found {len(issues)} issue(s):[/yellow]")
    for issue in issues:
        console.print(f"  - {issue}")
    raise typer.Exit(code=2)


# ─── Setup command ────────────────────────────────────────────

@app.command("setup")
def setup_cmd(
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Anthropic API key (non-interactive)"),
):
    """Interactive setup wizard — configure tcm for first use."""
    from tcm.agent.config import Config

    cfg = Config.load()

    console.print()
    console.print(Panel(
        "[bold]Welcome to TCM CLI[/bold]\n\n"
        "This wizard will configure tcm for first use.\n"
        "You need an Anthropic API key to get started.",
        title="[#c8a85c]tcm setup[/#c8a85c]",
        border_style="#c8a85c",
    ))
    console.print()

    existing_key = cfg.llm_api_key()

    if api_key:
        chosen_key = api_key
    elif existing_key:
        masked = existing_key[:7] + "..." + existing_key[-4:] if len(existing_key) > 11 else "***"
        console.print(f"  API key already configured: [green]{masked}[/green]")
        try:
            keep = input("  Keep existing key? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]Setup cancelled.[/dim]")
            raise typer.Exit()
        if keep in ("", "y", "yes"):
            chosen_key = existing_key
        else:
            chosen_key = _prompt_api_key()
    else:
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            masked = env_key[:7] + "..." + env_key[-4:] if len(env_key) > 11 else "***"
            console.print(f"  Found ANTHROPIC_API_KEY in environment: [green]{masked}[/green]")
            try:
                save_it = input("  Save to tcm config? [Y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                console.print("\n  [dim]Setup cancelled.[/dim]")
                raise typer.Exit()
            if save_it in ("", "y", "yes"):
                chosen_key = env_key
            else:
                chosen_key = _prompt_api_key()
        else:
            chosen_key = _prompt_api_key()

    cfg.set("llm.api_key", chosen_key)
    cfg.set("llm.provider", "anthropic")
    cfg.save()
    console.print("\n  [green]API key saved to ~/.tcm/config.json[/green]")

    # Health check
    console.print("\n  [cyan]Running health check...[/cyan]")
    from tcm.agent.doctor import run_checks, to_table, has_errors
    checks = run_checks(cfg)
    console.print(to_table(checks))

    if has_errors(checks):
        console.print("\n  [yellow]Some issues detected.[/yellow] Run `tcm doctor` for details.")
    else:
        console.print("\n  [green]All checks passed.[/green]")

    console.print()
    console.print(Panel(
        "[bold green]You're all set![/bold green]\n\n"
        "  [cyan]tcm[/cyan]                      Interactive mode\n"
        '  [cyan]tcm "your question"[/cyan]      Single query\n'
        "  [cyan]tcm doctor[/cyan]               Full health check\n"
        "  [cyan]tcm tool list[/cyan]            Available tools",
        title="[green]Quick Start[/green]",
        border_style="green",
    ))


def _prompt_api_key() -> str:
    """Prompt user for API key."""
    console.print("  Get your key at: [link=https://console.anthropic.com/settings/keys]console.anthropic.com/settings/keys[/link]")
    console.print()
    try:
        key = getpass.getpass("  Enter your Anthropic API key: ")
    except (EOFError, KeyboardInterrupt):
        console.print("\n  [dim]Setup cancelled.[/dim]")
        raise typer.Exit()
    return key.strip()


# ─── Doctor command ───────────────────────────────────────────

@app.command("doctor")
def doctor_cmd():
    """Run environment and configuration health checks."""
    from tcm.agent.config import Config
    from tcm.agent.doctor import run_checks, to_table, has_errors

    cfg = Config.load()
    checks = run_checks(cfg)
    console.print(to_table(checks))

    if has_errors(checks):
        console.print("\n[red]Blocking issues found.[/red] Fix errors above, then rerun `tcm doctor`.")
        raise typer.Exit(code=1)
    console.print("\n[green]No blocking issues.[/green]")


# ─── Keys subcommands ────────────────────────────────────────

keys_app = typer.Typer(help="Manage API keys for LLM providers")
app.add_typer(keys_app, name="keys")

@keys_app.callback(invoke_without_command=True)
def keys_default(ctx: typer.Context):
    """Default action shows key status when no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    from tcm.agent.config import Config
    cfg = Config.load()
    console.print(cfg.keys_table())

@keys_app.command("show")
def keys_show_cmd():
    """Show status of API keys."""
    from tcm.agent.config import Config
    cfg = Config.load()
    console.print(cfg.keys_table())

@keys_app.command("set")
def keys_set_cmd(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider to set (e.g. anthropic, openai, google, mistral, groq, cohere, together, ollama)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key value (omit to be prompted securely)"),
    make_default: bool = typer.Option(False, "--make-default", help="Also set llm.provider to this provider (only if supported)"),
):
    """Set the API key for a given provider. Interactive if options omitted."""
    from tcm.agent.config import Config, PROVIDER_SPECS, VALID_LLM_PROVIDERS

    cfg = Config.load()

    # Choose provider interactively if not specified
    prov = (provider or "").strip().lower()
    if not prov:
        console.print("  Choose a provider to configure:\n")
        items = list(PROVIDER_SPECS.items())
        # Primary first
        items.sort(key=lambda kv: (0 if kv[1].get("primary") else 1, kv[0]))
        for idx, (name, spec) in enumerate(items, 1):
            label = spec.get("label", name.title())
            note = " (primary)" if spec.get("primary") else ""
            console.print(f"   {idx}. {label}{note}")
        console.print()
        try:
            choice = input("  Enter number: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]Cancelled.[/dim]")
            raise typer.Exit()
        try:
            idx = int(choice)
            if idx < 1 or idx > len(items):
                raise ValueError
        except ValueError:
            console.print("  [red]Invalid selection[/red]")
            raise typer.Exit(code=2)
        prov = items[idx - 1][0]

    if prov == "ollama":
        console.print("  [yellow]Ollama typically does not require an API key.[/yellow]")
        try:
            confirm = input("  Save a placeholder anyway? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]Cancelled.[/dim]")
            raise typer.Exit()
        if confirm not in ("y", "yes"):
            console.print("  [dim]No changes made.[/dim]")
            return

    # Prompt for key if not provided
    key_val = api_key
    if key_val is None:
        label = PROVIDER_SPECS.get(prov, {}).get("label", prov.title())
        try:
            key_val = getpass.getpass(f"  Enter your {label} API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]Cancelled.[/dim]")
            raise typer.Exit()

    # Save
    try:
        cfg.set_llm_api_key(prov, key_val)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2)
    cfg.save()

    masked = (key_val[:7] + "..." + key_val[-4:]) if key_val and len(key_val) > 11 else ("***" if key_val else "(cleared)")
    console.print(f"  [green]Saved[/green] key for provider [bold]{prov}[/bold]: {masked}")

    # Optionally set as default provider (only for runtime-supported ones)
    if make_default:
        if prov in VALID_LLM_PROVIDERS:
            try:
                cfg.set("llm.provider", prov)
                cfg.save()
                console.print(f"  [green]Default provider set to[/green] {prov}")
            except ValueError as exc:
                console.print(f"[red]{exc}[/red]")
                raise typer.Exit(code=2)
        else:
            console.print(
                f"  [yellow]Note:[/yellow] {prov} keys saved, but runtime provider support is not enabled yet."
            )


# ─── Data subcommand ─────────────────────────────────────────

data_app = typer.Typer(help="Manage local datasets")
app.add_typer(data_app, name="data")


@data_app.command("pull")
def data_pull(
    dataset: str = typer.Argument(help="Dataset to install (herbs, formulas, tcmsp, tcmid, batman, symmap)"),
    output: Optional[Path] = typer.Option(None, help="Output directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-install even if already present"),
):
    """Download or install a dataset for local use."""
    from tcm.data.downloader import download_dataset
    ok = download_dataset(dataset, output, force=force)
    if not ok:
        raise typer.Exit(code=1)


@data_app.command("import")
def data_import(
    dataset: str = typer.Argument(help="Dataset name (tcmsp, tcmid, batman, symmap, ...)"),
    path: Path = typer.Argument(help="Path to downloaded archive or extracted directory"),
):
    """Register a manually downloaded dataset file or directory."""
    from tcm.data.downloader import import_dataset
    ok = import_dataset(dataset, path)
    if not ok:
        raise typer.Exit(code=1)


@data_app.command("status")
def data_status():
    """Show status of local datasets."""
    from tcm.data.downloader import dataset_status
    console.print(dataset_status())


# ─── Tool subcommand ─────────────────────────────────────────

tool_app = typer.Typer(help="Run individual tools")
app.add_typer(tool_app, name="tool")


@tool_app.command("list")
def tool_list():
    """List all available tools."""
    from tcm.tools import registry, ensure_loaded, tool_load_errors
    ensure_loaded()
    console.print(registry.list_tools_table())
    errors = tool_load_errors()
    if errors:
        console.print(f"[yellow]Warning:[/yellow] {len(errors)} tool module(s) failed to load")


# ─── Model subcommand ─────────────────────────────────────────

model_app = typer.Typer(help="Manage LLM model selection")
app.add_typer(model_app, name="model")


@model_app.command("list")
def model_list_cmd():
    """List all supported models."""
    from tcm.models.llm import list_models
    from rich.table import Table

    from tcm.agent.config import Config
    cfg = Config.load()
    current = cfg.get("llm.model")

    table = Table(title="Available Models")
    table.add_column("#", style="dim", width=3)
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider")
    table.add_column("Name")
    table.add_column("Context", justify="right")
    table.add_column("$/M in", justify="right")
    table.add_column("$/M out", justify="right")
    table.add_column("Description")

    for i, m in enumerate(list_models(), 1):
        marker = " ●" if m.id == current else ""
        ctx = f"{m.context_window:,}"
        table.add_row(
            str(i),
            f"{m.id}{marker}",
            m.provider,
            m.display_name,
            ctx,
            f"${m.input_price:.2f}",
            f"${m.output_price:.2f}",
            m.description,
        )
    console.print(table)


@model_app.command("set")
def model_set_cmd(
    model: str = typer.Argument(help="Model ID to use (e.g. gpt-4o, claude-sonnet-4-5-20250929)"),
):
    """Set the active model (provider is auto-detected)."""
    from tcm.agent.config import Config
    from tcm.models.llm import resolve_provider, MODEL_CATALOG

    cfg = Config.load()
    cfg.set("llm.model", model)
    cfg.save()

    provider = cfg.get("llm.provider")
    if model in MODEL_CATALOG:
        console.print(f"  [green]Model set to[/green] {model} [dim](provider: {provider})[/dim]")
    else:
        console.print(
            f"  [yellow]Model set to[/yellow] {model} [dim](not in catalog — provider: {provider})[/dim]\n"
            f"  [dim]This model may still work if your provider supports it.[/dim]"
        )


@model_app.command("show")
def model_show_cmd():
    """Show current model and provider."""
    from tcm.agent.config import Config
    from tcm.models.llm import MODEL_CATALOG

    cfg = Config.load()
    model = cfg.get("llm.model")
    provider = cfg.get("llm.provider")
    info = MODEL_CATALOG.get(model)

    console.print(f"  Model:    [cyan]{model}[/cyan]")
    console.print(f"  Provider: {provider}")
    if info:
        console.print(f"  Name:     {info.display_name}")
        console.print(f"  Context:  {info.context_window:,} tokens")
        console.print(f"  Pricing:  ${info.input_price:.2f} / ${info.output_price:.2f} per M tokens")
    else:
        console.print("  [dim](model not in catalog)[/dim]")


# ─── Report subcommand ───────────────────────────────────────

report_app = typer.Typer(help="Manage research reports")
app.add_typer(report_app, name="report")


@report_app.command("list")
def report_list():
    """List saved reports."""
    reports_dir = Path.cwd() / "outputs"
    if not reports_dir.exists():
        console.print("  [dim]No reports found.[/dim]")
        return
    md_files = sorted(reports_dir.glob("*.md"), reverse=True)
    if not md_files:
        console.print("  [dim]No reports found.[/dim]")
        return
    for f in md_files[:20]:
        console.print(f"  {f.name}")


# ─── Version command ──────────────────────────────────────────

@app.command("version")
def version_cmd():
    """Show tcm version."""
    console.print(f"tcm-cli v{__version__}")


# ─── Default callback (interactive mode or single query) ──────

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use"),
    continue_session: bool = typer.Option(False, "--continue", "-c", help="Continue last session"),
    language: Optional[str] = typer.Option(None, "--language", "--lang", help="Response language: en | zh | bi"),
):
    """TCM CLI — Traditional Chinese Medicine research agent."""
    if ctx.invoked_subcommand is not None:
        return

    # Collect positional args as the query string (avoids conflict with subcommand routing)
    query = " ".join(ctx.args).strip() if ctx.args else None

    from tcm.agent.config import Config
    cfg = Config.load()

    if model:
        cfg.set("llm.model", model)
    if language:
        try:
            cfg.set("ui.language", language.lower())
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=2)

    session = Session(config=cfg, verbose=verbose)

    if query:
        # Single query mode
        _run_single_query(session, query, verbose)
    else:
        # Interactive mode
        _run_interactive(session)


def _run_single_query(session: Session, query: str, verbose: bool):
    """Execute a single query and print result."""
    from tcm.agent.planner import create_plan
    from tcm.agent.executor import execute_plan
    from tcm.agent.synthesizer import synthesize_streaming

    try:
        with console.status("[bold cyan]Planning...[/bold cyan]"):
            plan = create_plan(session, query)
    except Exception as exc:
        if _is_auth_error(exc):
            if _handle_auth_error(session):
                # Retry once after updating credentials
                try:
                    with console.status("[bold cyan]Planning...[/bold cyan]"):
                        plan = create_plan(session, query)
                except Exception as exc2:
                    if _is_auth_error(exc2):
                        # Show help and exit
                        _handle_auth_error(session, prompt=False)
                        raise typer.Exit(code=1)
                    raise
            else:
                raise typer.Exit(code=1)
        raise

    steps = plan.get("steps", [])
    if steps and verbose:
        console.print(f"  [dim]Plan: {len(steps)} step(s)[/dim]")

    with console.status("[bold cyan]Executing...[/bold cyan]"):
        results = execute_plan(session, plan, verbose=verbose)

    console.print()
    for chunk in synthesize_streaming(session, query, plan, results):
        print(chunk, end="", flush=True)
    print()

    # Show usage
    llm = session.get_llm()
    if llm.usage.calls:
        console.print(f"\n  [dim]{llm.usage.summary()}[/dim]")


def _run_interactive(session: Session):
    """Launch interactive terminal."""
    console.print(BANNER)
    console.print(
        f"  [bold]TCM CLI[/bold] v{__version__} | "
        f"model: [cyan]{session.current_model}[/cyan] | "
        f"tools: [green]{_count_tools()}[/green]"
    )
    console.print(
        "  Type your research question, /help for commands, /exit to quit."
    )

    from tcm.ui.terminal import InteractiveTerminal
    terminal = InteractiveTerminal(session)
    terminal.run()


def _count_tools() -> int:
    """Count available tools."""
    try:
        from tcm.tools import registry, ensure_loaded
        ensure_loaded()
        return len(registry.list_tools())
    except Exception:
        return 0


def _is_auth_error(exc: Exception) -> bool:
    """Check if an exception is an authentication error."""
    err = str(exc).lower()
    return "authentication" in err or "401" in err or "invalid x-api-key" in err or "invalid api key" in err


def _handle_auth_error(session: Session, prompt: bool = True) -> bool:
    """Handle authentication failure.

    If prompt is True, offer to capture and save the API key interactively.
    Returns True if credentials were updated, else False.
    """
    provider = session.config.get("llm.provider", "anthropic")
    console.print()
    console.print(f"  [red]Authentication failed[/red] for provider [bold]{provider}[/bold].")
    console.print("  Your API key is missing or invalid.")
    console.print()

    if prompt:
        try:
            choice = input("  Enter a new API key now? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]Cancelled.[/dim]")
            return False
        if choice in ("y", "yes"):
            from tcm.agent.config import PROVIDER_SPECS
            label = PROVIDER_SPECS.get(provider, {}).get("label", provider.title())
            try:
                new_key = getpass.getpass(f"  Enter your {label} API key: ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n  [dim]Cancelled.[/dim]")
                return False
            try:
                session.config.set_llm_api_key(provider, new_key)
                session.config.save()
                # Recreate client with new credentials
                session.refresh_llm()
                console.print("  [green]API key saved.[/green]")
                return True
            except ValueError as exc:
                console.print(f"[red]{exc}[/red]")
                return False

    # Guidance for manual setup
    if provider == "anthropic":
        console.print("  To fix, run one of:")
        console.print('    [cyan]tcm config set llm.api_key YOUR_KEY[/cyan]')
        console.print('    [cyan]export ANTHROPIC_API_KEY=YOUR_KEY[/cyan]')
        console.print("  Get a key at: [link=https://console.anthropic.com/settings/keys]console.anthropic.com/settings/keys[/link]")
    elif provider == "openai":
        console.print("  To fix, run one of:")
        console.print('    [cyan]tcm config set llm.openai_api_key YOUR_KEY[/cyan]')
        console.print('    [cyan]export OPENAI_API_KEY=YOUR_KEY[/cyan]')
        console.print("  Get a key at: [link=https://platform.openai.com/api-keys]platform.openai.com/api-keys[/link]")
    else:
        console.print("  To fix, run:")
        console.print(f"    [cyan]tcm keys set -p {provider} --api-key YOUR_KEY[/cyan]")
        console.print("  Or set the provider-specific environment variable (see `tcm keys show`).")
    console.print()
    return False


def entry():
    """Package entry point."""
    app()
