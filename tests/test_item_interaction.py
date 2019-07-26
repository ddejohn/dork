"""Test the various usable items"""


from random import choice
from dork import repl
# pylint: disable=protected-access


def test_take_all_drop_all(game):
    """
        1. take all items
        2. confirm they are now in player inventory
        3. confirm room inventory is empty
        4. drop all items
        5. confirm player inventory empty
        6. confirm all items now in room inventory
    """

    hero = game.hero
    room_0 = game.rooms["room 0"]
    room_inventory = room_0.get_items("", False)

    repl._evaluate("take", game)
    assert hero.get_items("", False) == room_inventory
    assert room_0.get_items("", False) == "There's nothing here."

    repl._evaluate("drop", game)
    assert hero.get_items("", False) == "There's nothing here."
    assert room_0.get_items("", False) == room_inventory


def test_drop_item_from_inv(game):
    """
        1. take a random item from the room
        2. confirm it is in player inventory
        3. confirm it is not in room inventory
        4. drop item
        5. confirm no longer in player inventory
        6. confirm item in room inventory
    """

    hero = game.hero
    room_0 = game.rooms["room 0"]
    random_item = choice(list(room_0.inventory.keys()))

    repl._evaluate(f"take {random_item}", game)
    assert random_item in hero.inventory
    assert random_item not in room_0.inventory

    repl._evaluate(f"drop {random_item}", game)
    assert random_item not in hero.inventory
    assert random_item in room_0.inventory


def test_drop_item_not_in_inv(game):
    """try to drop an item that is not in your inventory"""

    no_drop = repl._evaluate("drop larsen", game)
    assert no_drop == ("There is no larsen in your inventory.", False)


def test_take_item_not_in_room(game):
    """try to take an item that is not in the room"""

    no_take = repl._evaluate(f"take larsen", game)
    assert no_take == ("There is no larsen here.", False)
