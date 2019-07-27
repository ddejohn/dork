"""This is the REPL which parses commands and passes them to a Game object."""


from dork.game_utils import game_data
from dork import types as dork_types
# pylint: disable=protected-access


_CMDS = game_data.CMDS
_MOVES = game_data.MOVES
_META = game_data.META
_ERRS = game_data.ERRS


def _new_game(player_name=None):
    if not player_name:
        player_name = input("What's your name, stranger? ")

    dork = dork_types.Gamebuilder.build(player_name)
    print(f"\nGreetings, {dork.hero.name}! " + game_data.TITLE + "\n")

    return dork


def _read():
    """Get input from CLI"""

    return str.casefold(input("> "))


def _evaluate(cmd, dork):
    """Parse a command and execute it"""

    cmd = cmd.strip().split(" ", 1)
    if cmd[0]:
        verb, *noun = cmd
        noun = noun[0] if noun else None
        call = _CMDS.get(verb, _MOVES.get(verb, _META.get(verb, _ERRS["u"])))

        if isinstance(call, dict):
            method, arg = call.get(noun, _ERRS["which way"])
        elif call not in _ERRS.values():
            if verb == noun:
                method, arg = _ERRS["twice"]
            elif len(call) > 1:
                if noun:
                    method, arg = _ERRS["which way"]
                else:
                    method, arg = call
            elif noun and len(call) == 1:
                method, arg = call[0], noun
            else:
                method, arg = call[0], None
        else:
            method, arg = call

    else:
        method, arg = _ERRS["?"]

    return dork(method, arg)


def repl():
    """read evaluate print loop"""

    dork = _new_game()
    should_exit = False

    while not should_exit:
        output, should_exit = _evaluate(cmd=_read(), dork=dork)
        if output == "new game":
            dork = _new_game()
        else:
            print(output + "\n")
