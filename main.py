from kivy.uix.boxlayout import BoxLayout
from colors import BACKGROUND
from kivy.app import App
from kivy.properties import ObjectProperty
import boardGUI
import analysisWidgets
import chess
from kivy.base import Builder
Builder.load_file("kv/app.kv")


class WindowLayout(BoxLayout):
    couleurBg = BACKGROUND
    boardGUI = ObjectProperty(None)
    pass


class MyChessApp(App):
    def build(self):
        return WindowLayout()

    def on_start(self):
        self.root.boardGUI.board = chess.Board()
        pass


if __name__ == '__main__':
    MyChessApp().run()
