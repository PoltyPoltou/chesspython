from typing import Set
from chess.pgn import GameNode
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.base import Builder
from kivy.properties import BooleanProperty,StringProperty
Builder.load_file("./kv/dropbox.kv")


class GameButton(ButtonBehavior, Widget):
    selected = BooleanProperty(False)
    text = StringProperty("")
    instances = set()

    def __init__(self, game, controller, dropdown, **kwargs):
        self.selected = False
        super().__init__(**kwargs)
        self.game = game
        self.controller = controller
        self.dropdown = dropdown
        GameButton.instances.add(self)

    def loadGame(self, instance):
        self.dropdown.dismiss()
        self.controller.loadGame(self.game)
        for b in GameButton.instances:
            b.selected = False
        self.selected = True


class GameMenu(DropDown):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.localCount = 1

    def createButtonForGame(self, controller, gameIn):
        game = gameIn.game()
        button = GameButton(game, controller, self,
                            height=44, size_hint=(1, None))

        if "Date" in game.headers and "StartTime" in game.headers and "White" in game.headers and "Black" in game.headers:
            button.text = game.headers["Date"] + " - " + game.headers["StartTime"] + \
                "\n" + game.headers["White"] + " - " + game.headers["Black"]
        else:
            button.text = "Local game - " + str(self.localCount)
            self.localCount += 1
        button.bind(on_release=button.loadGame)
        self.add_widget(button, len(self.children[0].children))

    def get_top_game(self):
        return self.children[0].children[-1].game.game()
