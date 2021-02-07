
from kivy.clock import Clock
from kivy.uix.label import Label
import movelist
from typing import Optional
from chess.pgn import GameNode
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, ColorProperty
import analysis
import chess
from analysisWidgets import parseEvalFromScore
from kivy.base import Builder
Builder.load_file("./kv/movelistheader.kv")


class ComputerVariationLabel(Label):
    pass


class ScoreLabel(ComputerVariationLabel):
    bgColor = ColorProperty()
    pass


class HeadMoveList(BoxLayout):
    txt = StringProperty("")

    threadEngine: Optional[analysis.BoardAnalysisWrapper] = ObjectProperty(
        None, rebind=True)

    def __init__(self, **kwargs):
        self.moveQualityDict: Optional[dict[GameNode,
                                            analysis.MoveQuality]] = None
        self.info = None
        self.gameNode = None
        self.computer_variation_widget: movelist.VariationStack = None
        super().__init__(**kwargs)
        self.redraw_trigger = Clock.create_trigger(
            self.redraw_engine_variation,
            interval=True,
            timeout=2)
        self.redraw_trigger()

    def on_threadEngine(self, instance, value):
        if(self.threadEngine is not None):
            self.threadEngine.addEvalEventListener(self)

    def on_updateGameNode(self, gameNode: GameNode):
        self.gameNode = gameNode
        if(self.moveQualityDict is not None):
            if(gameNode in self.moveQualityDict):
                if(self.moveQualityDict[gameNode].theoric):
                    self.txt = "[size=20][b][color=0066cc]" + \
                        self.moveQualityDict[gameNode].sanMove + \
                        "[/color][/b] was theoric[/size]"
                else:
                    strMove = "[b][color=" + self.moveQualityDict[gameNode].getHexColor(
                    ) + "]" + self.moveQualityDict[gameNode].sanMove + "[/color][/b] was " + str(self.moveQualityDict[gameNode])
                    self.txt = "[size=20][b][color=30a090]" + \
                        self.moveQualityDict[gameNode].sanBestMove + \
                        "[/color][/b] was best \n" + strMove * (
                            self.moveQualityDict[gameNode].sanMove != self.moveQualityDict[gameNode].sanBestMove) + "[/size]"
        pass

    def postAnalysis(self, moveQualityDict):
        self.moveQualityDict = moveQualityDict

    def newEngineEvalEvent(self):
        temp_dict = self.threadEngine.getEngineAnalysis()
        if("pv" in temp_dict and "time" in temp_dict and "score" in temp_dict):
            self.last_info_dict = temp_dict

    def redraw_engine_variation(self, dt):
        if(self.gameNode is not None and self.last_info_dict is not None and "pv" in self.last_info_dict and (self.info is None or self.last_info_dict["time"] != self.info["time"])):
            if(self.gameNode.board().is_legal(self.last_info_dict["pv"][0])):
                test_board = self.gameNode.board()
                legal_flag = True
                for move in self.last_info_dict["pv"]:
                    if(test_board.is_legal(move)):
                        test_board.push(move)
                    else:
                        legal_flag = False
                        break
                if(legal_flag):
                    self.info = self.last_info_dict
                    self.computer_variation_widget.clear_widgets()
                    sc, t = parseEvalFromScore(self.info["score"])
                    lbl = ScoreLabel(text=t)
                    lbl.color = (0, 0, 0, 1) if sc > 0 else (1, 1, 1, 1)
                    lbl.bgColor = (0, 0, 0) if sc < 0 else (1, 1, 1)
                    self.computer_variation_widget.add_widget(lbl)
                    txt = " : " + str((self.gameNode.ply() + 1) // 2) + "."
                    txt += " .. " * (self.gameNode.turn == chess.BLACK)
                    txt += self.gameNode.board().san(self.info["pv"][0]) + " "
                    self.computer_variation_widget.add_widget(
                        ComputerVariationLabel(text=txt))
                    board: chess.Board = self.gameNode.board()
                    board.push(self.info["pv"][0])
                    # we skip first move as it is different
                    for move in self.info["pv"][1:]:
                        if(board.turn == chess.WHITE):
                            txt = str(board.fullmove_number) + \
                                "." + board.san(move)
                        else:
                            txt = board.san(move)
                        txt += " "
                        self.computer_variation_widget.add_widget(
                            ComputerVariationLabel(text=txt))
                        board.push(move)


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
