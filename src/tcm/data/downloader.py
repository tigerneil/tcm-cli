"""
Dataset download and management for tcm.
"""

import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table

from tcm.agent.config import Config, CONFIG_DIR

logger = logging.getLogger("tcm.data.downloader")
console = Console()

DATASETS = {
    "tcmsp": {
        "name": "TCMSP",
        "description": "Traditional Chinese Medicine Systems Pharmacology — herbs, compounds, targets",
        "url": "https://old.tcmsp-e.com/",
        "size": "~50 MB",
    },
    "tcmid": {
        "name": "TCMID",
        "description": "Traditional Chinese Medicine Integrated Database — herb-compound-disease",
        "url": "http://www.megabionet.org/tcmid/",
        "size": "~30 MB",
    },
    "herbs": {
        "name": "Herb Monographs",
        "description": "Chinese Pharmacopoeia herb monograph data — 600+ herbs",
        "url": "N/A (bundled)",
        "size": "~5 MB",
    },
    "formulas": {
        "name": "Classical Formulas",
        "description": "Classical formula database — 300+ formulas with compositions",
        "url": "N/A (bundled)",
        "size": "~3 MB",
    },
    "batman": {
        "name": "BATMAN-TCM",
        "description": "Bioinformatics Analysis Tool for Molecular mechANism of TCM",
        "url": "http://bionet.ncpsb.org.cn/batman-tcm/",
        "size": "~100 MB",
    },
    "symmap": {
        "name": "SymMap",
        "description": "Symptom mapping database — TCM symptoms to herbs and modern diseases",
        "url": "https://www.symmap.org/",
        "size": "~20 MB",
    },
}


def download_dataset(dataset: str, output: Path = None):
    """Download a dataset."""
    ds = DATASETS.get(dataset.lower())
    if not ds:
        console.print(f"[red]Unknown dataset: {dataset}[/red]")
        console.print(f"Available: {', '.join(DATASETS.keys())}")
        return

    output = output or Path(CONFIG_DIR / "data" / dataset)
    output.mkdir(parents=True, exist_ok=True)

    console.print(f"  [cyan]{ds['name']}[/cyan]: {ds['description']}")
    console.print(f"  Source: {ds['url']}")
    console.print(f"  Size: {ds['size']}")
    console.print(f"  Output: {output}")
    console.print()

    # For now, provide instructions for manual download
    console.print(
        f"  [yellow]Automated download not yet implemented.[/yellow]\n"
        f"  Please download manually from: {ds['url']}\n"
        f"  Then place files in: {output}\n"
        f"  After downloading, run: tcm config set data.{dataset} {output}"
    )


def dataset_status() -> Table:
    """Show status of local datasets."""
    config = Config.load()
    table = Table(title="Local Datasets")
    table.add_column("Dataset", style="cyan")
    table.add_column("Status")
    table.add_column("Path")

    for key, ds in DATASETS.items():
        data_path = config.get(f"data.{key}")
        if data_path and Path(data_path).exists():
            status = "[green]✓ available[/green]"
            path_str = data_path
        else:
            status = "[dim]○ not downloaded[/dim]"
            path_str = "-"
        table.add_row(ds["name"], status, path_str)

    return table
