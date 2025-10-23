import json
from pprint import pprint

import typer

from .processors import ManifestProcessor

manifests = typer.Typer()


@manifests.command()
def display(filename: str) -> None:
    """Parse and print the contents of a manifest JSON file."""
    with open(filename) as f:
        meta = json.load(f)

    pprint(meta)


@manifests.command()
def create(filename: str, project_context: str) -> None:
    """Create a manifest file from the given project context."""
    ManifestProcessor(filename, project_context).create()
