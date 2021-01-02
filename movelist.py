import chess
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty

def print_it(instance, value):
    if value == "move" and instance.node is not None and instance.controller is not None:
        instance.controller.updateCurrentNode(instance.node)

class MoveLabel(Label):
    def __init__(self, text, node, controller, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.node = node
        self.controller = controller

    def on_kv_post(self, base_widget):
        return super().on_kv_post(base_widget)
    pass

class MoveList(ScrollView):
    gridLayoutRef = ObjectProperty(None)
    textHeight = 20

    def add_move(self, gameNode, controller):
        board = gameNode.parent.board()
        color = board.turn
        move = gameNode.move
        san = board.san(move)
        fullMoveCount = board.fullmove_number

        if(color == chess.WHITE):
            self.gridLayoutRef.add_widget(
                MoveLabel(str(fullMoveCount) + ". ", None, controller, markup=True))
            self.gridLayoutRef.size = (
                0, self.gridLayoutRef.size[1]+self.textHeight)
        moveWidget = MoveLabel("[ref=move]"+san+"[ref=move]", gameNode, controller, markup=True)
        moveWidget.bind(on_ref_press=print_it)
        self.gridLayoutRef.add_widget(moveWidget)
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
