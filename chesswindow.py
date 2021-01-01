from analysis import GameAnalysis
from colors import BACKGROUND
from keyboard import MyKeyboardListener
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
import boardGUI
import chess.pgn
import os

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = ObjectProperty(None)

class ChessWindow(BoxLayout):
    couleurBg = BACKGROUND
    boardGUI = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.keyboard: MyKeyboardListener = MyKeyboardListener()
        self.keyboard.bind_key('r', self.rotate)
        self.keyboard.bind_key('p', self.computerPlay)
        self.keyboard.bind_key('j', self.prevNode)
        self.keyboard.bind_key('l', self.nextNode)
        self.keyboard.bind_key('a', self.analyseFullGame)
        self.keyboard.bind_key('o', self.show_load)
        super().__init__(**kwargs)

    def rotate(self):
        if(self.boardGUI.pov == 'WHITE'):
            self.boardGUI.pov = 'BLACK'
        else:
            self.boardGUI.pov = 'WHITE'
        self.boardGUI.update_board()

    def computerPlay(self):
        if(self.boardGUI.evalWidget != None):
            bestMove = self.boardGUI.evalWidget.evalThread.bestMove()
            if(self.boardGUI.board.is_legal(bestMove)):
                self.boardGUI.playMove(bestMove)

    def prevNode(self):
        if(self.boardGUI.game.parent != None):
            self.boardGUI.game = self.boardGUI.game.parent
            self.boardGUI.board = self.boardGUI.game.board()
            self.boardGUI.moveList.remove_move()

    def nextNode(self):
        if(self.boardGUI.game.next() != None):
            self.boardGUI.moveList.add_move(self.boardGUI.board.turn, self.boardGUI.board.san(
                self.boardGUI.game.next().move), self.boardGUI.board.fullmove_number)
            self.boardGUI.game = self.boardGUI.game.next()
            self.boardGUI.board = self.boardGUI.game.board()

    def analyseFullGame(self):
        analysis = GameAnalysis()
        analysis.game = self.boardGUI.game.game()
        analysis.start()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=os.curdir)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        pgn = open(os.path.join(path, filename[0]))

        first_game = chess.pgn.read_game(pgn)
        if first_game is not None:
            analysis = GameAnalysis()
            analysis.game = first_game.game()
            analysis.start()
            self.boardGUI.game = first_game
            self.boardGUI.board = self.boardGUI.game.board()
            self.boardGUI.moveList.clearList()

        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()
