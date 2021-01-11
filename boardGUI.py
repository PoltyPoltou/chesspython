from chess.svg import board
from kivy.clock import Clock
from arrow import ArrowManager, arrow_factory
from analysisWidgets import EvaluationBar
from colors import *
from kivy.base import Builder
from kivy.graphics import *
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.anchorlayout import *
from kivy.uix.behaviors import *
from kivy.uix.boxlayout import *
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import *
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.input.motionevent import MotionEvent
from movelist import MoveList
from tile import Tile
from typing import List, Optional
import chess
import chess.pgn


class Row(GridLayout):
    rowNumber = NumericProperty(0)
    reverseOrder = BooleanProperty(False)


class PromotionBubble(ModalView):
    color = BooleanProperty(chess.WHITE)
    promotePlay = ObjectProperty(None)
    pieceDir = StringProperty("")

    def __init__(self, attachWidget, color, pieceDir, **kwargs):
        self.attach_to = attachWidget
        self.color = color
        self.pieceDir = pieceDir
        super().__init__(**kwargs)

    def dismiss(self, *largs, **kwargs):
        self.clear_widgets()
        self.attach_to.unselectCase()
        return super().dismiss(*largs, **kwargs)

    pass


class BoardWidget(GridLayout):
    pov = StringProperty('WHITE')
    imageDir = "images/"
    imageStyleDir = "std/"
    imageDict = {"r": "br.webp", "n": "bn.webp", "b": "bb.webp", "k": "bk.webp", "q": "bq.webp", "p": "bp.webp",
                 "R": "wr.webp", "N": "wn.webp", "B": "wb.webp", "K": "wk.webp", "Q": "wq.webp", "P": "wp.webp"}
    selectedTile: Optional[Tile] = None
    board: Optional[chess.Board] = ObjectProperty(None, rebind=True)
    evalBarWidget: Optional[EvaluationBar] = ObjectProperty(None)
    moveList: Optional[MoveList] = ObjectProperty(None)
    controller = None

    def __init__(self, **kwargs):
        self.board = None
        self.analysisArrow = None
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self.arrowManager = ArrowManager(self.parent)
        if(self.evalBarWidget is not None):
            self.bestMove = None
        return super().on_kv_post(base_widget)

    def setup(self, controller):
        self.controller = controller
        self.controller.evalWrapper.addEvalEventListener(self)
        self.board = self.controller.board
        if(self.hasEval() and not self.evalBarWidget.isStarted()):
            self.startEval()

    def hasEval(self):
        return self.evalBarWidget != None

    def startEval(self):
        self.evalBarWidget.start()
        pass

    def stopEval(self):
        self.evalBarWidget.stop()
        pass

    def newEngineEvalEvent(self):
        if(self.controller.evalWrapper.hasAnalysis()):
            bestMove = self.controller.evalWrapper.bestMove()
            if(bestMove is not None):
                tileFrom = self.findTileWidgetFromSquare(bestMove.from_square)
                tileTo = self.findTileWidgetFromSquare(bestMove.to_square)
                self.arrowManager.addEngineArrow(tileFrom, tileTo)

    def findTile(self, coords) -> Tile:
        for row in self.children:
            for tile in row.children:
                if(tile.coords == coords):
                    return tile
        return None

    def findTileWidgetFromSquare(self, square: chess.Square):
        return self.findTile(chess.square_name(square))

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
                self.arrowManager.removeArrows()
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
                self.arrowManager.addArrow(self.lastTouchedTile, tileTouched)
        return super().on_touch_up(touch)

    def handleSelection(self, tile: Tile):
        if(self.selectedTile != None):
            if(tile.coords == self.selectedTile.coords):
                self.unselectCase()
            else:
                move = chess.Move.from_uci(
                    self.selectedTile.coords + tile.coords)
                movePromoteTest = chess.Move.from_uci(
                    self.selectedTile.coords + tile.coords + 'q')
                isPromoteLegal = self.board.is_legal(movePromoteTest)
                if(self.board.is_legal(move) and not self.board.is_game_over(claim_draw=True)):
                    self.controller.playMove(move)
                    self.unselectCase()
                else:
                    if(isPromoteLegal and not self.board.is_game_over(claim_draw=True)):
                        color = self.board.piece_at(
                            self.selectedTile.square).color
                        promotebb = PromotionBubble(self,
                                                    color, self.imageDir + self.imageStyleDir)

                        def playMove(promoteChar):
                            moveToPlay = chess.Move.from_uci(
                                self.selectedTile.coords + tile.coords + promoteChar)
                            if(self.board.is_legal(moveToPlay)):
                                self.controller.playMove(moveToPlay)
                                self.unselectCase()
                            promotebb.dismiss()

                        promotebb.promotePlay = playMove
                        promotebb.open()
                    else:
                        self.unselectCase()
                        self.handleSelection(tile)
        else:
            if(self.board.piece_at(tile.square) != None and self.board.piece_at(tile.square).color == self.board.turn):
                self.selectCase(tile)

    def unselectCase(self):
        if(self.selectedTile != None):
            self.selectedTile.selected = False
        for row in self.children:
            for tile in row.children:
                tile.movableTo = False
                tile.canBeTaken = False
        self.selectedTile = None

    def selectCase(self, tile: Tile):
        self.unselectCase()
        self.selectedTile = tile
        self.selectedTile.selected = True
        for row in self.children:
            for t in row.children:
                if(tile.coords != t.coords):
                    t.movableTo = self.board.is_legal(
                        chess.Move.from_uci(tile.coords + t.coords)) or self.board.is_legal(
                        chess.Move.from_uci(tile.coords + t.coords + 'q'))
                    if(t.movableTo and self.board.piece_at(t.square) is not None):
                        t.canBeTaken = True
                        t.movableTo = False

    def update_board(self):
        self.on_board(self, self.board)

    def on_board(self, instance, value):
        self.newEngineEvalEvent()
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
        # On a une analyse de la partie en cours, alors on affiche le meilleur coup précedant
        self.arrowManager.removeOneArrow(self.analysisArrow)
        if(self.controller.game in self.controller.moveQualityDict):
            bestMove: chess.Move = self.controller.moveQualityDict[
                self.controller.game].bestMove
            self.analysisArrow = self.arrowManager.directAddArrow(self.findTileWidgetFromSquare(
                bestMove.from_square), self.findTileWidgetFromSquare(bestMove.to_square), (6/255, 101/255, 22/255, 0.8))
            pass
    pass
