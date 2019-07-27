# -*- coding: utf-8 -*-
"""Base types for the Dork game"""


import os
from copy import deepcopy
from random import choices, choice, randint, shuffle, randrange
from operator import add
from inspect import getfullargspec as argspec
import yaml
import matplotlib.pyplot as plt
from numpy import full as npf
import dork.game_utils.factory_data as factory_data
# pylint: disable=protected-access


class Grandparent:
    """common parent of holder, adjacent, and coord"""


class Holder(Grandparent):
    """A holder/container of items"""

    def __init__(self):
        super().__init__()
        self.inventory = {}

    def get_items(self, caller, verbose):
        """Print all inventory items"""

        if self.inventory:
            out = f"\n{caller} inventory:"
        else:
            out = f"There's nothing here."

        for name, item in self.inventory.items():
            out += "\n    " + name
            if verbose:
                out += Game._verbose_print(vars(item))
        return out


class Stats:
    """stats for items"""

    def __init__(self):
        self.attack = int
        self.strength = int
        self.weight = int
        self.luck = int
        self.equipable = bool


class Adjacent(Grandparent):
    """adjacency object for rooms"""

    def __init__(self):
        super().__init__()
        self.north = str
        self.south = str
        self.east = str
        self.west = str


class Coord(Grandparent):
    """coordinate object for rooms"""

    def __init__(self):
        super().__init__()
        self.x = int
        self.y = int


class Item(Stats):
    """An obtainable/usable item"""

    def __init__(self):
        super().__init__()
        self.description = str
        self.type = str


class Player(Holder):
    """A player or npc in the game"""

    instances = []

    def __init__(self):
        super().__init__()
        self.name = str
        self.description = str
        self.location = Room
        self.equipped = list
        self.instances.append(self)

    def move(self, cardinal, maze):
        """walk this way"""

        adjacent_room = getattr(self.location, cardinal)

        if not adjacent_room:
            out = f"You cannot go {cardinal} from here."
        else:
            adjacent_room.players[self.name] = \
                self.location.players.pop(self.name)

            maze[self.location.x][self.location.y] = MazeFactory.room_color
            self.location = adjacent_room
            maze[self.location.x][self.location.y] = MazeFactory.player_color

            MazeFactory.update(maze)
            out = self.location.description
        return out


class Room(Adjacent, Coord, Holder):
    """A room on the worldmap"""
    # pylint: disable=too-many-instance-attributes

    instances = []

    def __init__(self):
        super().__init__()
        self.description = str
        self.players = {}
        self.instances.append(self)

    def _take(self, hero, item_name):
        out = ""
        if not item_name:
            room_copy = deepcopy(self.inventory)
            for item in room_copy:
                hero.inventory[item] = self.inventory.pop(item)
                out += f"You took {item}\n"
        elif item_name in self.inventory:
            hero.inventory[item_name] = self.inventory.pop(item_name)
            out += f"You took {item_name}. You took it well."
        else:
            out = f"There is no {item_name} here."
        return out, False

    def _drop(self, hero, item_name):
        out = ""
        if not item_name:
            player_copy = deepcopy(hero.inventory)
            for item in player_copy:
                self.inventory[item] = hero.inventory.pop(item)
                out += f"You dropped {item}\n"
        elif item_name in hero.inventory:
            self.inventory[item_name] = hero.inventory.pop(item_name)
            out += f"You dropped {item_name}. How clumsy."
        else:
            out = f"There is no {item_name} in your inventory."
        return out, False


class Gamebuilder:
    """Build an instance of Game"""

    attrs = ["adjacent", "coordinates", "stats"]
    cardinals = ["north", "south", "east", "west"]

    dict_factories = {
        "players": Player,
        "inventory": Item,
    }

    @staticmethod
    def build(player_name):
        """Instantiate a game of Dork from dictionary"""

        data = Gamebuilder.load_game(player_name)

        if not data:
            data = MazeFactory.build()

            hero_data = {
                "name": player_name,
                "description": "the hero of dork!",
                "location": "Entrance",
                "inventory": {},
                "equipped": []
            }

            data["rooms"]["room 0"]["players"][player_name] = hero_data

        game = Game()
        setattr(game, "maze", data["maze"])
        setattr(game, "rooms", Gamebuilder._make_rooms(data["rooms"]))

        Gamebuilder._place_players(game)
        Gamebuilder._make_paths(game)

        for player in Player.instances:
            if player.name == player_name:
                hero = player

        game.hero = hero
        game.maze[hero.location.x][hero.location.y] = MazeFactory.player_color
        return game

    @staticmethod
    def _place_players(game):
        for _, room in game.rooms.items():
            for _, player in room.players.items():
                player.location = room

    @staticmethod
    def _make_paths(game):
        for _, room in game.rooms.items():
            for direction in Gamebuilder.cardinals:
                this_adj = getattr(room, direction)
                setattr(room, direction, game.rooms.get(this_adj, None))

    @staticmethod
    def _make_rooms(rooms):
        for name, room in rooms.items():
            new_room = Gamebuilder._rec_inst(Room, **room)
            rooms[name] = new_room
        return rooms

    @staticmethod
    def _rec_inst(clz, **data):
        new_obj = clz()
        for key, val in data.items():
            if key in Gamebuilder.dict_factories:
                for sub_key, sub_val in val.items():
                    new_sub = Gamebuilder._rec_inst(
                        Gamebuilder.dict_factories[key], **sub_val
                    )
                    getattr(new_obj, key)[sub_key] = new_sub
            elif key in Gamebuilder.attrs:
                for sub_key, sub_val in val.items():
                    setattr(new_obj, sub_key, sub_val)
            else:
                setattr(new_obj, key, val)
        return new_obj

    @staticmethod
    def load_game(player):
        """Load the save file associated with player"""

        save_files = []
        with os.scandir("./dork/saves") as saves:
            for entry in saves:
                save_files.append(entry.name.strip(".yml"))
        if player in save_files:
            file_path = f"./dork/saves/{player}.yml"
            with open(file_path) as file:
                data = yaml.safe_load(file.read())
        else:
            data = {}
        return data

    @staticmethod
    def save_game(game):
        """Save a game instance to a yaml file if it exists, else create one"""

        def _rec_data(data):
            out = {}
            for key, val in data.items():
                if isinstance(val, (Item, Player)):
                    out[key] = _rec_data(vars(val))
                elif isinstance(val, dict):
                    out[key] = _rec_data(val)
                elif isinstance(val, Room):
                    out[key] = val.name
                else:
                    out[key] = val
            return out

        data = {
            "maze": game.maze,
            "rooms": {}
        }

        for name, room in game.rooms.items():
            new_room = {}
            new_room["adjacent"] = {}
            new_room["coordinates"] = {}
            for key, val in vars(room).items():
                if isinstance(val, dict):
                    new_room[key] = _rec_data(val)
                elif key in Gamebuilder.cardinals:
                    this_adj = val.name if val else None
                    new_room["adjacent"][key] = this_adj
                elif key in ["x", "y"]:
                    new_room["coordinates"][key] = val
                else:
                    new_room[key] = val
            data["rooms"][name] = new_room

        file_name = f"./dork/saves/{game.hero.name}.yml"
        with open(file_name, "w") as save_file:
            yaml.safe_dump(
                data, save_file,
                indent=4, width=80,
            )

        return f"Your game was successfully saved as {game.hero.name}.yml!"


class Game:
    """An instance of Dork"""

    verbose = False
    dataaa = {}

    def __init__(self):
        self.maze = []
        self.rooms = {}
        self.hero = Player()

    def __call__(self, cmd, arg):
        do_func = getattr(self, cmd)
        func_args = argspec(do_func).args
        if arg:
            if not func_args or ("self" in func_args and len(func_args) == 1):
                out = self._repl_error("This command takes no arguments")
            else:
                out = do_func(arg)
        else:
            out = do_func()
        return out

    def _toggle_verbose(self) -> (str, bool):
        self.verbose = not self.verbose
        out = {
            True: "verbose inventory: ON",
            False: "verbose inventory: OFF"
        }[self.verbose]
        return out, False

    def _gtfo(self):
        return f"\nThanks for playing DORK, {self.hero.name}!", True

    def _draw_maze(self):
        MazeFactory.draw(self.maze)
        return "\b", False

    def _move(self, cardinal):
        return self.hero.move(cardinal, self.maze), False

    def _examine(self):
        return self.hero.location.get_items(
            self.hero.location.name, self.verbose
        ), False

    def _inventory(self):
        return self.hero.get_items(
            self.hero.name, self.verbose
        ), False

    def _look(self):
        return self.hero.location.description, False

    def _take_item(self, item_name=None):
        return self.hero.location._take(self.hero, item_name)

    def _drop_item(self, item_name=None):
        return self.hero.location._drop(self.hero, item_name)

    def _start_over(self):
        return self._confirm(), False

    def _save_game(self):
        return Gamebuilder.save_game(self), False

    @staticmethod
    def _verbose_print(data):
        out = ""
        spc = "    "
        for key, val in data.items():
            out += "\n" + spc*2 + f"{key}: {val}"
        return out

    @staticmethod
    def _confirm():
        print("\n!!!WARNING!!! You will lose unsaved data!\n")
        conf = False
        while True:
            conf = str.casefold(
                input("Would you like to proceed? Y/N: ")
            )
            conf = {
                "y": "new game",
                "n": "guess you changed your mind!"
            }.get(conf, None)
            if not conf:
                print("That is not a valid response!")
            else:
                break
        return conf

    @staticmethod
    def _repl_error(arg):
        return f"{arg}", False

    @staticmethod
    def _zork():
        return "holy *%&#@!!! a wild zork appeared!", False


class ItemFactory:
    """Generates a random named item with randomized stats"""

    items = factory_data.ITEMS
    names = factory_data.NAMES
    sequence = factory_data.SEQUENCE

    types = items["types"]
    condition = items["condition"]
    material = items["material"]

    posessive = names["posessive"]
    nonposessive = names["nonposessive"]
    suffixes = names["suffixes"]
    abstract = names["abstract"]
    adjectives = names["adjectives"]

    @staticmethod
    def build(weights=None):
        """generate a random item"""

        weights = {
            "player": [8, 0, 0, 7, 5, 10]
        }.get(weights, [8, 35, 3, 7, 5, 10])

        item_type = choice(choices(
            population=list(ItemFactory.types.keys()),
            weights=weights,
            k=len(list(ItemFactory.types.keys()))
        ))

        item_name = choice(choices(
            population=ItemFactory.types[item_type],
            k=len(ItemFactory.types[item_type])
        ))

        return ItemFactory._forge(item_name, item_type)

    @staticmethod
    def _generate(stats, item_name, item_type):
        return {
            "name": item_name,
            "type": item_type,
            "description": "",
            "stats": stats
        }

    @staticmethod
    def _stats(item_name, item_type):
        stats = factory_data.stats(item_type.split()[0])
        return ItemFactory._generate(stats, item_name, item_type)

    @staticmethod
    def _forge(item_name, item_type):
        new_name = []
        build = ItemFactory.sequence[item_type]

        seq = choice(choices(
            population=build["seq"],
            weights=build["w"],
            k=len(build["seq"])
        ))

        for lists in seq:
            if isinstance(lists, dict):
                this_list = lists.get(
                    item_type, lists.get("usable", ['']))
            elif lists:
                this_list = lists
            else:
                this_list = ['']

            this_word = choice(choices(
                population=this_list,
                k=len(this_list)
            ))

            if this_word:
                if this_word in ItemFactory.suffixes:
                    new_name[-1] += this_word
                    item_type = f"legendary {item_name}"
                else:
                    new_name.append(this_word)
            else:
                new_name.append(item_name)

        item_name = " ".join(new_name)
        return ItemFactory._stats(item_name, item_type)


class PlayerFactory:
    """Generate players for a room"""

    @staticmethod
    def build(i, room):
        """Make a player, give them items"""

        new_player = {
            "name": f"player {i}",
            "description": f"player {i} description",
            "location": room["name"],
            "inventory": {},
            "equipped": []
        }

        for _ in range(randint(1, 3)):
            new_item = ItemFactory.build("player")
            item_name = new_item.pop("name")
            if new_item["stats"]["equipable"]:
                new_player["equipped"].append(item_name)

            new_player["inventory"][item_name] = new_item
        return new_player


class RoomFactory:
    """Generate rooms for a given maze"""

    #  N, S and E, W are backwards because numpy uses column-order
    moves = {
        "north": (1, 0), "south": (-1, 0),
        "east": (0, 1), "west": (0, -1),
    }

    @staticmethod
    def build(maze, rooms):
        """build a room"""

        RoomFactory.maze = maze
        RoomFactory.rooms = rooms
        RoomFactory.worldmap = {}
        return RoomFactory._make_rooms()

    @staticmethod
    def _make_rooms():
        i = 0
        for room in RoomFactory.rooms:
            x, y = room
            new_room = {
                "name": f"room {i}",
                "description": f"room {i} description",
                "coordinates": {
                    "x": x,
                    "y": y,
                },
                "adjacent": {},
                "players": {},
                "inventory": {},
            }

            for _ in range(randint(1, 7)):
                new_item = ItemFactory.build()
                new_room["inventory"][new_item.pop("name")] = new_item

            for _ in range(randint(0, 2)):
                new_player = PlayerFactory.build(i, new_room)
                new_room["players"][new_player["name"]] = new_player

            RoomFactory.worldmap[room] = new_room
            i += 1

        return RoomFactory._get_adj()

    @staticmethod
    def _get_adj():
        for coord, room in RoomFactory.worldmap.items():
            for direction in RoomFactory.moves:
                searching = True
                position = coord
                while searching:
                    position = tuple(
                        map(
                            add, position, RoomFactory.moves[direction]
                        )
                    )
                    if RoomFactory.maze[position] == MazeFactory.wall_color:
                        room["adjacent"][direction] = None
                        searching = False
                    elif RoomFactory.maze[position] in \
                            [MazeFactory.room_color, MazeFactory.player_color]:
                        room["adjacent"][direction] = \
                            RoomFactory.worldmap[position]["name"]
                        searching = False

        for coord, room in deepcopy(RoomFactory.worldmap).items():
            new_room = RoomFactory.worldmap.pop(coord)
            RoomFactory.worldmap[new_room["name"]] = new_room

        return RoomFactory.worldmap

    @classmethod
    def _get_room_inv_description(cls, worldmap):
        for rooms in worldmap:
            inv_list = worldmap[rooms]["inventory"]
            num = len(inv_list)
            if num > 2:
                rand_ind = randrange(4)
                first_desc = worldmap[rooms]["description"] + "\n"
                desc = factory_data.ROOM_INV_DESCRIPTIONS["1"][rand_ind]
                worldmap[rooms]["description"] = first_desc+desc
            elif num == 1:
                first_desc = worldmap[rooms]["description"] + "\n"
                desc = factory_data.ROOM_INV_DESCRIPTIONS["2"]
                worldmap[rooms]["description"] = first_desc+desc
        return 0

    @classmethod
    def _get_adj_description(cls, worldmap):
        for rooms in worldmap:
            desc = ""
            adj_list = list()
            adj_possibilities = {"north", "east", "south", "west"}
            for pos in adj_possibilities:
                if worldmap[rooms]["adjacent"][pos] is not None:
                    adj_list.append(pos)

            adj_string = ""
            for adj in adj_list:
                if adj_list[0] == adj:
                    adj_string += " "+adj
                else:
                    adj_string += ", "+adj
            adj_string += "..."

            if((len(adj_list) == 1)
               and rooms != "room 0" and rooms != "room "+str(len(cls.rooms))):
                desc = factory_data.ADJ_ROOM_DESCRIPTIONS["1"]
            elif len(adj_list) == 2:
                rand_ind = randrange(8)
                desc = factory_data.ADJ_ROOM_DESCRIPTIONS["2"][rand_ind] \
                    + adj_string
            elif len(adj_list) == 3:
                rand_ind = randrange(5)
                desc = factory_data.ADJ_ROOM_DESCRIPTIONS["3"][rand_ind] \
                    + adj_string
            first_desc = worldmap[rooms]["description"] + "\n"
            worldmap[rooms]["description"] = first_desc+desc

        return 0


class MazeFactory:
    """Generate a maze with rooms on intersections, corners, and dead-ends"""

    wall_color, path_color, room_color, player_color = (-2, 2, 1, 0)
    moves = factory_data.MOVES
    rules = factory_data.rules(wall_color, path_color)

    @staticmethod
    def draw(maze):
        """display the maze"""

        plt.figure(figsize=(len(maze[0])//2, len(maze)//2))
        plt.pcolormesh(maze, cmap=plt.cm.get_cmap("tab20b"))
        plt.axis("equal")
        plt.axis("off")
        plt.ion()
        plt.show()

    @staticmethod
    def update(maze):
        """update the maze display"""

        plt.pcolormesh(maze, cmap=plt.cm.get_cmap("tab20b"))
        plt.axis("equal")
        plt.axis("off")
        plt.draw()

    # pylint: disable=R0914
    @staticmethod
    def build():
        """generate a maze"""

        x = choice([10, 12, 14, 18])
        y = 148//x

        maze = npf((x+1, y+1), MazeFactory.wall_color)
        grid = [(i, j) for i in range(1, x+1, 2) for j in range(1, y+1, 2)]
        path = [choice(grid)]
        rooms = []
        position = path[0]
        grid.remove(position)

        while grid:
            n = len(path)
            nsew = []
            for move in MazeFactory.moves:
                nsew.append([
                    tuple(map(add, move[0], position)),
                    tuple(map(add, move[1], position))
                ])
            shuffle(nsew)
            for probe in nsew:
                if probe[0] in grid:
                    maze[probe[0]] = MazeFactory.path_color
                    maze[probe[1]] = MazeFactory.path_color
                    grid.remove(probe[0])
                    path.extend(probe)
                    break
            if n == len(path):
                position = path[max(path.index(position)-1, 1)]
            else:
                position = path[-1]

        for coord in path:
            i, j = coord
            neighbors = [
                maze[i-1, j],
                maze[i+1, j],
                maze[i, j-1],
                maze[i, j+1]
            ]
            if neighbors in MazeFactory.rules:
                rooms.append(coord)
                maze[coord] = MazeFactory.room_color
            maze[rooms[0]] = MazeFactory.player_color

        return {
            "maze": maze.tolist(),
            "rooms": RoomFactory.build(maze, rooms)
        }
