import math
from typing import Optional
import chess
from chess.pgn import Game, GameNode
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
import analysis
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, ColorProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, Line, Mesh, Triangle
from kivy.clock import *


class EvaluationBar(Widget):
    bgColor = ObjectProperty((0, 0, 0))
    barColor = ObjectProperty((0, 0, 0))
    displayedEval = NumericProperty(0.00)
    eval = NumericProperty(0.00)
    textEval = StringProperty(0.00)
    pov = StringProperty("WHITE")
    sign = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.evalWrapper: analysis.BoardAnalysisWrapper = None
        self.board = None
        self.started = False
        super().__init__(**kwargs)

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
            self.eval = 10*math.tanh(evalLinear/4)
        self.displayedEval = self.eval

    pass


class HeadMoveList(BoxLayout):
    txt = StringProperty("")

    def __init__(self, **kwargs):
        self.moveQualityDict: Optional[dict[GameNode,
                                            analysis.MoveQuality]] = None
        super().__init__(**kwargs)

    threadEngine: Optional[analysis.BoardAnalysisWrapper] = ObjectProperty(
        None, rebind=True)

    def on_threadEngine(self, instance, value):
        if(self.threadEngine is not None):
            self.threadEngine.addEvalEventListener(self)

    def on_updateGameNode(self, gameNode: GameNode):
        if(self.moveQualityDict is not None):
            if(gameNode in self.moveQualityDict):
                self.txt = "[size=20][b][color=30a090]" + \
                    self.moveQualityDict[gameNode].sanBestMove + \
                    "[/color][/b] was the best move [/size]"
        pass

    def postAnalysis(self, moveQualityDict):
        self.moveQualityDict = moveQualityDict

    def newEngineEvalEvent(self):
        pass


class DepthTracker(BoxLayout):
    threadEngine: Optional[analysis.BoardAnalysisWrapper] = ObjectProperty(
        None, rebind=True)
    actualDepth = NumericProperty(0)
    defaultDepth = NumericProperty(0)

    def newEngineEvalEvent(self):
        self.actualDepth = self.threadEngine.getDepth()
        self.defaultDepth = self.threadEngine.getDefaultDepth()
        pass

    def on_threadEngine(self, instance, value):
        if(self.threadEngine is not None):
            self.threadEngine.addEvalEventListener(self)
    pass


class AnalysisProgressBar(Widget):
    progress = NumericProperty(0.00)
    lastScore = 0
    lastPos = 0

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
            print("self.lastPos : ", self.lastPos)
            print("pos : ", pos)
            print("posToZero : ", posToZero)
            print("lastHeight : ", lastHeight)
            print("newHeight : ", newHeight)
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
