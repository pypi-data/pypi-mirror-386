import subprocess
import typer

class Executor:
    def execute(self, command: str):
        if command.startswith("# Error"):
            typer.echo(command)
            return

        try:
            typer.echo(f" Executing: {command}\n")
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            typer.echo(f" Command failed: {e}")
        except Exception as e:
            typer.echo(f" Unexpected error: {e}")
