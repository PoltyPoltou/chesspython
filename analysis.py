import threading
import chess
import chess.engine
import time
import os


class BoardAnalysisWrapper():
    class ThreadContinuousEvaluation(threading.Thread):
        def __init__(self, wrapper):
            super().__init__()
            self.wrapper: BoardAnalysisWrapper = wrapper
            self.infoMove: chess.engine.InfoDict = None
            self.depth = 18
            self.stopFlag = False
            self.threads = 1
            self.setDaemon(True)
            self.finished = False
            print("Eval thread Launched")

        def run(self):
            while(not self.stopFlag):
                boardCopy = self.wrapper.board
                with self.wrapper.engine.analysis(boardCopy, chess.engine.Limit(self.depth), options={"threads": self.threads}) as analysis:
                    for info in analysis:
                        if(info.get('score') is not None):
                            self.infoMove = info
                        time.sleep(0.05)
                        if(self.stopFlag or self.wrapper.board.fen() != boardCopy.fen()):
                            break
                        self.finished = self.wrapper.board.fen() == boardCopy.fen()
                    # on dors si l'analyse est finie (limit atteinte)
                    while(not self.stopFlag and self.wrapper.board.fen() == boardCopy.fen()):
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
        if 'pv' in self._evalThread.infoMove:
            return self._evalThread.infoMove.get('pv')[0]
        return None

    def bestVariant(self):
        return self._evalThread.infoMove.get('pv').copy()

    def depth(self):
        return self._evalThread.infoMove.get('depth')

    def setLimitDepth(self, depth: int):
        self._evalThread.limit = chess.engine.Limit(depth=depth)

    def stop(self):
        self._evalThread.stopFlag = True

    def hasFinished(self):
        return self._evalThread.finished

class GameAnalysis(threading.Thread):
    class MoveQuality():
        def __init__(self, move, quality):
            self.move = move
            self.quality = quality

        def isPerfect(self):
            return self.quality >= 0

        def isGood(self):
            return self.quality >= -10 and self.quality < 0

        def isOk(self):
            return self.quality >= -25 and self.quality < -10

        def isImprecision(self):
            return self.quality >= -50 and self.quality < -25

        def isError(self):
            return self.quality >= -150 and self.quality < -50

        def isBlunder(self):
            return self.quality < -150

    def __init__(self):
        super().__init__()
        self.game = None

    def analyseGame(self, game : chess.pgn.Game):
        evalList = []
        curGame = game
        board = curGame.board()
        wrapper = BoardAnalysisWrapper(board)
        wrapper.start()
        while curGame is not None:
            wrapper.update(curGame.board())
            while not wrapper.hasFinished():
                time.sleep(0.1)
            if(wrapper.bestMove() is not None):
                evalList.append((curGame.move, wrapper.getEngineAnalysis()))
            curGame = curGame.next()
        wrapper.stop()
        return evalList

    def analyseMoves(self, evalList):
        moveQualityList = []
        evalPrev = None
        color = chess.BLACK
        for move, eval in evalList:
            if evalPrev is not None and move == evalPrev.get('pv')[0]:
                moveQualityList.append(GameAnalysis.MoveQuality(move, 0))
            elif evalPrev is not None:
                score = eval["score"].white() if color else eval["score"].black()
                prevScore = evalPrev["score"].white() if color else evalPrev["score"].black()
                if score.score() is not None and prevScore.score() is not None:
                    moveQualityList.append(GameAnalysis.MoveQuality(move, score.score() - prevScore.score()))
                elif prevScore.is_mate() != score.is_mate():
                    moveQualityList.append(GameAnalysis.MoveQuality(move, -100))
                elif prevScore.is_mate() and score.is_mate():
                    if prevScore.mate() <= score.mate():
                        moveQualityList.append(GameAnalysis.MoveQuality(move, -0.5))
                    if prevScore.mate() > score.mate():
                        moveQualityList.append(GameAnalysis.MoveQuality(move, 0))
            color = not color
            evalPrev = eval
        return moveQualityList

    def run(self):
        analysis = GameAnalysis()
        evalList = analysis.analyseGame(self.game.game())
        moveQuality = analysis.analyseMoves(evalList)
        for quality in moveQuality:
            print(quality.move," ", quality.quality)
