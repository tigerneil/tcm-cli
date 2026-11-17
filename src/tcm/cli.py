from __future__ import annotations

"""
tcm CLI entry point.

Usage:
    tcm                              # Interactive mode
    tcm "your question"              # Single query
    tcm -i tongue.jpg "Analyze"      # Multimodal vision query
    tcm studio --open                # Launch Multimodal TCM Studio web workbench
    tcm config set key value         # Configuration
    tcm data pull tcmsp              # Data management
"""

import os
import getpass
from typing import Any, List, Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from tcm import __version__
from tcm.agent.session import Session


class TCMGroup(typer.core.TyperGroup):
    """Custom group that treats unrecognized commands as query text."""

    def invoke(self, ctx: typer.Context) -> Any:
        # If the first positional arg is not a known subcommand,
        # move everything into ctx.args so the callback handles it as a query.
        protected = getattr(ctx, "_protected_args", None)
        if protected:
            cmd_name = str(protected[0])
            if self.get_command(ctx, cmd_name) is None:
                ctx.args = [*protected, *ctx.args]
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
def model_list_cmd(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider (e.g. anthropic, openai, google, qwen, deepseek, ollama)"),
    modality: Optional[str] = typer.Option(None, "--modality", help="Filter by modality: vision | audio | pdf | thinking | video | text"),
    tier: Optional[str] = typer.Option(None, "--tier", help="Filter by model tier (frontier, flagship, balanced, fast, local, specialized)"),
):
    """List all supported models with optional provider, modality, and tier filters."""
    from tcm.models.llm import list_models
    from rich.table import Table
    from tcm.agent.config import Config

    cfg = Config.load()
    current = cfg.get("llm.model")

    try:
        models = list_models(provider=provider, modality=modality, tier=tier)
    except TypeError:
        models = list_models(provider=provider)
        if modality:
            mod_norm = modality.strip().lower()
            models = [
                m for m in models
                if mod_norm in [x.lower() for x in (getattr(m, "modalities", None) or ["text"])]
            ]

    title_parts = ["Available Models"]
    if provider:
        title_parts.append(f"provider={provider}")
    if modality:
        title_parts.append(f"modality={modality}")
    if tier:
        title_parts.append(f"tier={tier}")

    table = Table(title=" · ".join(title_parts))
    table.add_column("#", style="dim", width=3)
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider")
    table.add_column("Name")
    table.add_column("Modalities", style="magenta")
    table.add_column("Context", justify="right")
    table.add_column("$/M in", justify="right")
    table.add_column("$/M out", justify="right")
    table.add_column("Description")

    for i, m in enumerate(models, 1):
        marker = " ●" if m.id == current else ""
        ctx = f"{m.context_window:,}"
        mods = ", ".join(getattr(m, "modalities", None) or ["text"])
        table.add_row(
            str(i),
            f"{m.id}{marker}",
            m.provider,
            m.display_name,
            mods,
            ctx,
            f"${m.input_price:.2f}",
            f"${m.output_price:.2f}",
            m.description,
        )
    console.print(table)


@model_app.command("recommend")
def model_recommend_cmd(
    task: str = typer.Argument(
        "tongue_vision",
        help="TCM task: tongue_vision | herb_identification | classical_ocr | network_pharmacology | clinical_safety | bilingual_synthesis | offline_local",
    ),
    modality: Optional[str] = typer.Option(None, "--modality", help="Optional required modality (vision, audio, pdf, thinking, video)"),
):
    """Recommend top SOTA foundation models for a specific TCM modality or clinical/research task."""
    from rich.table import Table
    from tcm.agent.config import Config
    from tcm.models.multimodal import SUPPORTED_RECOMMENDATION_TASKS, recommend_models_for_task

    norm_task = task.strip().lower()
    if norm_task not in SUPPORTED_RECOMMENDATION_TASKS:
        valid = ", ".join(SUPPORTED_RECOMMENDATION_TASKS)
        console.print(f"  [yellow]Unknown task '{task}'.[/yellow] Supported tasks: [cyan]{valid}[/cyan]")
        raise typer.Exit(code=2)

    cfg = Config.load()
    mods = [modality] if modality else None
    recs = recommend_models_for_task(norm_task, modalities=mods)

    table = Table(title=f"Recommended SOTA Models for '{norm_task}'")
    table.add_column("#", style="dim", width=3)
    table.add_column("Model ID", style="cyan")
    table.add_column("Provider")
    table.add_column("Tier")
    table.add_column("Modalities", style="magenta")
    table.add_column("Score", justify="right")
    table.add_column("Key")
    table.add_column("Clinical / Research Rationale")

    for idx, rec in enumerate(recs, 1):
        prov = str(rec.get("provider", ""))
        has_key = prov == "ollama" or bool(cfg.llm_api_key(prov))
        key_badge = "[green]✓[/green]" if has_key else "[dim]○[/dim]"
        table.add_row(
            str(idx),
            str(rec.get("id", "")),
            prov,
            str(rec.get("tier", "")),
            ", ".join(rec.get("modalities", [])),
            f"{rec.get('score', 0):.1f}",
            key_badge,
            str(rec.get("reason", "")),
        )

    console.print(table)
    if recs:
        top_id = recs[0]["id"]
        console.print(f"\n  [dim]Switch with:[/dim] [cyan]tcm model set {top_id}[/cyan]")


@model_app.command("set")
def model_set_cmd(
    model: str = typer.Argument(help="Model ID to use (e.g. gpt-4o, claude-sonnet-4-5-20250929)"),
):
    """Set the active model (provider is auto-detected)."""
    from tcm.agent.config import Config
    from tcm.models.llm import MODEL_CATALOG

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


@model_app.command("google")
def model_google_cmd():
    """List models available from the Google Gemini API (requires GOOGLE_API_KEY)."""
    from tcm.models.llm import list_google_models
    from tcm.agent.config import Config
    from rich.table import Table

    cfg = Config.load()
    api_key = cfg.get("llm.google_api_key") or None

    try:
        models = list_google_models(api_key=api_key)
    except ValueError as exc:
        console.print(f"  [red]{exc}[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"  [red]Failed to list Google models: {exc}[/red]")
        raise typer.Exit(code=1)

    table = Table(title="Google Gemini Models (live from API)")
    table.add_column("Model ID", style="cyan")
    table.add_column("Display Name")
    table.add_column("Context In", justify="right")
    table.add_column("Context Out", justify="right")
    table.add_column("Description")

    for m in models:
        in_tok = str(m["input_token_limit"]) if m["input_token_limit"] else "-"
        out_tok = str(m["output_token_limit"]) if m["output_token_limit"] else "-"
        table.add_row(
            m["id"],
            m["display_name"] or "",
            in_tok,
            out_tok,
            (m["description"] or "")[:60],
        )
    console.print(table)
    console.print(f"\n  [dim]{len(models)} models returned. Use 'tcm model set <model-id>' to switch.[/dim]")


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
        mods = ", ".join(getattr(info, "modalities", None) or ["text"])
        console.print(f"  Modalities: {mods}")
        console.print(f"  Context:  {info.context_window:,} tokens")
        console.print(f"  Pricing:  ${info.input_price:.2f} / ${info.output_price:.2f} per M tokens")
    else:
        console.print("  [dim](model not in catalog)[/dim]")


# ─── Studio command ───────────────────────────────────────────

@app.command("studio")
def studio_cmd(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host interface to bind"),
    port: int = typer.Option(8765, "--port", "-p", help="TCP port to bind"),
    open_browser: bool = typer.Option(False, "--open/--no-open", help="Open Multimodal TCM Studio in default web browser"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="SOTA LLM model ID to activate for Studio"),
    language: Optional[str] = typer.Option(None, "--language", "--lang", help="Default Studio language: en | zh | bi"),
):
    """Launch the local Multimodal TCM Studio web workbench and REST API server."""
    import threading
    import webbrowser
    from tcm.agent.config import Config
    from tcm.studio.server import create_studio_server

    cfg = Config.load()
    if model:
        cfg.set("llm.model", model)
    if language:
        try:
            cfg.set("ui.language", language.lower())
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=2)

    session = Session(config=cfg)
    try:
        server = create_studio_server(host=host, port=port, session=session)
    except OSError as exc:
        console.print(f"  [red]Failed to bind TCM Studio on {host}:{port}:[/red] {exc}")
        raise typer.Exit(code=1)

    site_url = f"{server.base_url}/"
    studio_url = f"{server.base_url}/studio"
    health_url = f"{server.base_url}/api/health"
    provider = session.config.get("llm.provider", "anthropic")
    tools_total = _count_tools()

    console.print()
    console.print(Panel(
        f"[bold #c8a85c]TCM Studio v{__version__} — Multimodal Research & Clinical Workbench[/bold #c8a85c]\n\n"
        f"  [bold]Official Website:[/bold]           [link={site_url}][cyan]{site_url}[/cyan][/link]\n"
        f"  [bold]Multimodal Studio App:[/bold]      [link={studio_url}][bold green]{studio_url}[/bold green][/link]\n"
        f"  [bold]REST API Health:[/bold]            [link={health_url}][dim]{health_url}[/dim][/link]\n\n"
        f"  [bold]Active SOTA Model:[/bold]          [cyan]{session.current_model}[/cyan] [dim]({provider})[/dim]\n"
        f"  [bold]Computational TCM Tools:[/bold]    [green]{tools_total}[/green] tools ready\n\n"
        f"  [dim]Press Ctrl+C to stop the server.[/dim]",
        title="[bold #c8a85c]tcm studio[/bold #c8a85c]",
        border_style="#c8a85c",
    ))

    if open_browser:
        timer = threading.Timer(0.35, lambda: webbrowser.open(studio_url))
        timer.daemon = True
        timer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n  [dim]Shutting down TCM Studio...[/dim]")
    finally:
        server.server_close()


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


def _attach_cli_inputs(
    session: Session,
    images: Optional[List[Path]] = None,
    audios: Optional[List[Path]] = None,
    files: Optional[List[Path]] = None,
) -> None:
    """Validate and attach CLI --image / --audio / --file inputs to the session."""
    for group in (images or [], audios or [], files or []):
        for path in group:
            expanded = path.expanduser()
            if not expanded.exists():
                console.print(f"[red]Attachment file not found:[/red] {expanded}")
                raise typer.Exit(code=2)
            session.add_attachment(expanded)


# ─── Default callback (interactive mode or single query) ──────

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use"),
    continue_session: bool = typer.Option(False, "--continue", "-c", help="Continue last session"),
    language: Optional[str] = typer.Option(None, "--language", "--lang", help="Response language: en | zh | bi"),
    image: Optional[List[Path]] = typer.Option(None, "--image", "-i", help="Attach image(s) for multimodal vision analysis (e.g. tongue/herb photo)"),
    audio: Optional[List[Path]] = typer.Option(None, "--audio", help="Attach audio recording(s) for auscultation/voice analysis"),
    file: Optional[List[Path]] = typer.Option(None, "--file", "-f", help="Attach PDF/document/prescription file(s)"),
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
    _attach_cli_inputs(session, images=image, audios=audio, files=file)

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

    attachments = session.active_attachments() or None

    try:
        with console.status("[bold cyan]Planning...[/bold cyan]"):
            plan = create_plan(session, query, attachments=attachments)
    except Exception as exc:
        if _is_auth_error(exc):
            if _handle_auth_error(session):
                # Retry once after updating credentials
                try:
                    with console.status("[bold cyan]Planning...[/bold cyan]"):
                        plan = create_plan(session, query, attachments=attachments)
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
    for chunk in synthesize_streaming(session, query, plan, results, attachments=attachments):
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
        from tcm.studio.server import _ensure_all_tools_loaded
        from tcm.tools import registry
        _ensure_all_tools_loaded()
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
