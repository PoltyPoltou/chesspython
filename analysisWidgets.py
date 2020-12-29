from typing import Optional
import chess
import analysis
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import *


class EvaluationBar(Widget):
    bgColor = ObjectProperty((0, 0, 0))
    barColor = ObjectProperty((0, 0, 0))
    eval = NumericProperty(0.00)
    textEval = StringProperty(0.00)
    pov = StringProperty("WHITE")
    sign = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.evalThread = None
        super().__init__(**kwargs)

    def start(self, board):
        self.evalThread = analysis.BoardAnalysisWrapper(board)
        self.evalThread.start()
        self.evalEvent = Clock.schedule_interval(self.checkEval, 1/120)

    def stop(self):
        if(self.evalThread != None):
            self.evalEvent.cancel()
            self.evalThread.stopThread()
            self.evalThread = None

    def parseEval(self, engineEval: chess.engine.Score):
        if(engineEval.score() is not None):
            eval = engineEval.score() / 100
            textEval = str(eval)
            if(eval > 10):
                eval = 10
            if(eval < -10):
                eval = -10
        elif(engineEval.score() == chess.engine.MateGiven):
            eval = 10
            textEval = "1-0"
        elif(engineEval.score() == -chess.engine.MateGiven):
            eval = -10
            textEval = "0-1"
        else:
            sign = abs(engineEval.mate())/engineEval.mate()
            lst = {-1: "-", 1: "+"}
            eval = sign * 10
            textEval = lst[sign] + "M" + str(abs(engineEval.mate()))
        return (eval, textEval)

    def checkEval(self, dt):
        if(self.evalThread.hasAnalysis()):
            povScore: chess.engine.PovScore = self.evalThread.getEngineAnalysis()[
                "score"]
            self.eval, self.textEval = self.parseEval(
                povScore.pov(chess.WHITE))
        pass

    pass
