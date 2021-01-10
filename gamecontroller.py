import threading
from analysis import GameAnalysis, BoardAnalysisWrapper, MoveQuality
import chess.pgn
from movelist import MoveList
from typing import List, Optional
import boardGUI


class GameController():
    moveList: Optional[MoveList] = None
    boardGUI = None
    progressBar = None
    chessWindow = None
    moveListHeader = None

    listAnalysis = []

    def __init__(self):
        self.lock = threading.Lock()
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        self.moveQualityDict: dict[chess.pgn.GameNode, MoveQuality] = {}
        self.evalWrapper = BoardAnalysisWrapper(self.board)
        self.evalWrapper.start()

    def playMove(self, move: chess.Move):
        if self.game.next() is None:
            self.updateCurrentNode(self.game.add_main_variation(move))
        elif self.game.has_variation(move):
            self.updateCurrentNode(self.game.variation(move))
        else:
            self.updateCurrentNode(self.game.add_variation(move))

    def loadGame(self, game):
        analysis = GameAnalysis(self)
        analysis.game = game.game()
        analysis.start()
        self.chessWindow.lockLoad()
        self.listAnalysis.append(analysis)
        self.updateCurrentNode(game)

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
            self.game = game
            self.board = self.game.board()
            self.boardGUI.changeBoard(self.board)
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
