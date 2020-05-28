import argparse


class _HelpAction(argparse._HelpAction):
    """Redefined class to print full help on the different commands.

    """

    def __call__(self, parser, _, __, ___):
        parser.print_help()
        print()

        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print(f'Command "{choice}"')
                print(subparser.format_help())

        parser.exit()


class _SortingDict(dict):
    def __init__(self, mapping=(), **kwargs):
        super(_SortingDict, self).__init__(mapping, **kwargs)

    def __lt__(self, other):
        return self["$ref"] < other["$ref"]
