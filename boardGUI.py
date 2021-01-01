from movelist import MoveList
from typing import List, Optional
import chess
import chess.pgn
from kivy.uix.widget import Widget
from keyboard import MyKeyboardListener
from colors import *
from kivy.graphics import *
from kivy.uix.gridlayout import *
from kivy.uix.boxlayout import *
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.uix.image import *
from kivy.base import Builder
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from tile import Tile
from analysisWidgets import EvaluationBar
from analysis import GameAnalysis
import os

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = ObjectProperty(None)

class Row(GridLayout):
    rowNumber = NumericProperty(0)
    reverseOrder = BooleanProperty(False)


class BoardWidget(GridLayout):
    pov = StringProperty('WHITE')
    imageDir = "images/"
    imageStyleDir = "std/"
    imageDict = {"r": "br.webp", "n": "bn.webp", "b": "bb.webp", "k": "bk.webp", "q": "bq.webp", "p": "bp.webp",
                 "R": "wr.webp", "N": "wn.webp", "B": "wb.webp", "K": "wk.webp", "Q": "wq.webp", "P": "wp.webp"}
    selectedTile: Optional[Tile] = None
    board: Optional[chess.Board] = ObjectProperty(None, True)
    game: Optional[chess.pgn.Game] = ObjectProperty(None, True)
    evalWidget: Optional[EvaluationBar] = ObjectProperty(None, True)
    moveList: Optional[MoveList] = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.keyboard: MyKeyboardListener = MyKeyboardListener()
        self.keyboard.bind_key('r', self.rotate)
        self.keyboard.bind_key('p', self.computerPlay)
        self.keyboard.bind_key('j', self.prevNode)
        self.keyboard.bind_key('l', self.nextNode)
        self.keyboard.bind_key('a', self.analyseFullGame)
        self.keyboard.bind_key('o', self.show_load)
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        if(self.evalWidget != None):
            self.startEval()
        return super().on_kv_post(base_widget)

    def hasEval(self):
        return self.evalWidget != None

    def startEval(self):
        self.evalWidget.start(self.board)
        pass

    def stopEval(self):
        self.evalWidget.stop()
        pass

    def rotate(self):
        if(self.pov == 'WHITE'):
            self.pov = 'BLACK'
        else:
            self.pov = 'WHITE'
        self.update_board()

    def computerPlay(self):
        if(self.evalWidget != None):
            bestMove = self.evalWidget.evalThread.bestMove()
            if(self.board.is_legal(bestMove)):
                self.playMove(bestMove)

    def prevNode(self):
        if(self.game.parent != None):
            self.game = self.game.parent
            self.board = self.game.board()
            self.moveList.remove_move()

    def nextNode(self):
        if(self.game.next() != None):
            self.moveList.add_move(self.board.turn, self.board.san(
                self.game.next().move), self.board.fullmove_number)
            self.game = self.game.next()
            self.board = self.game.board()

    def analyseFullGame(self):
        analysis = GameAnalysis()
        analysis.game = self.game.game()
        analysis.start()

    def playMove(self, move: chess.Move):
        if(self.moveList != None):
            self.moveList.add_move(self.board.turn, self.board.san(
                move), self.board.fullmove_number)
        self.game = self.game.add_main_variation(move)
        self.board = self.game.board()
        self.evalWidget.update(self.board)

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
            self.game = first_game
            self.board = self.game.board()
            self.moveList.clearList()

        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()

    def on_touch_down(self, touch):
        for row in self.children:
            for tile in row.children:
                if(tile.collide_point(touch.pos[0], touch.pos[1])):
                    print(tile.coords, tile.square,
                          self.board.piece_at(tile.square), tile.pieceSourceImg, "WHITE" * self.board.turn + "BLACK" * (not self.board.turn))
                    if(touch.button == "left"):
                        self.handleSelection(tile)
                    else:
                        self.unselectCase()
        return super().on_touch_down(touch)

    def handleSelection(self, tile: Tile):
        if(self.selectedTile != None):
            if(tile.coords == self.selectedTile.coords):
                self.unselectCase()
            else:
                move = chess.Move.from_uci(
                    self.selectedTile.coords + tile.coords)
                if(self.board.is_legal(move) and not self.board.is_game_over(claim_draw=True)):
                    self.playMove(move)
                    self.unselectCase()
                else:
                    self.unselectCase()
                    self.handleSelection(tile)
        else:
            if(self.board.piece_at(tile.square) != None and self.board.piece_at(tile.square).color == self.board.turn):
                self.selectCase(tile)
        self.update_board()

    def unselectCase(self):
        if(self.selectedTile != None):
            self.selectedTile.selected = False
        for row in self.children:
            for tile in row.children:
                tile.movableTo = False
        self.selectedTile = None

    def selectCase(self, tile: Tile):
        self.unselectCase()
        self.selectedTile = tile
        self.selectedTile.selected = True
        for row in self.children:
            for t in row.children:
                if(tile.coords != t.coords):
                    t.movableTo = self.board.is_legal(
                        chess.Move.from_uci(tile.coords + t.coords))

    def update_board(self):
        self.on_board(self, self.board)

    def on_board(self, instance, value):
        lastMoveIndexList: list[int] = []
        if(self.board.move_stack != []):
            lastMoveIndexList.append(self.board.move_stack[-1].from_square)
            lastMoveIndexList.append(self.board.move_stack[-1].to_square)
        for row in self.children:
            for tile in row.children:
                if(isinstance(tile, Tile) and tile.square < 64):
                    if (self.board.piece_at(tile.square) != None):
                        tile.pieceSourceImg = self.imageDir + self.imageStyleDir + \
                            self.imageDict[self.board.piece_at(
                                tile.square).symbol()]
                    else:
                        tile.pieceSourceImg = ""
                    tile.played = tile.square in lastMoveIndexList

    pass
