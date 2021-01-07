import threading
import chess
import chess.pgn
import chess.engine
import time
import os

from kivy.clock import Clock


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
        self.dispatcher = Clock.create_trigger(self.notifyListener)

    def update(self, board):
        self.board = board
        self._evalThread.finished = False

    def start(self):
        self._evalThread.start()

    def hasAnalysis(self):
        return self._evalThread.infoMove is not None

    def getEngineAnalysis(self):
        return self._evalThread.infoMove.copy()

    def bestMove(self):
        if 'pv' in self._evalThread.infoMove and len(self._evalThread.infoMove.get('pv')) > 0:
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
                "Listener added to ThreadContinuousEvaluation without newEngineEvalEvent(dt) attribute")


class GameAnalysis(threading.Thread):
    class MoveQuality():
        def __init__(self, move, quality):
            self.move = move
            self.quality = quality

        def isPerfect(self):
            return self.quality >= 0

        def isGood(self):
            return self.quality >= -20 and self.quality < 0

        def isOk(self):
            return self.quality >= -75 and self.quality < -20

        def isImprecision(self):
            return self.quality >= -150 and self.quality < -75

        def isError(self):
            return self.quality >= -400 and self.quality < -150

        def isBlunder(self):
            return self.quality < -400

        def __str__(self):
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

    def __init__(self, controller):
        super().__init__()
        self.game = None
        self.stopFlag = False
        self.wrapper = None
        self.controller = controller
        self.running = False

    def analyseGame(self, game: chess.pgn.Game):
        evalList = []
        curGame = game
        board = curGame.board()
        self.wrapper = BoardAnalysisWrapper(board)
        self.wrapper.start()
        size = curGame.end().board().fullmove_number*2
        progress = 0
        while curGame is not None and not self.stopFlag:
            self.wrapper.update(curGame.board())
            while not self.wrapper.hasFinished() and not self.stopFlag:
                time.sleep(0.1)
            if(self.wrapper.bestMove() is not None):
                evalList.append(
                    (curGame.move, self.wrapper.getEngineAnalysis()))
            curGame = curGame.next()
            progress += 1
            self.controller.progressBar.progress = progress/size
        self.controller.progressBar.progress = 1
        self.wrapper.stop()
        return evalList

    def analyseMoves(self, evalList):
        moveQualityList = []
        evalPrev = None
        color = chess.BLACK
        for move, eval in evalList:
            if evalPrev is not None and move == evalPrev.get('pv')[0]:
                moveQualityList.append(GameAnalysis.MoveQuality(move, 0))
            elif evalPrev is not None:
                score = eval["score"].white(
                ) if color else eval["score"].black()
                prevScore = evalPrev["score"].white(
                ) if color else evalPrev["score"].black()
                if score.score() is not None and prevScore.score() is not None:
                    moveQualityList.append(GameAnalysis.MoveQuality(
                        move, score.score() - prevScore.score()))
                elif prevScore.is_mate() != score.is_mate():
                    moveQualityList.append(
                        GameAnalysis.MoveQuality(move, -100))
                elif prevScore.is_mate() and score.is_mate():
                    if prevScore.mate() <= score.mate():
                        moveQualityList.append(
                            GameAnalysis.MoveQuality(move, -0.5))
                    if prevScore.mate() > score.mate():
                        moveQualityList.append(
                            GameAnalysis.MoveQuality(move, 0))
            color = not color
            evalPrev = eval
        return moveQualityList

    def run(self):
        self.running = True
        evalList = self.analyseGame(self.game.game())
        moveQuality = self.analyseMoves(evalList)
        for quality in moveQuality:
            print(quality.move, " ", quality)
        self.controller.postAnalysis(self.game.game(), moveQuality)
        self.running = False

    def stop(self):
        self.stopFlag = True
        if self.wrapper is not None:
            self.wrapper.stop()
