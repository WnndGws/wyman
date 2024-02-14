#!/usr/bin/env python
"""Checks for the input program in order of tldr, man, and --help.

Has autocompletion
"""

import re
import subprocess

import click


def get_programs(ctx, args: str, incomplete):
    """Get the list of possible binaries on the system"""
    # Call subprocess with shell envs, decode the bytes to a str, remove trailing \n, split by : character
    paths = (
        subprocess.run(
            ["echo $PATH"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        .stdout.decode("utf-8")
        .partition("\n")[0]
        .split(":")
    )

    programs = []

    # Loop over paths to find executables and return only names
    for i in paths:
        programs.extend(
            subprocess.run(
                [f'find {i} -maxdepth 3 -executable -printf "%f\n"'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                shell=True,
            )
            .stdout.decode("utf-8")
            .split("\n")
        )

    # Convert to a set to remove duplicates, then back to a list
    programs = list(set(programs))
    programs.sort()

    return [k for k in programs if incomplete in k]


@click.command()
@click.argument("program", type=click.STRING, shell_complete=get_programs)
def main(program):
    """Checks to see if there is a tldr."""
    success = False
    tldr_list = subprocess.check_output(["tldr", "--list"]).strip()
    match = re.findall(r"(%s)" % program, str(tldr_list))
    if len(match) > 0:
        try:
            args = ["tldr", program]
            success = True
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            success = False
    else:
        click.echo(f"No tldr entry for {program}")
    if not success:
        try:
            args = [
                "curl",
                "--silent",
                "--max-time",
                "1",
                f"https://cheat.sh/{program}",
            ]
            output = subprocess.check_output(args).decode("utf-8")
            if not output[:7] == "Unknown":
                success = True
                click.echo(output)
            else:
                success = False
                click.echo(f"No cheat.sh entry for {program}")
        except subprocess.CalledProcessError:
            success = False
            click.echo("cheat.sh timed out")
    if not success:
        try:
            args = ["man", program]
            success = True
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            success = False
    if not success:
        try:
            args = [program, "--help"]
            success = True
            subprocess.check_call(args)
        except OSError:
            success = False
            click.echo(f"No --help flag for {program}")
            click.echo(
                f"There either is no program called {program}, or it does not have a man-page"
            )


if __name__ == "__main__":
    main()
