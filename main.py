from kivy.app import App
import analysisWidgets
import movelist
import chess
import chesswindow
from kivy.base import Builder
from kivy.core.window import Window
import game_and_analysis_serialisation as serialisationWrapper
from kivy.config import Config


class MyChessApp(App):
    def build(self):
        return chesswindow.ChessWindow()

    def on_start(self):
        return super().on_start()

    def on_stop(self):
        self.stopThreads()
        serialisationWrapper.saveGamesToDisk(self.root.controller.savedGames)
        return super().on_stop()

    def stopThreads(self):
        if(self.root.boardGUI.hasEval()):
            self.root.boardGUI.stopEval()
        self.root.controller.evalWrapper.stop()
        for analysis in self.root.controller.listAnalysis:
            analysis.stop()


if __name__ == '__main__':
    Config.read("config.ini")
    Config.write()
    Window.size = (1024, 768)
    MyChessApp().run()
