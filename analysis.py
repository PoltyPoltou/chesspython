from logging import exception
import threading
from typing import Optional, TYPE_CHECKING
import chess
import chess.pgn
import chess.engine
import time
import os
from kivy.clock import Clock
if TYPE_CHECKING:
    import gamecontroller


class BoardAnalysisWrapper():
    class ThreadContinuousEvaluation(threading.Thread):
        def __init__(self, wrapper):
            super().__init__()
            self.wrapper: BoardAnalysisWrapper = wrapper
            self.infoMove: chess.engine.InfoDict = None
            self.defaultDepth = 18
            self.stopFlag = False
            self.threads = 3
            self.setDaemon(True)
            self.finished = False

        def run(self):
            print("Eval thread Launched")
            while(not self.stopFlag):
                boardCopy = self.wrapper.board
                with self.wrapper.engine.analysis(boardCopy, chess.engine.Limit(depth=self.defaultDepth), multipv=1, options={"threads": self.threads}) as analysis:
                    for info in analysis:
                        if(info.get('score') is not None):
                            self.infoMove = info
                            self.wrapper.dispatcher()
                        if(self.stopFlag or self.wrapper.board.fen() != boardCopy.fen()):
                            break

                    self.finished = self.wrapper.board.fen() == boardCopy.fen()
                    # on dors si l'analyse est finie (limit atteinte)
                    while(not self.stopFlag and self.finished):
                        time.sleep(0.1)
            self.wrapper.engine.quit()
            print("Eval thread Killed")
        pass

    def __init__(self, board, engineStr="DEFAULT"):
        if engineStr == "DEFAULT":
            if os.name.startswith('posix'):
                engineStr = "./engines/stockfish_20090216_x64_bmi2"
            else:
                engineStr = "./engines/stockfish12.exe"
        self.board: chess.Board = board
        self.engine: chess.engine.SimpleEngine = chess.engine.SimpleEngine.popen_uci(
            engineStr)
        self._evalThread = self.ThreadContinuousEvaluation(self)
        self.listenerList = []
        self.dispatcher = Clock.create_trigger(
            self.notifyListener, interval=True, timeout=1 / 30)

    def update(self, board):
        self.board = board
        self._evalThread.finished = False

    def start(self):
        self._evalThread.start()

    def hasAnalysis(self):
        return self._evalThread.infoMove is not None

    def getEngineAnalysis(self):
        return self._evalThread.infoMove.copy()

    def setInfoDict(self, infoDict):
        self._evalThread.infoMove = infoDict
        self.notifyListener(0)

    def bestMove(self):
        if 'pv' in self._evalThread.infoMove and len(
                self._evalThread.infoMove.get('pv')) > 0:
            return self._evalThread.infoMove.get('pv')[0]
        return None

    def bestVariant(self):
        if 'pv' in self._evalThread.infoMove:
            return self._evalThread.infoMove.get('pv').copy()
        else:
            return None

    def getDepth(self):
        if 'depth' in self._evalThread.infoMove:
            return self._evalThread.infoMove.get('depth')
        else:
            return None

    def getDefaultDepth(self):
        return self._evalThread.defaultDepth

    def setDefaultDepth(self, depth: int):
        if(depth != self._evalThread.defaultDepth):
            self._evalThread.finished = False
        self._evalThread.defaultDepth = depth

    def stop(self):
        self._evalThread.stopFlag = True

    def hasFinished(self):
        return self._evalThread.finished

    def notifyListener(self, dt):
        for listener in self.listenerList:
            listener.newEngineEvalEvent()

    def addEvalEventListener(self, listener):
        if(hasattr(listener, "newEngineEvalEvent")):
            self.listenerList.append(listener)
        else:
            raise Exception(
                "Listener added to ThreadContinuousEvaluation without newEngineEvalEvent function")


class MoveQuality:
    def __init__(
            self,
            move,
            quality=None,
            bestMove=None,
            sanMove=None,
            sanBestMove=None,
            theoric=False):
        self.move: chess.Move = move
        self.bestMove: Optional[chess.Move] = bestMove
        self.quality = quality
        self.sanMove = sanMove
        self.sanBestMove = sanBestMove
        self.theoric = theoric

    def isPerfect(self):
        return (not self.theoric) and self.quality >= 0

    def isGood(self):
        return (not self.theoric) and self.quality >= -20 and self.quality < 0

    def isOk(self):
        return (not self.theoric) and self.quality >= - \
            75 and self.quality < -20

    def isImprecision(self):
        return (not self.theoric) and self.quality >= - \
            150 and self.quality < -75

    def isError(self):
        return (not self.theoric) and self.quality >= - \
            400 and self.quality < -150

    def isBlunder(self):
        return (not self.theoric) and self.quality < -400

    def getColor(self):
        if self.isPerfect():
            return (50 / 256, 161 / 256, 144 / 256, 1)
        elif self.isGood():
            return (105 / 256, 163 / 256, 38 / 256, 1)
        elif self.isOk():
            return (0.75, 0.75, 0.75, 1)
        elif self.isImprecision():
            return (255 / 256, 213 / 256, 0, 1)
        elif self.isError():
            return (214 / 256, 137 / 256, 4 / 256, 1)
        elif self.isBlunder():
            return (105 / 256, 15 / 256, 12 / 256, 1)
        elif self.theoric:
            return (0, 102 / 255, 204 / 255, 1)

    def getHexColor(self):
        color = self.getColor()
        return ('%02x%02x%02x' %
                (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))

    def __str__(self):
        if(self.theoric):
            return "Theoric"  # dans le cahier
        if(self.isPerfect()):
            return "Perfect"
        if(self.isGood()):
            return "Good"
        if(self.isOk()):
            return "Ok"
        if(self.isImprecision()):
            return "Imprecision"
        if(self.isError()):
            return "Error"
        if(self.isBlunder()):
            return "Blunder"


class GameAnalysis(threading.Thread):

    def __init__(self, controller):
        super().__init__()
        self.game = None
        self.stopFlag = False
        self.wrapper = None
        self.controller: gamecontroller = controller
        self.running = False

    def analyseGame(self, game: chess.pgn.Game):
        if(game is not game.end()):
            evalList = []
            curGame = game
            size = game.end().board().ply()
            board = curGame.board()

            with open(self.controller.chessWindow.getOpeningFile(True)) as pgn:
                white_open_game = chess.pgn.read_game(pgn)
            is_white_opening = game.headers["White"].lower(
            ) == white_open_game.headers["White"].lower()

            with open(self.controller.chessWindow.getOpeningFile(False)) as pgn:
                black_open_game = chess.pgn.read_game(pgn)
            is_black_opening = game.headers["Black"].lower(
            ) == black_open_game.headers["Black"].lower()
            opening_game = white_open_game if is_white_opening else (
                black_open_game if is_black_opening else None)
            theory_info_dict = {
                "theoric": True,
                "score": chess.engine.PovScore(
                    chess.engine.Cp(0),
                    chess.WHITE)}
            self.wrapper = BoardAnalysisWrapper(board)
            self.wrapper.start()

            self.controller.progressBar.newEval()
            self.controller.progressBar.progressDelta = 1 / size

            while curGame is not None and not self.stopFlag:
                # equivalent to : opening_game is not None and ...
                if((is_white_opening or is_black_opening) and opening_game.next() is not None and curGame.next().move is not None and (opening_game.next().move == curGame.next().move)):
                    evalList.append((curGame.move, theory_info_dict))
                    opening_game = opening_game.next()
                else:
                    self.wrapper.update(curGame.board())
                    while not self.wrapper.hasFinished() and not self.stopFlag:
                        time.sleep(0.1)
                    if(self.wrapper.bestMove() is not None):
                        info_dict = self.wrapper.getEngineAnalysis()
                        # the last theory move need to have analysis (to
                        # qualify next move)
                        if(is_white_opening or is_black_opening):
                            info_dict.update([("theoric", True)])
                        evalList.append((curGame.move, info_dict))
                    is_white_opening = False  # the opening has ended we don't check anymore
                    is_black_opening = False  # the opening has ended we don't check anymore
                self.controller.progressBar.addEval(evalList[-1][1])
                curGame = curGame.next()
            self.wrapper.stop()
            return evalList
        else:
            return []

    def analyseMoves(self, evalList):
        nodeToMoveQualityMap = {}
        evalPrev = None
        gameNode: chess.pgn.GameNode = self.game.game()
        color = chess.BLACK
        for i in range(len(evalList)):
            if(not isinstance(gameNode, chess.pgn.Game)):
                move, eval = evalList[i]
                if("theoric" in eval):
                    nodeToMoveQualityMap.update(
                        [(gameNode, MoveQuality(move, 0, sanMove=gameNode.san(), theoric=True))])
                else:
                    bestMove = evalPrev.get('pv')[0]
                    sanMove = gameNode.san()
                    sanBestMove = gameNode.parent.board().san(bestMove)
                    if(move == bestMove):
                        nodeToMoveQualityMap.update([(gameNode, MoveQuality(
                            move, 0, bestMove, sanMove, sanBestMove))])
                    else:
                        score = eval["score"].white(
                        ) if color else eval["score"].black()
                        prevScore = evalPrev["score"].white(
                        ) if color else evalPrev["score"].black()
                        if score.score() is not None and prevScore.score() is not None:
                            nodeToMoveQualityMap.update([(gameNode, MoveQuality(
                                move, score.score() - prevScore.score(), bestMove, sanMove, sanBestMove))])
                        elif prevScore.is_mate() != score.is_mate():
                            nodeToMoveQualityMap.update([
                                (gameNode, MoveQuality(move, -100, bestMove, sanMove, sanBestMove))])
                        elif prevScore.is_mate() and score.is_mate():
                            if prevScore.mate() <= score.mate():
                                nodeToMoveQualityMap.update([
                                    (gameNode, MoveQuality(move, -0.5, bestMove, sanMove, sanBestMove))])
                            if prevScore.mate() > score.mate():
                                nodeToMoveQualityMap.update([
                                    (gameNode, MoveQuality(move, 0, bestMove, sanMove, sanBestMove))])
                        else:
                            raise exception("tout cassé")
            gameNode = gameNode.next()
            color = not color
            evalPrev = evalList[i][1]
        return nodeToMoveQualityMap

    def run(self):
        self.running = True
        evalList = self.analyseGame(self.game.game())
        moveQuality = self.analyseMoves(evalList)
        self.controller.postAnalysis(self.game.game(), moveQuality)
        self.running = False

    def stop(self):
        self.stopFlag = True
        if self.wrapper is not None:
            self.wrapper.stop()
