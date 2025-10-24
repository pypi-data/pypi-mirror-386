import typer
from .translator import Translator
from .executor import Executor
from .utils import confirm_run, print_header
from .config import set_api_key, load_api_key

app = typer.Typer(help="Yoki: AI-powered natural language → terminal command converter")

@app.command()
def setkey(api_key: str):
    """Save your API key for Gemini."""
    set_api_key(api_key)
    typer.echo("✅ API key saved successfully!")

@app.command()
def run(query: str, yes: bool = typer.Option(False, "--yes", help="Run without confirmation")):
    """Convert a natural language query to a terminal command and optionally execute it."""
    print_header()
    translator = Translator()
    executor = Executor()

    # Pass OS info to Gemini for proper command generation
    import platform
    os_name = platform.system()
    full_query = f"[OS: {os_name}] {query}"

    command = translator.translate(full_query)
    typer.echo(f"\nSuggested command:\n\n{command}\n")

    if yes or confirm_run():
        executor.execute(command)
    else:
        typer.echo("Command not executed.")
