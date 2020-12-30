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
            self.limit: chess.engine.Limit = chess.engine.Limit(depth=30)
            self.restartAnalysis = False
            self.stopFlag = False
            self.threads = 1
            self.setDaemon(True)
            self.finished = False
            print("Eval thread Launched")

        def run(self):
            while(not self.stopFlag):
                boardCopy = self.wrapper.board
                with self.wrapper.engine.analysis(boardCopy, self.limit, options={"threads": self.threads}) as analysis:
                    self.finished = False
                    for info in analysis:
                        if(info.get('score') != None):
                            self.infoMove = info
                        time.sleep(0.05)
                        if(self.stopFlag or (self.restartAnalysis or self.wrapper.board.fen() != boardCopy.fen())):
                            self.restartAnalysis = False
                            break
                    # on dors si l'analyse est finie (limit atteinte)
                    while(not self.stopFlag and self.wrapper.board.fen() == boardCopy.fen()):
                        self.finished = True
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

    def start(self):
        self._evalThread.start()

    def hasAnalysis(self):
        return self._evalThread.infoMove != None

    def getEngineAnalysis(self):
        return self._evalThread.infoMove.copy()

    def bestMove(self):
        return self._evalThread.infoMove.get('pv')[0]

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
