"""
EvenAge CLI - Production-grade modular CLI.

Provides project initialization, agent management, and Docker orchestration.
"""

from __future__ import annotations

import sys
import traceback

import click

from .commands import add, init, logs, ps, run, run_dev_alias, scale, stop
from .utils import EvenAgeError, console, print_error

try:
    from evenage import __version__ as pkg_version
except ImportError:
    pkg_version = "0.2.3"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=pkg_version, prog_name="EvenAge")
def cli():
    """EvenAge - Transparent, Docker-native agent framework."""
    pass


cli.add_command(init)
cli.add_command(add)
cli.add_command(run)
cli.add_command(logs)
cli.add_command(ps)
cli.add_command(scale)
cli.add_command(stop)
cli.add_command(run_dev_alias)


def main():
    """Main entry point with error handling."""
    try:
        cli()
    except EvenAgeError as e:
        print_error(e.message, hint=e.hint)
        sys.exit(1)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red bold]Unexpected error:[/red bold] {e}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
