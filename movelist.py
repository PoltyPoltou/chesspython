import chess
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty

def loadNode(instance, value):
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
    gameStr = ""

    def update_moves(self, controller):
        if str(controller.game.game()) == self.gameStr:
            for child in self.gridLayoutRef.children:
                child.bold = child.node == controller.game
            return
        self.gameStr =str(controller.game.game())
        curGame = controller.game.game().next()
        index = len(self.gridLayoutRef.children)-1
        prevBoard = controller.game.game().board()
        while curGame is not None:
            board = curGame.board()
            # skip move count when playing white
            if prevBoard.turn == chess.WHITE:
                index -= 1
            if(index < 0):
                # add move when not enough chidlren
                self.add_move(curGame, controller)
                index += 2 if prevBoard.turn == chess.WHITE else 1
            elif self.gridLayoutRef.children[index].node != curGame:
                # otherwise update directly the widget
                self.gridLayoutRef.children[index].node = curGame
                san = prevBoard.san(curGame.move)
                self.gridLayoutRef.children[index].text = "[ref=move]"+san+"[ref=move]"
            # check boldness
            self.gridLayoutRef.children[index].bold = self.gridLayoutRef.children[index].node == controller.game
            index -= 1
            curGame = curGame.next()
            prevBoard = board
        # remove all unused indexes
        while index > -1:
            self.remove_move()
            index -= 1

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
        moveWidget.bind(on_ref_press=loadNode)
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
