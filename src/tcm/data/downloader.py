"""
Dataset download and management for tcm.

Supports three install modes:
- bundled   : serialised from in-memory tool data (herbs, formulas)
- http      : streamed HTTP download with progress bar, auto-extracted
- manual    : guided instructions + `tcm data import` to register a local file
"""

import json
import logging
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from tcm.agent.config import Config, CONFIG_DIR

logger = logging.getLogger("tcm.data.downloader")
console = Console()

# download_url values:
#   "bundled"  — generated from in-memory package data
#   <https://…> — direct file URL, downloaded automatically
#   None       — no direct URL; show guided manual instructions
DATASETS: dict[str, dict] = {
    "herbs": {
        "name": "Herb Monographs",
        "description": "Chinese Materia Medica herb database — properties, functions, compounds",
        "homepage": None,
        "download_url": "bundled",
        "filename": "herbs.json",
        "size": "~1 MB",
        "extract": False,
    },
    "formulas": {
        "name": "Classical Formulas",
        "description": "Classical formula database with 君臣佐使 compositions",
        "homepage": None,
        "download_url": "bundled",
        "filename": "formulas.json",
        "size": "~1 MB",
        "extract": False,
    },
    "tcmsp": {
        "name": "TCMSP",
        "description": "Traditional Chinese Medicine Systems Pharmacology — herbs, compounds, targets",
        "homepage": "https://old.tcmsp-e.com/",
        "download_url": None,  # requires free registration
        "filename": None,
        "size": "~50 MB",
        "extract": True,
        "manual_note": "Requires free registration at https://old.tcmsp-e.com/",
    },
    "tcmid": {
        "name": "TCMID",
        "description": "Traditional Chinese Medicine Integrated Database — herb-compound-disease",
        "homepage": "http://www.megabionet.org/tcmid/",
        "download_url": None,
        "filename": None,
        "size": "~30 MB",
        "extract": True,
        "manual_note": "Available at http://www.megabionet.org/tcmid/ (registration may be required)",
    },
    "batman": {
        "name": "BATMAN-TCM",
        "description": "Bioinformatics Analysis Tool for Molecular mechANism of TCM",
        "homepage": "http://bionet.ncpsb.org.cn/batman-tcm/",
        "download_url": None,
        "filename": None,
        "size": "~100 MB",
        "extract": True,
        "manual_note": "Available at http://bionet.ncpsb.org.cn/batman-tcm/ (registration required)",
    },
    "symmap": {
        "name": "SymMap",
        "description": "Symptom mapping database — TCM symptoms to herbs and modern diseases",
        "homepage": "https://www.symmap.org/",
        "download_url": None,
        "filename": None,
        "size": "~20 MB",
        "extract": True,
        "manual_note": "Available at https://www.symmap.org/download/ (free account required)",
    },
}


# ── Public API ────────────────────────────────────────────────

def download_dataset(dataset: str, output: Optional[Path] = None, force: bool = False) -> bool:
    """Download / install a dataset.  Returns True on success."""
    ds = DATASETS.get(dataset.lower())
    if not ds:
        console.print(f"[red]Unknown dataset '{dataset}'.[/red]")
        console.print(f"  Available: {', '.join(DATASETS.keys())}")
        return False

    output = output or Path(CONFIG_DIR / "data" / dataset)
    output.mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(f"  [bold]{ds['name']}[/bold]  [dim]{ds['description']}[/dim]")
    console.print(f"  Destination: {output}")

    if not force and _is_installed(output):
        console.print("  [green]✓ Already installed.[/green]  Pass --force to reinstall.")
        _save_config(dataset, output)
        return True

    download_url = ds.get("download_url")

    if download_url == "bundled":
        ok = _install_bundled(dataset, output, ds)
    elif download_url:
        ok = _http_download(dataset, download_url, output, ds)
    else:
        ok = _guided_install(dataset, output, ds)

    if ok:
        _save_config(dataset, output)
    return ok


def import_dataset(dataset: str, path: Path) -> bool:
    """Register an existing local file or directory as a dataset."""
    ds = DATASETS.get(dataset.lower())
    if not ds:
        console.print(f"[red]Unknown dataset '{dataset}'.[/red]")
        console.print(f"  Available: {', '.join(DATASETS.keys())}")
        return False

    path = path.resolve()
    if not path.exists():
        console.print(f"[red]Path does not exist: {path}[/red]")
        return False

    dest = Path(CONFIG_DIR / "data" / dataset)

    if path.is_dir():
        _save_config(dataset, path)
        console.print(f"  [green]✓ Registered directory: {path}[/green]")
        return True

    # It’s a file — try to extract it
    dest.mkdir(parents=True, exist_ok=True)
    extracted = _extract_archive(path, dest)
    if not extracted:
        # Plain file — just copy it
        shutil.copy2(path, dest / path.name)
        console.print(f"  [green]✓ Copied {path.name} → {dest}[/green]")
    _save_config(dataset, dest)
    return True


def dataset_status() -> Table:
    """Show status of local datasets."""
    config = Config.load()
    table = Table(title="Local Datasets")
    table.add_column("Dataset", style="cyan")
    table.add_column("Install", style="dim")
    table.add_column("Status")
    table.add_column("Path", style="dim")

    for key, ds in DATASETS.items():
        data_path = config.get(f"data.{key}")
        dl = ds.get("download_url")
        install_type = "bundled" if dl == "bundled" else "http" if dl else "manual"

        if data_path and Path(data_path).exists() and _is_installed(Path(data_path)):
            status = "[green]✓ installed[/green]"
            path_str = data_path
        else:
            status = "[dim]○ not installed[/dim]"
            path_str = "-"
        table.add_row(ds["name"], install_type, status, path_str)

    return table


# ── Internal helpers ──────────────────────────────────────────

def _is_installed(output: Path) -> bool:
    """Return True if the dataset directory is non-empty."""
    return output.exists() and any(output.iterdir())


def _save_config(dataset: str, output: Path) -> None:
    """Persist the dataset path in ~/.tcm/config.json."""
    cfg = Config.load()
    cfg.set(f"data.{dataset}", str(output))
    cfg.save()


def _install_bundled(dataset: str, output: Path, ds: dict) -> bool:
    """Serialise in-memory tool data to a JSON file on disk."""
    try:
        if dataset == "herbs":
            from tcm.tools.herbs import HERB_DB as data  # type: ignore
        elif dataset == "formulas":
            from tcm.tools.formulas import FORMULA_DB as data  # type: ignore
        else:
            console.print(f"[red]No bundled data available for '{dataset}'.[/red]")
            return False

        filename = ds.get("filename", f"{dataset}.json")
        out_file = output / filename
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        console.print(f"  [green]✓ Installed {len(data)} entries → {out_file}[/green]")
        return True

    except Exception as exc:
        console.print(f"  [red]Failed: {exc}[/red]")
        logger.exception("Bundled install failed for %s", dataset)
        return False


def _http_download(dataset: str, url: str, output: Path, ds: dict) -> bool:
    """Stream-download a file with a rich progress bar, then extract."""
    filename = ds.get("filename") or url.rsplit("/", 1)[-1] or f"{dataset}.bin"
    dest_file = output / filename

    console.print(f"  Downloading: [link={url}]{url}[/link]")
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=120) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0)) or None

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(ds["name"], total=total)
                with dest_file.open("wb") as fh:
                    for chunk in resp.iter_bytes(chunk_size=65_536):
                        fh.write(chunk)
                        progress.update(task, advance=len(chunk))

    except httpx.HTTPStatusError as exc:
        console.print(f"  [red]HTTP {exc.response.status_code}: download failed.[/red]")
        return False
    except httpx.RequestError as exc:
        console.print(f"  [red]Network error: {exc}[/red]")
        return False

    console.print(f"  [green]✓ Downloaded → {dest_file}[/green]")

    if ds.get("extract"):
        _extract_archive(dest_file, output, remove_after=True)

    return True


def _extract_archive(archive: Path, dest: Path, remove_after: bool = False) -> bool:
    """Extract ZIP or tar archive into dest.  Returns True if handled."""
    name = archive.name.lower()
    try:
        if name.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest)
            console.print(f"  [green]✓ Extracted ZIP → {dest}[/green]")
        elif any(name.endswith(s) for s in (".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
            with tarfile.open(archive) as tf:
                tf.extractall(dest)
            console.print(f"  [green]✓ Extracted tar → {dest}[/green]")
        else:
            return False  # not a recognised archive

        if remove_after:
            archive.unlink(missing_ok=True)
        return True

    except Exception as exc:
        console.print(f"  [red]Extraction failed: {exc}[/red]")
        logger.exception("Extraction failed for %s", archive)
        return False


def _guided_install(dataset: str, output: Path, ds: dict) -> bool:
    """Print step-by-step manual instructions for datasets without a direct URL."""
    note = ds.get("manual_note", f"Download from {ds.get('homepage', 'the vendor website')}.")
    console.print()
    console.print(f"  [yellow]⚠  Automated download unavailable for {ds['name']}.[/yellow]")
    console.print(f"  {note}")
    console.print()
    console.print("  [bold]Steps:[/bold]")
    console.print(f"  1. Download the archive ({ds['size']}) from the link above.")
    console.print(f"  2. Run:")
    console.print(f"       tcm data import {dataset} /path/to/downloaded/file")
    console.print(f"     or, if already extracted:")
    console.print(f"       tcm data import {dataset} /path/to/extracted/folder")
    console.print()
    return False
