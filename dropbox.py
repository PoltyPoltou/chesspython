from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button


class GameButton(Button):

    def __init__(self, game, controller, dropdown, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.controller = controller
        self.dropdown = dropdown

    def loadGame(self, instance):
        self.controller.loadGame(self.game)
        self.dropdown.dismiss()


class GameMenu(DropDown):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.localCount = 1

    def createButtonForGame(self, controller, gameIn):
        game = gameIn.game()
        button = GameButton(game, controller, self,
                            height=44, size_hint=(1, None))

        if "Date" in game.headers and "StartTime" in game.headers and "White" in game.headers and "Black" in game.headers:
            button.text = game.headers["Date"]+" - " + game.headers["StartTime"] + \
                "\n" + game.headers["White"] + " - " + game.headers["Black"]
        else:
            button.text = "Local game - " + str(self.localCount)
            self.localCount += 1
        button.bind(on_release=button.loadGame)
        self.add_widget(button, len(self.children[0].children))
