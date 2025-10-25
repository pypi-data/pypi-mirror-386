
import click
from pathlib import Path

from . import config
from .scanner import scan_directory
from .exporters.markdown import to_markdown
from .exporters.json_exporter import to_json


@click.group()
def main():
    """A CLI tool to generate a project map."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--ext", default=".py,.json,.md", help="Comma-separated list of file extensions to include.")
@click.option("--out", default="project_tree.md", help="Output file name.")
@click.option("--format", type=click.Choice(["md", "json"]), default="md", help="Output format.")
@click.option("--max-file-size", default="1MB", help="Maximum file size to include (e.g., 1MB, 2K).")
def map(path: Path, ext: str, out: str, format: str, max_file_size: str):
    """Generate a project map from a directory."""
    try:
        size_in_bytes = config.parse_size(max_file_size)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    cfg = config.Config(
        ext=ext.split(","),
        out=Path(out),
        format=format,
        max_file_size=size_in_bytes,
    )

    documents = list(scan_directory(path, cfg))

    if cfg.format == "md":
        output = to_markdown(documents, path)
    elif cfg.format == "json":
        output = to_json(documents, path)
    else:
        click.echo(f"Error: Unknown format {cfg.format}", err=True)
        return

    cfg.out.write_text(output, encoding="utf-8")
    click.echo(f"Project map saved to {cfg.out}")
