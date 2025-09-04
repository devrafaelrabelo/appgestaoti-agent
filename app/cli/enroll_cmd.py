import typer
from app.workflows.enroll_flow import run as run_enroll

def enroll():
    ok, msg = run_enroll()
    if ok:
        typer.secho(msg, fg=typer.colors.GREEN)
    else:
        typer.secho(msg, fg=typer.colors.RED)
        raise typer.Exit(code=1)