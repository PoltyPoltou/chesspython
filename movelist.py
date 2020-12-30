import chess
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label


class MoveList(GridLayout):

    def add_move(self, color: chess.Color, san: str, fullMoveCount: int):
        if(color == chess.WHITE):
            self.add_widget(Label(text=str(fullMoveCount) + ". "))
        self.add_widget(Label(text=san))
    pass
