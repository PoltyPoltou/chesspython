from __future__ import annotations
from typing import TYPE_CHECKING
if(TYPE_CHECKING):
    from typing import List, Optional
    from movelist import MoveList
    from chesswindow import ChessWindow
    from boardGUI import BoardWidget
    from analysisWidgets import AnalysisProgressBar
    from movelistheader import HeadMoveList
    from openings.openingGraph import OpeningContainer
import threading
from analysis import GameAnalysis, BoardAnalysisWrapper, MoveQuality
import game_and_analysis_serialisation as serialisationWrapper
from chesscomGameReader import ChessComGameReader
import chess.pgn
import chess.engine


class GameController():
    moveList: Optional[MoveList] = None
    boardWidget: Optional[BoardWidget] = None
    progressBar: Optional[AnalysisProgressBar] = None
    chessWindow: Optional[ChessWindow] = None
    moveListHeader: Optional[HeadMoveList] = None
    openingWidget: Optional[OpeningContainer] = None
    listAnalysis = []

    def __init__(self):
        self.lock = threading.Lock()
        self.game = chess.pgn.Game()
        self.board = self.game.board()
        self.moveQualityDict: dict[chess.pgn.GameNode, MoveQuality] = {}
        self.localAnalyses: dict[chess.pgn.GameNode,
                                 chess.engine.InfoDict] = {}
        self.evalWrapper = BoardAnalysisWrapper(self.board)
        self.evalWrapper.addEvalEventListener(self)
        self.evalWrapper.start()
        self.dropdown = None
        self.openingGame = False

    def post_init_controller(self):
        self.updateCurrentNode(self.game)

    def newEngineEvalEvent(self):
        '''
        updates the dict of already analysed positions in this runtime
        '''
        eval = self.evalWrapper.getEngineAnalysis()
        if("depth" in eval and self.evalWrapper.hasFinished()):
            if(self.game in self.localAnalyses):
                if(eval["depth"] > self.localAnalyses[self.game]["depth"]):
                    self.localAnalyses[self.game] = eval
            else:
                self.localAnalyses.update([(self.game, eval)])

    def initSavedGames(self):
        self.savedGames = serialisationWrapper.loadLastSavedData()
        for game in self.savedGames.storageDict.keys():
            self.chessWindow.dropdown.createButtonForGame(self, game)
        purged_games = {}
        for game in self.savedGames.storageDict:
            is_present = self.is_game_already_saved(purged_games, game)
            if(not is_present):
                purged_games.update(
                    [(game, self.savedGames.storageDict[game])])
        self.savedGames.storageDict = purged_games

    def is_game_already_saved(self, mapping, game):
        if("Date" in game.headers and "StartTime" in game.headers):
            for g in mapping:
                if(g is game):
                    return True
                if("Date" in g.headers and "StartTime" in g.headers):
                    if(g.headers["Date"] == game.headers["Date"] and
                            g.headers["StartTime"] == game.headers["StartTime"]):
                        return True
        return False

    def playMove(self, move: chess.Move):
        if self.game.next() is None:
            new_node = self.game.add_main_variation(move)
            if(self.openingWidget is not None):
                self.openingWidget.actualize_node(self.game)
            self.updateCurrentNode(new_node)
        elif self.game.has_variation(move):
            self.updateCurrentNode(self.game.variation(move))
        else:
            new_node = self.game.add_variation(move)
            if(self.openingWidget is not None):
                self.openingWidget.actualize_node(self.game)
            self.updateCurrentNode(new_node)

    def deleteNode(self):
        old_game = self.game

        def confirmDeleteNode():
            self.updateCurrentNode(self.game.parent)
            self.game.remove_variation(old_game)
            if(self.openingWidget is not None):
                self.openingWidget.remove_node_and_children(old_game)
        title = "Delete node ? " + str((self.game.ply() + 1) // 2) + "." + \
            (".." * ((self.game.ply() - 1) % 2)) + " " + self.game.san()
        self.chessWindow.confirmPopup(title, confirmDeleteNode)

    def addGame(self, game, dictQuality):
        if game.end() is not game.game():  # la game est-elle vide ?
            if game not in self.savedGames.storageDict:
                self.savedGames.storageDict.update([(game, dictQuality)])
                self.dropdown.createButtonForGame(self, game)
            elif (dictQuality is not self.savedGames.storageDict[game]):
                self.savedGames.storageDict[game] = dictQuality.copy()

    def loadGame(self, game):
        if (self.game.game() not in self.savedGames and self.game.game()
                is not self.game.end() and self.openingGame is None):
            self.addGame(self.game.game(), self.moveQualityDict)
        self.updateCurrentNode(game.end())
        self.moveList.scroll_y = 0
        if game.game() in self.savedGames.storageDict:
            if len(self.savedGames.storageDict[game]) > 0:
                self.postAnalysis(self.game, self.savedGames.storageDict[game])

    def computerPlay(self):
        if(self.evalWrapper is not None):
            bestMove = self.evalWrapper.bestMove()
            if(self.board.is_legal(bestMove)):
                self.playMove(bestMove)

    def prevNode(self):
        if(self.game.parent is not None):
            self.updateCurrentNode(self.game.parent)

    def nextNode(self):
        if(self.game.next() is not None):
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
                self.moveQualityDict = self.savedGames.storageDict.get(
                    self.game.game(), {})
            self.game = game
            self.board = self.game.board()
            self.boardWidget.board = self.board
            self.boardWidget.update_board()
            if(self.game not in self.localAnalyses or self.localAnalyses[self.game]["depth"] < self.evalWrapper.getDefaultDepth()):
                self.evalWrapper.update(self.board)
            else:
                self.evalWrapper.setInfoDict(self.localAnalyses[self.game])
            self.moveList.new_move(self.game, self)
            self.moveListHeader.on_updateGameNode(game)
            if(self.openingWidget is not None):
                self.openingWidget.select_node(game)

    def postAnalysis(self, game, moveQualityDict):
        self.moveQualityDict = moveQualityDict
        self.moveList.postAnalysis(moveQualityDict.values())
        self.moveListHeader.postAnalysis(moveQualityDict)
        self.moveQualityDict = moveQualityDict
        self.savedGames.storageDict.update([(game.game(), moveQualityDict)])
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
                is_present = self.is_game_already_saved(
                    self.savedGames.storageDict, game)
                if(not is_present):
                    self.addGame(game, {})
            prev = game
            game = reader.nextGame()
        if prev is not None:
            self.loadGame(prev)
