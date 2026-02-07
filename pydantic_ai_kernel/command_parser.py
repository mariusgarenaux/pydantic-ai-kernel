from typing import Callable
from dataclasses import dataclass


class CommandArgs:
    def __init__(self):
        pass


class CommandParser:
    def __init__(
        self, positionals: list[str] | None = None, flags: list[str] | None = None
    ):
        self.positionals = positionals if positionals is not None else []
        self.flags = flags if flags is not None else []

    def parse(self, components):
        # Create an argument object
        arg_obj = CommandArgs()
        for each_positional in self.positionals:
            arg_obj.__setattr__(each_positional, False)
        for each_flag in self.flags:
            arg_obj.__setattr__(each_flag, False)

        positional_idx = 0
        # Handle parameters and flags
        for component in components:
            if component.startswith("--"):
                # Handle flags
                if "=" in component:
                    key, value = component[2:].split("=", 1)
                    if key in self.flags:
                        arg_obj.__setattr__(key, value)
                    else:
                        raise ValueError(f"Unknown flag '{key}'")
                else:
                    key = component[2:]
                    if key in self.flags:
                        arg_obj.__setattr__(key, True)
                    else:
                        raise ValueError(f"Unknown flag '{key}'")
            else:
                arg_obj.__setattr__(
                    self.positionals[positional_idx], component
                )  # Store the value or process as needed
                positional_idx += 1

        return arg_obj


@dataclass
class Command:
    handler: Callable
    parser: CommandParser = CommandParser()
