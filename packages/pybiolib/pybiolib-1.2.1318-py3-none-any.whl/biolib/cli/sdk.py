import click

from biolib._internal.add_copilot_prompts import add_copilot_prompts


@click.group(name='sdk', help='Advanced commands for developers')
def sdk():
    pass


@sdk.command(
    name='add-copilot-prompts', help='Add BioLib-specific GitHub Copilot prompts and instructions to your repository'
)
@click.option('--force', is_flag=True, help='Force overwrite existing files.')
def add_copilot_prompts_command(force: bool) -> None:
    add_copilot_prompts(force)
