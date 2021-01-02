from analysis import GameAnalysis, BoardAnalysisWrapper
import chess.pgn
from movelist import MoveList
from typing import List, Optional
import boardGUI

class GameController():
    moveList: Optional[MoveList] = None
    boardGUI = None

    listAnalysis = []

    def __init__(self):
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        self.evalWrapper = BoardAnalysisWrapper(self.board)
        self.evalWrapper.start()

    def playMove(self, move: chess.Move):
        self.updateCurrentNode(self.game.add_main_variation(move))

    def loadGame(self, game):
        analysis = GameAnalysis()
        analysis.game = game.game()
        analysis.start()
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
        analysis = GameAnalysis()
        analysis.game = self.game.game()
        analysis.start()
        self.listAnalysis.append(analysis)

    def updateCurrentNode(self, game):
        self.game = game
        self.board = self.game.board()
        self.boardGUI.changeBoard(self.board)
        self.evalWrapper.update(self.board)
        self.refreshFullMoveList()

    def refreshFullMoveList(self):
        # recreate move list
        self.moveList.clearList()
        curGame = self.game.game().next()
        while curGame is not None:
            self.moveList.add_move(curGame, self)
            curGame = curGame.next()

