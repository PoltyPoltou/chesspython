from analysis import GameAnalysis, BoardAnalysisWrapper
import chess.pgn
from movelist import MoveList
from typing import List, Optional
import boardGUI

class GameController():
    moveList: Optional[MoveList] = None
    boardGUI = None

    def __init__(self):
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        self.evalWrapper = BoardAnalysisWrapper(self.board)
        self.evalWrapper.start()

    def playMove(self, move: chess.Move):
        self.moveList.add_move(self.board.turn, self.board.san(
            move), self.board.fullmove_number)
        self.updateCurrentNode(self.game.add_main_variation(move))

    def loadGame(self, game):
        analysis = GameAnalysis()
        analysis.game = game.game()
        analysis.start()
        self.updateCurrentNode(game)
        self.moveList.clearList()

    def computerPlay(self):
        if(self.evalWrapper != None):
            bestMove = self.evalWrapper.bestMove()
            if(self.board.is_legal(bestMove)):
                self.playMove(bestMove)

    def prevNode(self):
        if(self.game.parent != None):
            self.updateCurrentNode(self.game.parent)
            self.moveList.remove_move()

    def nextNode(self):
        if(self.game.next() != None):
            self.moveList.add_move(self.board.turn, self.board.san(
                self.game.next().move), self.board.fullmove_number)
            self.updateCurrentNode(self.game.next())

    def analyseFullGame(self):
        analysis = GameAnalysis()
        analysis.game = self.game.game()
        analysis.start()

    def updateCurrentNode(self, game):
        self.game = game
        self.board = self.game.board()
        self.boardGUI.changeBoard(self.board)
        self.evalWrapper.update(self.board)
