import click



class BuxCLI(click.Group):
    def format_help(self, ctx, formatter):
        click.echo(click.style(r"""                                                                                         
██████  ██    ██ ██   ██  ██████ ██      ██ 
██   ██ ██    ██  ██ ██  ██      ██      ██ 
██████  ██    ██   ███   ██      ██      ██ 
██   ██ ██    ██  ██ ██  ██      ██      ██ 
██████   ██████  ██   ██  ██████ ███████ ██ 
                                            
""", fg="magenta", bold=True))
        click.echo(click.style("Run commands with automatic email notifications when they succeed, fail, or a server starts.\n", fg="yellow"))
        click.echo(click.style("Examples:", fg="green", bold=True))
        click.echo(click.style("  buxcli run \"python manage.py runserver\"", fg="cyan"))
        click.echo(click.style("  buxcli docker pull ollama\n", fg="cyan"))
        super().format_help(ctx, formatter)
