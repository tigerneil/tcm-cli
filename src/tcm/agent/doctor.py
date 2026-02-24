"""
Health checks for tcm CLI.
"""

import shutil
import sys
from rich.table import Table


def run_checks(config, session=None) -> list[dict]:
    """Run all health checks. Returns list of check results."""
    checks = []

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    checks.append({
        "name": "Python version",
        "status": "ok" if py_ok else "error",
        "detail": f"Python {py_ver}" + ("" if py_ok else " (need 3.10+)"),
    })

    # Anthropic API key
    key = config.llm_api_key("anthropic")
    checks.append({
        "name": "Anthropic API key",
        "status": "ok" if key else "error",
        "detail": "configured" if key else "missing — run `tcm setup`",
    })

    # Core dependencies
    for pkg in ["anthropic", "rich", "typer", "httpx", "prompt_toolkit"]:
        try:
            __import__(pkg)
            checks.append({"name": f"Package: {pkg}", "status": "ok", "detail": "installed"})
        except ImportError:
            checks.append({"name": f"Package: {pkg}", "status": "error", "detail": "not installed"})

    # Optional dependencies
    for pkg, label in [("pandas", "pandas"), ("numpy", "numpy"), ("rdkit", "RDKit (chemistry)")]:
        try:
            __import__(pkg)
            checks.append({"name": f"Optional: {label}", "status": "ok", "detail": "installed"})
        except ImportError:
            checks.append({"name": f"Optional: {label}", "status": "info", "detail": "not installed (optional)"})

    # Tool loading
    from tcm.tools import ensure_loaded, tool_load_errors
    ensure_loaded()
    errors = tool_load_errors()
    if errors:
        checks.append({
            "name": "Tool modules",
            "status": "warn",
            "detail": f"{len(errors)} module(s) failed to load: {', '.join(errors.keys())}",
        })
    else:
        from tcm.tools import registry
        checks.append({
            "name": "Tool modules",
            "status": "ok",
            "detail": f"{len(registry.list_tools())} tools loaded",
        })

    return checks


def to_table(checks: list[dict]) -> Table:
    """Render checks as a Rich table."""
    table = Table(title="tcm doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail")

    for check in checks:
        status = check["status"]
        if status == "ok":
            icon = "[green]✓[/green]"
        elif status == "warn":
            icon = "[yellow]⚠[/yellow]"
        elif status == "info":
            icon = "[dim]○[/dim]"
        else:
            icon = "[red]✗[/red]"
        table.add_row(check["name"], icon, check["detail"])

    return table


def has_errors(checks: list[dict]) -> bool:
    """Check if any health check failed."""
    return any(c["status"] == "error" for c in checks)
