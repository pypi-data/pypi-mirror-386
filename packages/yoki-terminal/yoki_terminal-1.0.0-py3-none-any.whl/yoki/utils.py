import typer

def confirm_run() -> bool:
    return typer.confirm("⚡ Do you want to run this command?")

def print_header():
    typer.echo("translating...")
    
