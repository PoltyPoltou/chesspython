from typing import List, Optional
import chess
from kivy.uix.widget import Widget
from keyboard import KeyboardListener
from colors import *
from kivy.graphics import *
from kivy.uix.gridlayout import *
from kivy.uix.boxlayout import *
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.uix.image import *
from kivy.base import Builder
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from tile import Tile


class Row(GridLayout):
    rowNumber = NumericProperty(0)
    reverseOrder = BooleanProperty(False)


class BoardWidget(GridLayout, KeyboardListener):
    pov = StringProperty('WHITE')
    board: Optional[chess.Board] = ObjectProperty(None, True)
    imageDir = "images/"
    imageStyleDir = "std/"
    imageDict = {"r": "br.webp", "n": "bn.webp", "b": "bb.webp", "k": "bk.webp", "q": "bq.webp", "p": "bp.webp",
                 "R": "wr.webp", "N": "wn.webp", "B": "wb.webp", "K": "wk.webp", "Q": "wq.webp", "P": "wp.webp"}
    selectedTile: Optional[Tile] = None

    def __init__(self, **kwargs):
        self.initKeyboard()
        self.bind_key('r', self.rotate)
        super().__init__(**kwargs)

    def rotate(self, key, modifiers):
        if(self.pov == 'WHITE'):
            self.pov = 'BLACK'
        else:
            self.pov = 'WHITE'
        self.update_board()

    def playMove(self, move: chess.Move):
        self.board.push(move)
        self.update_board()

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
                if(self.board.is_legal(move)):
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
