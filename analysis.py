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
            while(not self.wrapper.board.is_game_over() and not self.stopFlag):
                boardCopy = self.wrapper.board.copy()
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
        self.evalThread = self.ThreadContinuousEvaluation(self)

    def start(self):
        self.evalThread.start()

    def hasAnalysis(self):
        return self.evalThread.infoMove != None

    def getEngineAnalysis(self):
        return self.evalThread.infoMove.copy()

    def bestMove(self):
        return self.evalThread.infoMove.get('pv')[0].copy()

    def bestVariant(self):
        return self.evalThread.infoMove.get('pv').copy()

    def depth(self):
        return self.evalThread.infoMove.get('depth')

    def setLimitDepth(self, depth: int):
        self.evalThread.limit = chess.engine.Limit(depth=depth)

    def stopThread(self):
        self.evalThread.stopFlag = True

    def hasFinished(self):
        return self.evalThread.finished


class ThreadGameAnalysis(threading.Thread):
    def __init__(self, game: chess.Board, pv=3, threads=3, limit=chess.engine.Limit(depth=18)):
        super().__init__(self)
        self.engine.configure({"threads": threads})
        self.threads = threads
        self.limit = limit
        self.moveStack = list(game.move_stack)
        self.root: chess.Board = game.root()
        self.analyseList: list[chess.engine.InfoDict] = []
        self.pv = pv
        self.setDaemon(True)

    def run(self):
        self.time = time.time()
        wrapper = BoardAnalysisWrapper(self.root)
        wrapper.start()
        for move in self.moveStack:
            self.root.push(move)
            while(not wrapper.hasFinished()):
                time.sleep(0.2)
            self.analyseList.append(wrapper.getEngineAnalysis())
            self.progress.set(100 * self.root.ply() / len(self.moveStack))
        self.time = time.time() - self.time
        self.engine.quit()
