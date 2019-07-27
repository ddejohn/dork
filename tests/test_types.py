# -*- coding: utf-8 -*-
"""Basic tests for state and entity relationships in dork"""


import dork.types as types
import dork.game_utils.factory_data as factory_data
# pylint: disable=protected-access


def test_confirm_method_blank(capsys, mocker):
    """confirm should do things"""

    mocked_input = mocker.patch('builtins.input')
    mocked_input.side_effect = ["bumblebee", "y", "tester"]
    types.Game._confirm()
    captured = capsys.readouterr()
    assert "\n!!!WARNING!!! You will lose unsaved data!\n" in captured.out
    assert "That is not a valid response!" in captured.out
    assert mocked_input.call_count == 2


def test_start_over_no(capsys, mocker, game):
    """confirm should do things"""

    mocked_input = mocker.patch('builtins.input')
    mocked_input.side_effect = ["bumblebee", "n"]
    assert game._start_over() == ("guess you changed your mind!", False)
    captured = capsys.readouterr()
    assert "\n!!!WARNING!!! You will lose unsaved data!\n" in captured.out
    assert mocked_input.call_count == 2


def test_start_over_yes(capsys, mocker, game):
    """confirm should do things"""

    # the call count here as 2 is a magic number need to document that
    mocked_input = mocker.patch('builtins.input')
    mocked_input.side_effect = ["y", "tester"]
    game._start_over()
    captured = capsys.readouterr()
    assert "\n!!!WARNING!!! You will lose unsaved data!\n" in captured.out
    assert mocked_input.call_count == 1


def test_move_method(game, cardinals):
    """testing the move function for any map"""

    for direction in cardinals:
        assert game._move(direction) in [
            (game.hero.location.description, False),
            (f"You cannot go {direction} from here.", False)
        ]


def test_mazefactory():
    """builds all game types"""

    assert isinstance(factory_data.rules(0, 0), list)
    assert isinstance(factory_data.stats("magic"), dict)
    assert isinstance(types.MazeFactory.build(), dict)
