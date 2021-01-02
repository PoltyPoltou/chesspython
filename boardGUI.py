from arrow import Arrow
from analysisWidgets import EvaluationBar
from colors import *
from kivy.base import Builder
from kivy.graphics import *
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.uix.boxlayout import *
from kivy.uix.gridlayout import *
from kivy.uix.image import *
from kivy.uix.widget import Widget
from kivy.input.motionevent import MotionEvent
from movelist import MoveList
from tile import Tile
from typing import List, Optional
import chess
import chess.pgn
import gamecontroller


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
    evalWidget: Optional[EvaluationBar] = ObjectProperty(None, True)
    moveList: Optional[MoveList] = ObjectProperty(None)
    controller: Optional[gamecontroller.GameController] = None

    def __init__(self, **kwargs):
        self.board = None
        self.arrowList = []
        super().__init__(**kwargs)

    def setup(self, controller):
        self.controller = controller
        self.evalWidget.evalWrapper = controller.evalWrapper
        self.changeBoard(self.controller.board)

    def changeBoard(self, board):
        self.board = board
        if(self.hasEval() and not self.evalWidget.isStarted()):
            self.startEval()
        self.evalWidget.update(self.board)

    def hasEval(self):
        return self.evalWidget != None

    def startEval(self):
        self.evalWidget.start()
        pass

    def stopEval(self):
        self.evalWidget.stop()
        pass

    def findTileTouched(self, touch: MotionEvent) -> Tuple[Tile, Widget]:
        for row in self.children:
            for tile in row.children:
                if(tile.collide_point(touch.pos[0], touch.pos[1])):
                    return (tile, row)
        return None, None

    def on_touch_down(self, touch: MotionEvent):
        tileTouched, row = self.findTileTouched(touch)
        if(tileTouched != None and row != None):
            if(touch.button == "left"):
                print(tileTouched.coords, self.children.index(row), row.children.index(tileTouched), "WHITE" *
                      self.board.turn + "BLACK" * (not self.board.turn))
                self.handleSelection(tileTouched)
                self.removeArrows()
            else:
                self.unselectCase()
            if(touch.button == 'right'):
                touch.grab(self)
                self.lastTouchedTile = tileTouched
        return super().on_touch_down(touch)

    def on_touch_up(self, touch: MotionEvent):
        if(touch.button == "right" and touch.grab_current is self):
            tileTouched, row = self.findTileTouched(touch)
            touch.ungrab(self)
            if(tileTouched != None and row != None):
                arrowToDraw: Arrow = Arrow()
                arrowToDraw.setTiles(self.lastTouchedTile, tileTouched)
                if(arrowToDraw.isValid()):
                    self.arrowList.append(arrowToDraw)
                    self.parent.add_widget(arrowToDraw)
        return super().on_touch_up(touch)

    def handleSelection(self, tile: Tile):
        if(self.selectedTile != None):
            if(tile.coords == self.selectedTile.coords):
                self.unselectCase()
            else:
                move = chess.Move.from_uci(
                    self.selectedTile.coords + tile.coords)
                if(self.board.is_legal(move) and not self.board.is_game_over(claim_draw=True)):
                    self.controller.playMove(move)
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

    def removeArrows(self):
        for arr in self.arrowList:
            self.parent.remove_widget(arr)
        self.arrowList = []

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
