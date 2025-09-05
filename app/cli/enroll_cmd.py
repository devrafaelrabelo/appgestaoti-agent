# app/cli/enroll_cmd.py
import typer
import logging

from app.workflows.enroll_flow import run as run_enroll

app = typer.Typer(help="Utilitários CLI do agente AppGestaoTI")


@app.command("enroll")
def enroll() -> None:
    """
    Executa o fluxo de inscrição (enroll).
    Retorna código 0 em sucesso, 1 em falha.
    """
    logging.basicConfig(level=logging.INFO)

    ok, msg = run_enroll()
    if ok:
        typer.secho(f"✔ Enroll OK: {msg}", fg=typer.colors.GREEN, bold=True)
        raise typer.Exit(code=0)
    else:
        typer.secho(f"✘ Enroll falhou: {msg}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
