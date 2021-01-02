from colors import BACKGROUND
from keyboard import MyKeyboardListener
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
import boardGUI
import arrow
import chess.pgn
import gamecontroller
import os
from movelist import MoveList
from typing import List, Optional


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = ObjectProperty(None)


class ChessWindow(BoxLayout):
    couleurBg = BACKGROUND
    boardGUI = ObjectProperty(None)
    moveList: Optional[MoveList] = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.controller = gamecontroller.GameController()

        self.keyboard: MyKeyboardListener = MyKeyboardListener()
        self.keyboard.bind_key('r', self.rotate)
        self.keyboard.bind_key('p', self.controller.computerPlay)
        self.keyboard.bind_key('j', self.controller.prevNode)
        self.keyboard.bind_key('l', self.controller.nextNode)
        self.keyboard.bind_key('a', self.controller.analyseFullGame)
        self.keyboard.bind_key('o', self.show_load)

        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self.controller.moveList = self.moveList
        self.controller.boardGUI = self.boardGUI
        self.boardGUI.setup(self.controller)
        return super().on_kv_post(base_widget)

    def rotate(self):
        if(self.boardGUI.pov == 'WHITE'):
            self.boardGUI.pov = 'BLACK'
        else:
            self.boardGUI.pov = 'WHITE'
        self.boardGUI.update_board()

    def show_load(self):
        content = LoadDialog(
            load=self.load, cancel=self.dismiss_popup, path=os.curdir)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        pgn = open(os.path.join(path, filename[0]))

        first_game = chess.pgn.read_game(pgn)
        if first_game is not None:
            self.controller.loadGame(first_game)

        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()
