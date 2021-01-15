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
import game_and_analysis_serialisation as serialisationWrapper
from chesscomGameReader import ChessComGameReader
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
        self.dropdown = None

    def initSavedGames(self):
        self.savedGames = serialisationWrapper.loadLastSavedData()
        for game in self.savedGames.storageDict.keys():
            self.chessWindow.dropdown.createButtonForGame(self, game)

    def playMove(self, move: chess.Move):
        if self.game.next() is None:
            self.updateCurrentNode(self.game.add_main_variation(move))
        elif self.game.has_variation(move):
            self.updateCurrentNode(self.game.variation(move))
        else:
            self.updateCurrentNode(self.game.add_variation(move))

    def addGame(self, game, dictQuality):
        if game.end() is not game.game():  # la game est-elle vide ?
            if game not in self.savedGames.storageDict:
                self.savedGames.storageDict.update([(game, dictQuality)])
                self.dropdown.createButtonForGame(self, game)
            elif (dictQuality is not self.savedGames.storageDict[game]):
                self.savedGames.storageDict[game] = dictQuality.copy()

    def loadGame(self, game):
        if (self.game.game() not in self.savedGames):
            self.addGame(self.game.game(), {})
        self.updateCurrentNode(game.end())
        if game.game() in self.savedGames.storageDict:
            if len(self.savedGames.storageDict[game]) > 0:
                self.postAnalysis(self.game, self.savedGames.storageDict[game])

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
            self.boardWidget.update_board()
            self.evalWrapper.update(self.board)
            self.moveList.new_move(self.game, self)
            self.moveListHeader.on_updateGameNode(game)

    def postAnalysis(self, game, moveQualityDict):
        self.moveList.postAnalysis(moveQualityDict.values())
        self.moveListHeader.postAnalysis(moveQualityDict)
        self.moveQualityDict = moveQualityDict
        self.addGame(game, moveQualityDict)
        self.chessWindow.unlockLoad()
        self.updateCurrentNode(game.end())

    def analysisRunning(self):
        for analysis in self.listAnalysis:
            if analysis.running:
                return True
        return False

    def loadChessComGames(self, username: str):
        if(self.savedGames.username != username):
            serialisationWrapper.saveGamesToDisk(self.savedGames)
            self.savedGames = serialisationWrapper.loadGamesFromDisk(username)
        reader = ChessComGameReader(username)
        game = reader.nextGame()
        while (game is not None and game in self.savedGames):
            game = reader.nextGame()
        prev = None
        while game is not None:
            if(game not in self.savedGames):
                self.addGame(game, {})
            prev = game
            game = reader.nextGame()
        if prev is not None:
            self.loadGame(prev)
