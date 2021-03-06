from kivy.base import Builder
from typing import Optional
from kivy.uix.image import Image
from kivy.uix.behaviors.button import ButtonBehavior
import chess
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from tile import Tile
import kivy.animation
from typing import List, Dict, Tuple
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
imageDir = "images/"
imageStyleDir = "std/"
imageDict = {"r": "br.webp", "n": "bn.webp", "b": "bb.webp", "k": "bk.webp", "q": "bq.webp", "p": "bp.webp",
             "R": "wr.webp", "N": "wn.webp", "B": "wb.webp", "K": "wk.webp", "Q": "wq.webp", "P": "wp.webp"}
Builder.load_file("./kv/pieceassets.kv")


def setpos(instance, pos):
    instance.pos = pos


def setsize(instance, size):
    instance.size = size


class ChessPieceWidget(Scatter):
    linkedTile: Optional[Tile] = ObjectProperty(allownone=True, rebind=True)
    source: Optional[str] = StringProperty()

    def __init__(self, linkedTile, src, boardwidget, **kwargs):
        self.linkedTile = linkedTile
        super().__init__(**kwargs)
        self.source = src
        self.bindLinkedTile()
        self.boardwidget = boardwidget
        self.grabbed = False

    def on_kv_post(self, base_widget):
        self.do_scale = False
        self.do_rotation = False
        return super().on_kv_post(base_widget)

    def unbindLinkedTile(self):
        self.linkedTile.unbind(pos=setpos)
        self.linkedTile.unbind(size=setsize)

    def bindLinkedTile(self):
        self.linkedTile.bind(pos=setpos)
        self.linkedTile.bind(size=setsize)

    def getRow(self):
        return self.linkedTile.row

    def getColumn(self):
        return ord(self.linkedTile.column) - ord('a')

    def on_touch_down(self, touch):
        if(self.collide_point(touch.x,touch.y)):
            touch.grab(self)
        super().on_touch_down(touch)
        return False # continue the spreading of the event

    def on_touch_up(self, touch):
        if(touch.grab_current is self and touch.button == "left"):
            touch.ungrab(self)
            tile, _ = self.boardwidget.findTileTouched(touch)
            move_made = self.boardwidget.handleSelection(tile)
            #desactivate animation for next board update
            self.boardwidget.anim = False
            if(not move_made):
                self.pos = self.linkedTile.pos
                if(self.linkedTile is not tile):
                    self.boardwidget.selectCase(self.linkedTile)
        super().on_touch_up(touch)
        return False

    def on_transform_with_touch(self, touch):
        self.center = touch.pos
        if(not self.linkedTile.selected):
            self.boardwidget.selectCase(self.linkedTile)
            pass
        return super().on_transform_with_touch(touch)
    pass


class PieceManager:
    def __init__(self, chessTileList: List[Tile], widgetToAdd: Widget, boardWidget) -> None:
        self.pieceDict: dict[chess.Piece, list[ChessPieceWidget]] = {}
        self.board: chess.Board = None
        self._chessTileList: list[Tile] = list(chessTileList)
        self._chessTileList.sort(key=lambda t: t.square)
        self.widgetToAdd = widgetToAdd
        self.boardWidget = boardWidget

    def getTile(self, sq: int) -> Tile:
        if(self._chessTileList[0].square == 0):
            return self._chessTileList[sq]
        else:
            return self._chessTileList[-1-sq]

    def pieceFactory(self, piece: chess.Piece, square: int):
        result = ChessPieceWidget(self.getTile(square),
                                  imageDir + imageStyleDir + imageDict[piece.symbol()],self.boardWidget)
        addToDictList(self.pieceDict, piece, result)
        self.widgetToAdd.add_widget(result)

    def pieceDestroyer(self, piece: chess.Piece, asset: ChessPieceWidget) -> None:
        self.widgetToAdd.remove_widget(asset)
        self.pieceDict[piece].remove(asset)

    def updatePiecesOnBoard(self, board: chess.Board, animation: bool = True):
        boardPieceDict = getDictOfBoard(board)
        def sortByFirstElem(tuple): return tuple[0]
        for pieceKey in boardPieceDict.keys():
            distanceList = []
            alreadyMatchedAssets = set()
            alreadyMatchedSquare = set()
            for square, column, row in boardPieceDict[pieceKey]:
                if(pieceKey in self.pieceDict):
                    for chessPieceAsset in self.pieceDict[pieceKey]:
                        dist = (chessPieceAsset.getRow()-1-row)**2 + \
                            (chessPieceAsset.getColumn()-column)**2
                        distanceList.append((dist,
                                             (chessPieceAsset, (square, column, row))))
            distanceList.sort(key=sortByFirstElem)
            for priority, (asset, (square, column, row)) in distanceList:
                if(asset not in alreadyMatchedAssets and square not in alreadyMatchedSquare):
                    alreadyMatchedAssets.add(asset)
                    alreadyMatchedSquare.add(square)
                    if(priority != 0):
                        if animation:
                            anim = kivy.animation.Animation(
                                pos=self.getTile(square).pos, d=0.15, t="out_cubic")
                            asset.unbindLinkedTile()
                            anim.sqr = self.getTile(square)

                            def endAnimation(
                                    a: kivy.animation.Animation, w: ChessPieceWidget):
                                w.linkedTile = a.sqr
                                w.bindLinkedTile()

                            anim.bind(on_complete=endAnimation)
                            anim.start(asset)

                        else:
                            asset.unbindLinkedTile()
                            asset.linkedTile = self.getTile(square)
                            asset.bindLinkedTile()
            if(pieceKey in self.pieceDict):
                for chessPieceAsset in self.pieceDict[pieceKey]:
                    if(chessPieceAsset not in alreadyMatchedAssets):
                        self.pieceDestroyer(pieceKey, chessPieceAsset)
            for square, column, row in boardPieceDict[pieceKey]:
                if(square not in alreadyMatchedSquare):
                    self.pieceFactory(pieceKey, square)
        for pieceKey in self.pieceDict.keys():
            if(pieceKey not in boardPieceDict.keys()):
                copy_dict = list(self.pieceDict[pieceKey])
                for asset in copy_dict:
                    self.pieceDestroyer(pieceKey, asset)
        pass


def getDictOfBoard(board: chess.Board) -> Dict[chess.Piece,
                                               List[Tuple[int, int, int]]]:
    result = {}
    chess
    for square in range(64):
        piece = board.piece_at(square)
        if(piece is not None):
            addToDictList(result, piece, (square, chess.square_file(
                square), chess.square_rank(square)))
    return result


def addToDictList(dict, key, value):
    if(key in dict):
        dict[key].append(value)
    else:
        dict.update([(key, [value])])
