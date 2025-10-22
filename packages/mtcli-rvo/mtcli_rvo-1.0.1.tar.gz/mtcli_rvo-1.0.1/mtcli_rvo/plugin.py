from mtcli_rvo.commands.rvo import rvo

def register(cli):
    """Registra o comando 'rvo' no mtcli."""
    cli.add_command(rvo, name="rvo")
