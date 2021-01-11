from __future__ import annotations
from typing import TYPE_CHECKING
if(TYPE_CHECKING):
    from typing import List, Optional
    from movelist import MoveList
    from chesswindow import ChessWindow
    from boardGUI import BoardWidget
    from analysisWidgets import AnalysisProgressBar, HeadMoveList
import threading
from analysis import GameAnalysis, BoardAnalysisWrapper, MoveQuality
import chess.pgn


class GameController():
    moveList: Optional[MoveList] = None
    boardWidget: Optional[BoardWidget] = None
    progressBar: Optional[AnalysisProgressBar] = None
    chessWindow: Optional[ChessWindow] = None
    moveListHeader: Optional[HeadMoveList] = None

    listAnalysis = []

    def __init__(self):
        self.lock = threading.Lock()
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        self.moveQualityDict: dict[chess.pgn.GameNode, MoveQuality] = {}
        self.evalWrapper = BoardAnalysisWrapper(self.board)
        self.evalWrapper.start()
        self.mapAllGame = {}
        self.dropdown = None

    def playMove(self, move: chess.Move):
        if self.game.next() is None:
            self.updateCurrentNode(self.game.add_main_variation(move))
        elif self.game.has_variation(move):
            self.updateCurrentNode(self.game.variation(move))
        else:
            self.updateCurrentNode(self.game.add_variation(move))

    def addGame(self, game, dictQuality):
        if game.end() is not game.game():
            if game not in self.mapAllGame:
                self.mapAllGame.update([(game, {})])
                self.dropdown.createButtonForGame(self, game)
            self.mapAllGame[game] = dictQuality.copy()

    def loadGame(self, game):
        self.addGame(self.game.game(), self.moveQualityDict)
        self.updateCurrentNode(game)
        if game.game() in self.mapAllGame:
            self.moveQualityDict = self.mapAllGame[game]
            if len(self.moveQualityDict) > 0:
                self.postAnalysis(self.game, self.moveQualityDict)

    def computerPlay(self):
        if(self.evalWrapper != None):
            bestMove = self.evalWrapper.bestMove()
            if(self.board.is_legal(bestMove)):
                self.playMove(bestMove)

    def prevNode(self):
        if(self.game.parent != None):
            self.updateCurrentNode(self.game.parent)

    def nextNode(self):
        if(self.game.next() != None):
            self.updateCurrentNode(self.game.next())

    def analyseFullGame(self):
        if not self.analysisRunning():
            analysis = GameAnalysis(self)
            analysis.game = self.game.game()
            analysis.start()
            self.listAnalysis.append(analysis)
            self.chessWindow.lockLoad()

    def updateCurrentNode(self, game):
        with self.lock:
            if self.game.game() is not game.game():
                self.moveQualityDict.clear()
            self.game = game
            self.board = self.game.board()
            self.boardWidget.board = self.board
            self.evalWrapper.update(self.board)
            self.moveList.new_move(self.game, self)
            self.moveListHeader.on_updateGameNode(game)

    def postAnalysis(self, game, moveQualityDict):
        self.moveList.postAnalysis(moveQualityDict.values())
        self.moveListHeader.postAnalysis(moveQualityDict)
        self.moveQualityDict = moveQualityDict
        self.chessWindow.unlockLoad()
        self.updateCurrentNode(game.end())

    def analysisRunning(self):
        for analysis in self.listAnalysis:
            if analysis.running:
                return True
        return False
