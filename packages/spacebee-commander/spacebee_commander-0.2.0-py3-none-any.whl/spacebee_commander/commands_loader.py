import importlib.metadata

from .telecommand_interface import TelecommandInterface


def load_commands() -> dict[str, TelecommandInterface]:
    commands = {}

    # Discover entry points registered under this group
    command_sets = importlib.metadata.entry_points(group="spacebee_commander.command")

    for command_set in command_sets:
        loader = command_set.load()
        for command in loader():
            if not isinstance(command, TelecommandInterface):
                raise TypeError(f'Invalid command: {command}')
            commands[command.name] = command

    return commands
