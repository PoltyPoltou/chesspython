from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.clock import Clock
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
        self.watching = False
        self.watch_chesscom_reader = None
        self.watching_trigger = Clock.create_trigger(
            self.watch_new_game, interval=True, timeout=60)

    def watch_chess_com(self):
        self.watching = not self.watching
        if(self.watching):
            self.loadGame(self.chessWindow.dropdown.get_top_game())
            self.watching_trigger()
            self.watch_chesscom_reader = ChessComGameReader(self.chessWindow.get_input_text())
            while(self.watch_chesscom_reader.nextGame() is not None):
                pass #iterates over the games available to be at the last one
        else:
            self.watching_trigger.cancel()

    def watch_new_game(self, dt):
        if(not self.analysisRunning()):
            new_game = self.watch_chesscom_reader.nextGame()
            if(new_game is not None):
                self.updateCurrentNode(new_game.end())
                self.analyseFullGame()
        pass

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
        for g in mapping:
            if(game_headers_equality(g,game)):
                return True
        return False

    def playMove(self, move: chess.Move):
        if self.game.next() is None:
            new_node = self.game.add_main_variation(move)
            self.moveList.go_to_bottom()
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
                self.postAnalysis(self.game, self.savedGames.storageDict[game.game()])  
                self.progressBar.drawAllMeshes_from_qualitymove(
                    self.savedGames.storageDict[game.game()])
        self.chessWindow.rotate_defined(game.game().headers["White"].lower() == self.chessWindow.get_input_text())

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
            if(game is not self.game):
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
                self.moveListHeader.redraw_engine_variation(0)
                if(self.openingWidget is not None):
                    self.openingWidget.select_node(game)

    def postAnalysis(self, game, moveQualityDict):
        self.moveQualityDict = moveQualityDict
        self.moveList.postAnalysis(moveQualityDict)
        self.moveListHeader.postAnalysis(moveQualityDict)
        self.moveQualityDict = moveQualityDict
        self.savedGames.storageDict.update([(game.game(), moveQualityDict)])
        self.chessWindow.unlockLoad()
        analysisDict = {}
        for key in moveQualityDict:
            if not moveQualityDict[key].theoric:
                analysisDict.update([(key,moveQualityDict[key].evalDict)])
        self.localAnalyses.update(analysisDict)
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


def game_headers_equality(
        g1: chess.pgn.Game,
        g2: chess.pgn.Game) -> bool:
    '''
     is not suitable to detect changes between g1 and g2
    '''
    if(g1 is g2):
        return True
    h1: chess.pgn.Headers = g1.game().headers
    h2: chess.pgn.Headers = g2.game().headers
    if(h1["White"] != "?" and h2["White"] != "?" and h1["Black"] != "?" and h2["Black"] != "?"):
        return h1["White"] ==  h2["White"] and \
                h1["Black"] ==  h2["Black"] and \
                (not ("StartTime" in h1 and "StartTime" in h2)  or h1["StartTime"] == h1["StartTime"]) and \
                (not ("Date" in h1 and "Date" in h2)  or h1["Date"] == h1["Date"]) and\
                g1.end().board().fen() == g2.end().board().fen() 
    else:
        return g1.end().board().fen() == g2.end().board().fen() 
