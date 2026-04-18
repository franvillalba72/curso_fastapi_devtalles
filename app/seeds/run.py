import typer

from app.seeds.service import run_all, run_categories, run_tags, run_users


app = typer.Typer(help="Seeds: users, categories and tags.")


@app.command("all")
def all_():  # Hay que usar otro nombre porque "all" es una palabra reservada en Python
    run_all()
    typer.echo("All seeds executed successfully.")


@app.command("users")
def users():
    run_users()
    typer.echo("Users seeded successfully.")


@app.command("categories")
def categories():
    run_categories()
    typer.echo("Categories seeded successfully.")


@app.command("tags")
def tags():
    run_tags()
    typer.echo("Tags seeded successfully.")
