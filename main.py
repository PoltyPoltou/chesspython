from kivy.app import App
import analysisWidgets
import movelist
import chess
import chesswindow
from kivy.base import Builder
Builder.load_file("kv/app.kv")

class MyChessApp(App):
    def build(self):
        return chesswindow.ChessWindow()

    def on_start(self):
        return super().on_start()

    def on_stop(self):
        self.stopThreads()
        return super().on_stop()

    def stopThreads(self):
        if(self.root.boardGUI.hasEval()):
            self.root.boardGUI.stopEval()


if __name__ == '__main__':
    MyChessApp().run()
