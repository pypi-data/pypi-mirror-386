# microservice_starter/cli.py
import typer
from .generator import create_microservice

app = typer.Typer(help="Microservice setup generator with Docker & Celery support.")

@app.command("create")
def create(name: str):
    """Create a new microservice project."""
    try:
        create_microservice(name)
        typer.secho(f"✅ Project '{name}' created successfully!", fg=typer.colors.GREEN)
    except FileExistsError as e:
        typer.secho(str(e), fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)

def main():
    app()

if __name__ == "__main__":
    main()
