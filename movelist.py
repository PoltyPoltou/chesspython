import chess
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty


class MoveLabel(AnchorLayout):
    lbl_ref = ObjectProperty(None)

    def __init__(self, text, pos, **kwargs):
        super().__init__(**kwargs)
        self.lbl_ref.text = text
        self.anchor_x = pos

    def on_kv_post(self, base_widget):
        return super().on_kv_post(base_widget)
    pass


class MoveList(ScrollView):
    gridLayoutRef = ObjectProperty(None)
    textHeight = 20

    def add_move(self, color: chess.Color, san: str, fullMoveCount: int):
        if(color == chess.WHITE):
            self.gridLayoutRef.add_widget(
                MoveLabel(str(fullMoveCount) + ". ", "center"))
            self.gridLayoutRef.size = (
                0, self.gridLayoutRef.size[1]+self.textHeight)
        self.gridLayoutRef.add_widget(MoveLabel(san, "left"))
        if(self.gridLayoutRef.height > self.height):
            self.scroll_y = 0

    def remove_move(self):
        if(len(self.gridLayoutRef.children) % 3 == 2):
            self.gridLayoutRef.remove_widget(self.gridLayoutRef.children[0])
            self.gridLayoutRef.size = (
                0, self.gridLayoutRef.size[1]-self.textHeight)
        self.gridLayoutRef.remove_widget(self.gridLayoutRef.children[0])
    pass

    def clearList(self):
        self.gridLayoutRef.clear_widgets()
        self.gridLayoutRef.size = (0, 0)
