"""Command line interface for :mod:`fairsharing_client`."""

import click

__all__ = [
    "main",
]


@click.command()
@click.option("--force", is_flag=True)
def main(force: bool) -> None:
    """Download the FAIRsharing data."""
    from .api import ensure_fairsharing

    ensure_fairsharing(force_download=force)


if __name__ == "__main__":
    main()
