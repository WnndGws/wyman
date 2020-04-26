#!/bin/python

import click
import re
import subprocess

def get_programs(ctx, args, incomplete):
    # Call subprocess with shell envs, decode the bytes to a str, split by : character
    paths = subprocess.run(["echo $PATH"], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8').split(":")

    programs = []

    # Loop over paths to find executables and return only names
    for i in paths:
        programs.extend(subprocess.run([f'find {i} -maxdepth 3 -executable -printf "%f\n"'], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8').split("\n"))

    # Convert to a set to remove duplicates, then back to a list
    programs = list(set(programs))

    return [k for k in programs if incomplete in k]

@click.command()
@click.argument("program", type=click.STRING, autocompletion=get_programs)
def main(program):
    """Checks to see if there is a tldr"""
    success = False
    tldr_list = subprocess.check_output(["tldr", "--list"]).strip()
    match = re.findall(r"(%s)" % program, str(tldr_list))
    if len(match) > 0:
        try:
            args = ["tldr", program]
            subprocess.check_call(args)
            success = True
        except subprocess.CalledProcessError:
            success = False
    if not success:
        try:
            args = ["man", program]
            subprocess.check_call(args)
            success = True
        except subprocess.CalledProcessError:
            success = False
    if not success:
        try:
            args = [program, "--help"]
            subprocess.call(args)
            success = True
        except OSError:
            success = False
            click.echo(f"There either is no program called {program}, or it does not have a man-page")

if __name__ == "__main__":
    main()
