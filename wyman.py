#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "httpx",
#     "plumbum",
#     "rich",
#     "typer",
# ]
# ///
"""wyman: Small utility to check tldr, cheat.sh, manpages, and help in that
order.
"""

import os
from enum import StrEnum
from typing import Annotated

import httpx
import plumbum
import typer
from rich.console import Console
from rich.text import Text


class Source(StrEnum):
    TLDR = "tldr"
    CHEAT = "cheat"
    MAN = "man"


app = typer.Typer(add_completion=False)
console = Console()


def _tldr(cmd_name: str, args: tuple[str, ...] = ()) -> bool:
    if plumbum.local.which("tldr") is None:
        console.print("tldr is not installed, skipping")
        return False
    retcode, _, _ = plumbum.local["tldr"][cmd_name][args].run(retcode=None)
    if retcode == 0:
        os.execvp("tldr", ["tldr", *args, cmd_name])
        return True
    console.print(f"no `tldr` page found for {cmd_name}...")
    return False


def _cheat(cmd_name: str) -> bool:
    try:
        resp = httpx.get(
            f"https://cht.sh/{cmd_name}",
            headers={"User-Agent": "curl/8"},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        console.print(f"cheat.sh request failed: {exc}")
        return False
    if not resp.is_success:
        console.print(f"`cheat.sh` returned a {resp.status_code}")
        return False
    first_line = resp.text.splitlines()[0] if resp.text else ""
    if first_line == "Unknown topic.":
        console.print(f"no `cheat.sh` page found for {cmd_name}...")
        return False
    console.print(Text.from_ansi(resp.text))
    return True


def _man(cmd_name: str) -> None:
    retcode = plumbum.local["man"]["-w", cmd_name].run(retcode=None)[0]
    if retcode == 0:
        os.execvp("man", ["man", cmd_name])  # never returns
    console.print(f"no `man-page` found for {cmd_name}...")


CHECKERS: dict[Source, object] = {
    Source.TLDR: lambda c: _tldr(c, ("--platform", "linux")),
    Source.CHEAT: _cheat,
    Source.MAN: lambda c: (_man(c), False)[1],  # _man execvp or falls through
}


@app.command()
def main(
    command: Annotated[str, typer.Argument(help="Command to search for")],
    prefer: Annotated[
        Source | None,
        typer.Option(
            "--prefer",
            "-p",
            help="Try this source first, then the rest in default order.",
        ),
    ] = None,
) -> None:
    """Check tldr, cheat.sh, and man for COMMAND, in that order."""
    order = list(Source)
    if prefer is not None:
        order.remove(prefer)
        order.insert(0, prefer)

    for source in order:
        label = {
            Source.TLDR: f"checking `tldr {command}`",
            Source.CHEAT: f"fetching cheat.sh/{command}",
            Source.MAN: f"checking `man {command}`",
        }[source]
        with console.status(f"{label}...", spinner="dots"):
            if CHECKERS[source](command):
                raise typer.Exit
        if source is Source.MAN:
            break
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
