#!/usr/bin/env python
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.style import Style

from plot_tree.common import PACKAGE_VERSION
from plot_tree.default import CSV_FILE_NAME, OUTPUT_DIR_NAME
from plot_tree.example_csv import create_example_csv
from plot_tree.tree_plotter import TreePlotter

app = typer.Typer(
    context_settings=dict(help_option_names=['-h', '--help']),
    add_completion=False
)


def version_callback(value: bool):
    if value:
        typer.echo(f'Version: {PACKAGE_VERSION}')
        raise typer.Exit()


def example_callback(value: bool):
    if value:
        create_example_csv()
        raise typer.Exit()


@app.command()
def csv(
        csv_file: str = typer.Argument(default=CSV_FILE_NAME, help='csv file name'),
        output_dir: str = typer.Option(OUTPUT_DIR_NAME, '--output-dir', '-o', help='output directory'),
        example: Annotated[
            Optional[bool],
            typer.Option('--example', '-e',
                         callback=example_callback,
                         is_eager=True,
                         help='create an example csv file at current directory'),
        ] = None,
        version: Annotated[
            Optional[bool],
            typer.Option('--version', '-v', callback=version_callback, is_eager=True, help=PACKAGE_VERSION),
        ] = None,
        ctx: typer.Context = typer.Option(None, hidden=True)

):
    '''Plot tree from a csv file with child-parent relationships.
    '''
    console = Console()

    csv_file_path = Path(csv_file)
    if not os.path.exists(csv_file):
        console.print(f'csv file not found: {csv_file_path.resolve()}')
        typer.echo(ctx.get_help())
        raise typer.Exit(code=1)

    output_dir_path = Path(output_dir)
    plotter = TreePlotter(csv_file=csv_file_path, output_dir=output_dir_path)
    plotter.plot()

    console.print(f'''
Read from csv file: `{csv_file_path.resolve()}`
Wrote to folder: `{output_dir_path.resolve()}`
''', style=Style(color='green')
                  )
    cat_art = f"""
Done. Enjoy your day! 

 /\_/\  
( ^‿^ )
 > ^ <  :smiling_face_with_sunglasses: :canada: v{PACKAGE_VERSION}   
"""
    console.print(cat_art, style=Style(color='magenta'))


if __name__ == '__main__':
    app()
