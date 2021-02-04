import math
from typing import Optional
import chess
import chess.engine
from chess.pgn import GameNode
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
import analysis
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, Mesh, Line
from kivy.clock import *
from kivy.base import Builder
Builder.load_file("./kv/analysis.kv")


def getHeight(instance, eval):
    return 0.5 * instance.height * \
        (1 + instance.sign * eval/10)


class EvaluationBar(Widget):
    bgColor = ObjectProperty((0, 0, 0))
    barColor = ObjectProperty((0, 0, 0))
    eval = NumericProperty()
    rectHeight = NumericProperty()
    textEval = StringProperty()
    pov = StringProperty("WHITE")
    sign = BooleanProperty()
    animRunning = BooleanProperty(False)
    animWidget = ObjectProperty(rebind=True)

    def __init__(self, **kwargs):
        self.evalWrapper: analysis.BoardAnalysisWrapper = None
        self.board = None
        self.started = False
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        return super().on_kv_post(base_widget)

    def isStarted(self):
        return self.evalWrapper is not None and self.started

    def start(self):
        if(self.evalWrapper is not None):
            self.started = True
            self.evalWrapper.addEvalEventListener(self)

    def stop(self):
        if(self.evalWrapper != None and self.started):
            self.evalWrapper = None
            self.started = False

    def update(self, board):
        self.board = board

    def parseEval(self, povScore: chess.engine.PovScore):
        engineEval = povScore.white()
        if(self.board != None and self.board.is_game_over(claim_draw=True)):
            textEval = self.board.result(claim_draw=True)
            if(povScore.is_mate()):
                eval = 10 if textEval == "1-0" else -10
            else:
                eval = 0
        elif(engineEval.score() is not None):
            eval = engineEval.score() / 100
            textEval = str(eval)
            if(eval > 10):
                eval = 10
            if(eval < -10):
                eval = -10
        elif(engineEval.mate() == 0 and povScore.turn == chess.WHITE):
            # Black won
            textEval = "0-1"
            eval = -10
            pass
        elif(engineEval.mate() == 0 and povScore.turn == chess.BLACK):
            # White won
            textEval = "1-0"
            eval = 10
            pass
        elif(povScore.is_mate()):
            if(engineEval.mate() > 0):
                eval = 10
                textEval = "+M" + str(abs(engineEval.mate()))
            else:
                eval = -10
                textEval = "-M" + str(abs(engineEval.mate()))

        return (eval, textEval)

    def newEngineEvalEvent(self):
        if(self.evalWrapper.hasAnalysis()):
            povScore: chess.engine.PovScore = self.evalWrapper.getEngineAnalysis()[
                "score"]
            evalLinear, self.textEval = self.parseEval(povScore)
            eval = 10*math.tanh(evalLinear/4)
            if(evalLinear > 10):
                eval = 10
            if(not self.animRunning):
                anim = Animation(
                    size=(10, getHeight(self, eval)), d=0.3, t="out_quad")
                anim.e = eval

                def endAnimation(a, w):
                    self.eval = a.e
                    self.animRunning = False

                anim.bind(on_complete=endAnimation)
                self.animRunning = True
                anim.start(self.animWidget)

    pass


class AnalysisProgressBar(Widget):
    progress = NumericProperty(0.00)

    def __init__(self, **kwargs):
        self.evalList = []
        self.lastScore = 0
        self.lastPos = 0
        self.reconstruct = False
        self.progressDelta = 0
        self.bind(size=lambda a1, a2: self.drawAllMeshes())
        super().__init__(**kwargs)

    def drawTriangles(self, lastPos, newPos, lastHeight, newHeight):
        trianglePts = []
        baseWhite = lastHeight >= 0.5 * self.height and newHeight >= 0.5 * self.height \
            and (lastHeight > 0.5 * self.height or newHeight > 0.5 * self.height)
        baseBlack = lastHeight <= 0.5 * self.height and newHeight <= 0.5 * self.height \
            and (lastHeight < 0.5 * self.height or newHeight < 0.5 * self.height)
        if baseWhite or baseBlack:
            refHeight = min(lastHeight, newHeight) if baseWhite else max(
                lastHeight, newHeight)
            biggestHeight = max(lastHeight, newHeight) if baseWhite else min(
                lastHeight, newHeight)

            refPos = lastPos if refHeight == lastHeight else newPos
            biggestPos = lastPos if biggestHeight == lastHeight else newPos

            trianglePts += [self.x + self.width*lastPos,
                            self.y + 0.5 * self.height, 0, 0,
                            self.x + self.width*lastPos,
                            self.y + refHeight, 0, 0,
                            self.x + self.width*newPos,
                            self.y + 0.5 * self.height, 0, 0,

                            self.x + self.width*lastPos,
                            self.y + refHeight, 0, 0,
                            self.x + self.width*newPos,
                            self.y + 0.5 * self.height, 0, 0,
                            self.x + self.width*newPos,
                            self.y + refHeight, 0, 0,

                            self.x + self.width*refPos,
                            self.y + refHeight, 0, 0,
                            self.x + self.width*biggestPos,
                            self.y + refHeight, 0, 0,
                            self.x + self.width*biggestPos,
                            self.y + biggestHeight, 0, 0
                            ]
        baseColor = 0.65 if baseWhite else 0.35

        with self.canvas:
            Color(baseColor, baseColor, baseColor)
            if len(trianglePts) > 0:
                Mesh(vertices=trianglePts, mode="triangles",
                     indices=range(int(len(trianglePts)/4)))

    def addEval(self, eval):
        if(not self.reconstruct):
            self.evalList.append(eval)
        score = eval["score"].white().score()
        if score is None and eval["score"].white().is_mate():
            score = eval["score"].white().moves * 1000
        pos = self.progress
        maxScale = 600
        lastHeight = min(max(self.lastScore, -maxScale), maxScale) / \
            (2*maxScale) * self.height + 0.5 * self.height
        newHeight = min(max(score, -maxScale), maxScale) / (2*maxScale) * \
            self.height + 0.5 * self.height

        alternate = lastHeight > 0.5 * self.height and newHeight < 0.5 * self.height \
            or lastHeight < 0.5 * self.height and newHeight > 0.5 * self.height
        if alternate:
            a = (newHeight - lastHeight) / (pos - self.lastPos)
            posToZero = self.lastPos - (lastHeight - 0.5 * self.height) / a
            self.drawTriangles(self.lastPos, posToZero,
                               lastHeight, 0.5 * self.height)
            self.drawTriangles(posToZero, pos, 0.5 * self.height, newHeight)
        else:
            self.drawTriangles(self.lastPos, pos, lastHeight, newHeight)

        with self.canvas:
            Color(1., 1., 1.)
            Line(points=[self.x + self.width*self.lastPos,
                         self.y + lastHeight, self.x + self.width*pos, self.y + newHeight])

        self.lastScore = score
        self.lastPos = pos
        self.progress += self.progressDelta

    def drawAllMeshes(self):
        self.resetBar()
        self.reconstruct = True
        for eval in self.evalList:
            self.addEval(eval)
        self.reconstruct = False

    def resetBar(self):
        self.lastScore = 0
        self.lastPos = 0
        self.progress = 0
        self.canvas.clear()

    def newEval(self):
        self.resetBar()
        self.progressDelta = 0
        self.evalList = []
