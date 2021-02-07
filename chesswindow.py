from kivy.uix.boxlayout import BoxLayout
from colors import BACKGROUND
from keyboard import MyKeyboardListener
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.button import Button
import boardGUI
import arrow
import chess.pgn
import dropbox
import gamecontroller
import movelistheader
import os
from movelist import MoveList
from typing import List, Optional
import openings.openingGraph
from kivy.core.window import Window
from kivy.base import Builder
Builder.load_file("./kv/chesswindow.kv")


class MyFileChooserListView(FileChooserListView):
    loaderWidget = ObjectProperty(None)

    def on_touch_down(self, touch):
        x, y = touch.pos
        if(self.collide_point(x, y) and touch.is_double_tap):
            self.loaderWidget.load(self.path, self.selection)
        else:
            super().on_touch_down(touch)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = ObjectProperty(None)


class ChessWindow(GridLayout):
    couleurBg = BACKGROUND
    opening_color = BooleanProperty(None, allownone=True)
    boardGUI = ObjectProperty(None)
    progressBar = ObjectProperty(None)
    moveList: Optional[MoveList] = ObjectProperty(None)
    loadButton = ObjectProperty(None)
    loadChesscomButton = ObjectProperty(None)
    loadGameButton = ObjectProperty(None)
    analysisButton = ObjectProperty(None)
    moveListHeader = ObjectProperty(None)
    evalBarWidget = ObjectProperty(None)
    inputText = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.controller = gamecontroller.GameController()
        self.controller.chessWindow = self
        self.dropdown = dropbox.GameMenu()
        self.keyboard: MyKeyboardListener = MyKeyboardListener()
        self.openingWidget = None
        self.keyboard.bind_key('r', self.rotate)
        self.keyboard.bind_key('p', self.controller.computerPlay)
        self.keyboard.bind_key('j', self.controller.prevNode)
        self.keyboard.bind_key('l', self.controller.nextNode)
        self.keyboard.bind_key('a', self.controller.analyseFullGame)
        self.keyboard.bind_key('delete', self.controller.deleteNode)
        super().__init__(**kwargs)

    def text_lost_focus(self, focus):
        if not focus:
            if self.keyboard.isClosed():
                self.keyboard.respawn()

    def on_kv_post(self, base_widget):
        self.controller.moveList = self.moveList
        self.controller.boardWidget = self.boardGUI
        self.controller.progressBar = self.progressBar
        self.controller.moveListHeader = self.moveListHeader
        self.controller.dropdown = self.dropdown
        self.controller.initSavedGames()
        self.evalBarWidget.evalWrapper = self.controller.evalWrapper
        self.moveListHeader.threadEngine = self.controller.evalWrapper
        self.inputText.text = self.controller.savedGames.username
        self.boardGUI.setup(self.controller)
        self.controller.post_init_controller()
        return super().on_kv_post(base_widget)

    def rotate(self):
        if(self.boardGUI.pov == 'WHITE'):
            self.boardGUI.pov = 'BLACK'
        else:
            self.boardGUI.pov = 'WHITE'
        self.boardGUI.arrowManager.rotateBoard()
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

    def load_from_chess_com(self):
        username = self.inputText.text
        self.controller.loadChessComGames(username)

    def confirmPopup(self, title, fun_on_accept):
        content = BoxLayout(orientation='horizontal')
        confirm_button = Button(text="Confirm")
        cancel_button = Button(text="Cancel")
        content.add_widget(confirm_button)
        content.add_widget(cancel_button)
        popup = Popup(title=title, content=content,
                      size_hint=(None, None), size=(300, 100))
        confirm_button.bind(on_press=popup.dismiss)
        confirm_button.bind(on_press=lambda x: fun_on_accept())
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
        pass

    def dismiss_popup(self):
        self._popup.dismiss()

    def lockLoad(self):
        self.loadButton.disabled = True
        self.loadChesscomButton.disabled = True
        self.loadGameButton.disabled = True
        self.loadGameButton.disabled = True
        self.analysisButton.disabled = True

    def unlockLoad(self):
        self.loadButton.disabled = False
        self.loadChesscomButton.disabled = False
        self.loadGameButton.disabled = False
        self.analysisButton.disabled = False

    def load_opening(self, white_or_black_bool):
        self.opening_color = white_or_black_bool
        with open(self.getOpeningFile(white_or_black_bool)) as openingFile:
            self.controller.loadGame(chess.pgn.read_game(openingFile))
        Window.size = Window.size[0] + 500, Window.size[1]
        self.controller.openingGame = True
        self.openingWidget = openings.openingGraph.OpeningContainer(
            self.controller.game.game(), self.controller.updateCurrentNode,
            size=(500, Window.size[1]))
        self.add_widget(self.openingWidget)
        self.openingWidget.toggleactivate()
        self.controller.openingWidget = self.openingWidget

    def unload_opening(self, white_or_black_bool):
        if(self.opening_color is not None):
            self.opening_color = None
            self.openingWidget.toggleactivate()
            self.remove_widget(self.openingWidget)
            Window.size = Window.size[0] - 500, Window.size[1]
            with open(self.getOpeningFile(white_or_black_bool), "w") as openingFile:
                openingFile.write(str(self.controller.game.game()))
            self.controller.updateCurrentNode(chess.pgn.Game())
            self.openingWidget = None
            self.controller.openingGame = False
            self.controller.openingWidget = None
        else:
            print("Unloading opening but none were opened")

    def getOpeningFile(self, white_or_black_bool):
        return "./data/WHITE_opening.txt" * white_or_black_bool + \
            "./data/BLACK_opening.txt" * (not white_or_black_bool)
