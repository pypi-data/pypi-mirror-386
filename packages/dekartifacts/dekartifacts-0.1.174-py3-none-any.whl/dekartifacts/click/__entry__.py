from dektools.typer import command_version
from . import app
from .docker import app as docker_app
from .registry import app as registry_app

command_version(app, __name__)
app.add_typer(docker_app, name='docker')
app.add_typer(registry_app, name='registry')


def main():
    app()
