"""Central package for heavy edge analysis."""

__all__ = [
    "get_sample_path",
    "RawProfileCsvs",
    "ProfileData",
]

import logging

from .io import (
    ProfileData,
    RawProfileCsvs,
)
from .samples import get_sample_path

logger = logging.getLogger(__name__)


def main():
    import argparse
    import sys
    from importlib.metadata import entry_points

    from heavyedge.cli.command import DEPRECATED_COMMANDS, REGISTERED_COMMANDS

    from .cli.parser import ConfigArgumentParser

    def filter_commands(commands):
        filtered_commands = []
        for group, command_dict in commands:
            not_deprecated = {
                name: (cls, desc)
                for name, (cls, desc) in command_dict.items()
                if cls not in DEPRECATED_COMMANDS
            }
            filtered_commands.append((group, not_deprecated))
        return filtered_commands

    def format_epilog(commands):
        command_lengths = []
        for _, command_dict in commands:
            for name in command_dict.keys():
                command_lengths.append(len(name))

        INDENT1 = 2 * " "
        INDENT2 = 4 * " "
        SPACING = max(max(command_lengths) + 5, 20)
        ret = "LIST OF COMMANDS\n"
        for group, command_dict in commands:
            ret += f"{INDENT1}{group}:\n"
            if not command_dict:
                ret += f"{INDENT2}(no commands available)\n"
            else:
                for name, (_, desc) in command_dict.items():
                    ret += f"{INDENT2}{name}{(SPACING - len(name)) * ' '}{desc}\n"
            ret += "\n"
        return ret

    ORDERS = []
    COMMANDS = []
    for ep in entry_points(group="heavyedge.commands"):
        module = ep.load()
        order = getattr(module, "PLUGIN_ORDER", None)
        commands = dict()
        for key in list(REGISTERED_COMMANDS.keys()):
            commands[key] = REGISTERED_COMMANDS.pop(key)
        ORDERS.append(order)
        COMMANDS.append((ep.name, commands))

    max_order = max([x for x in ORDERS if x is not None])
    ORDERS = [x if x is not None else max_order for x in ORDERS]
    COMMANDS = [x for _, x in sorted(zip(ORDERS, COMMANDS))]

    heavyedge_parser = argparse.ArgumentParser(
        prog="heavyedge",
        description="Heavy edge profile analysis.",
        epilog=format_epilog(filter_commands(COMMANDS)),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    heavyedge_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Set logging level",
    )
    heavyedge_parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List all installed plugins",
    )
    subparser = heavyedge_parser.add_subparsers(
        title="Command",
        dest="command",
        metavar="<command>",
        help="Refer to the epilog for a list of commands",
        parser_class=ConfigArgumentParser,
    )

    COMMAND_OBJS = dict()
    for _, command_dict in COMMANDS:
        for name, (cls, _) in command_dict.items():
            COMMAND_OBJS[name] = cls(name, logger)

    for command in COMMAND_OBJS.values():
        command.add_parser(subparser)

    args = heavyedge_parser.parse_args()

    logging.basicConfig(
        format="heavyedge: [%(asctime)s] [%(levelname)8s] --- %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=args.log_level.upper(),
    )
    logger.debug(f"Input command: {' '.join(sys.argv)}")

    if args.list_plugins:

        INDENT = 2 * " "
        msg = "COMMAND PLUGINS\n"
        for _, ep in sorted(zip(ORDERS, entry_points(group="heavyedge.commands"))):
            msg += f"{INDENT}{ep.name} ({ep.value})\n"
        msg += "\n"
        msg += "RAW DATA PLUGINS\n"
        for ep in entry_points(group="heavyedge.rawdata"):
            msg += f"{INDENT}{ep.name} ({ep.value})\n"

        print(msg)

    elif args.command is None:
        heavyedge_parser.print_help(sys.stderr)
        sys.exit(1)

    else:
        command = COMMAND_OBJS[args.command]
        try:
            command.run(args)
        except Exception:
            input_command = " ".join(sys.argv)
            logger.exception(f"Got exception while running '{input_command}'.")
            sys.exit(1)
