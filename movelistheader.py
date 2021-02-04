
from typing import Optional
from chess.pgn import GameNode
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
import analysis
from kivy.base import Builder
Builder.load_file("./kv/movelistheader.kv")


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
                if(self.moveQualityDict[gameNode].theoric):
                    self.txt = "[size=20][b][color=0066cc]" + \
                        self.moveQualityDict[gameNode].sanMove + \
                        "[/color][/b] was theoric[/size]"
                else:
                    strMove = "[b][color=" + \
                        self.moveQualityDict[gameNode].getHexColor(
                        )+"]"+self.moveQualityDict[gameNode].sanMove+"[/color][/b] was "+str(self.moveQualityDict[gameNode])
                    self.txt = "[size=20][b][color=30a090]" + \
                        self.moveQualityDict[gameNode].sanBestMove + \
                        "[/color][/b] was best \n" + strMove * (
                            self.moveQualityDict[gameNode].sanMove != self.moveQualityDict[gameNode].sanBestMove)+"[/size]"
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
