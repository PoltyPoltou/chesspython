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
                for childOfChild in child.children:
                    childOfChild.bold = childOfChild.node == controller.game
            return

        self.gameStr =str(controller.game.game())

        lastGame = controller.game.game()
        curGame = lastGame.next()
        prevBoard = lastGame.board()
        # Track if we need to delete the last entry black move
        lastEntryComplete = False
        while curGame is not None:
            board = curGame.board()
            # We need to get the full move number BEFORE the move was done
            fullmove_number = prevBoard.fullmove_number
            if len(self.gridLayoutRef.children) < fullmove_number:
                self.addMainFullMoveEntry(fullmove_number)
            entry = self.gridLayoutRef.children[-fullmove_number]

            index = 2 if prevBoard.turn == chess.WHITE else 3
            # create new move
            if len(entry.children) < index :
                self.add_move_in_entry(curGame, controller, entry)
            elif entry.children[-index].node != curGame:
                # otherwise update directly the widget
                entry.children[-index].node = curGame
                san = prevBoard.san(curGame.move)
                entry.children[-index].text = "[ref=move]"+san+"[ref=move]"
                entry.children[-index].color = (1,1,1,1)
            # last entry is complete iif its black who has played
            lastEntryComplete = index == 3

            # check boldness
            entry.children[-index].bold = entry.children[-index].node == controller.game
            lastGame = curGame
            curGame = curGame.next()
            prevBoard = board

        # remove all unused indexes
        fullmove_number = prevBoard.fullmove_number
        while len(self.gridLayoutRef.children) > fullmove_number:
            self.remove_move()

        # remove last entry black move if incomplete
        if not lastEntryComplete :
            entry = self.gridLayoutRef.children[0]
            if len(entry.children) > 2:
                entry.remove_widget(entry.children[0])

    def add_move(self, gameNode, controller):
        board = gameNode.parent.board()
        color = board.turn

        if(color == chess.WHITE):
            self.addMainFullMoveEntry(board.fullmove_number)
        entry = self.gridLayoutRef.children[0]
        self.add_move_in_entry(gameNode, controller, entry)


    def add_move_in_entry(self, gameNode, controller, entry):
        board = gameNode.parent.board()
        move = gameNode.move
        san = board.san(move)

        moveWidget = MoveLabel("[ref=move]"+san+"[ref=move]", gameNode, controller, markup=True)
        moveWidget.bind(on_ref_press=loadNode)
        entry.add_widget(moveWidget)
        if(self.gridLayoutRef.height > self.height):
            self.scroll_y = 0

    def remove_move(self):
        self.gridLayoutRef.remove_widget(self.gridLayoutRef.children[0])

    def clearList(self):
        self.gridLayoutRef.clear_widgets()
        self.gridLayoutRef.size = (0, 0)

    def postAnalysis(self, moveQualityList):
        full_move = len(self.gridLayoutRef.children)
        index = 2
        color = chess.WHITE
        for quality in moveQualityList:
            # skip move count when playing white
            if color == chess.WHITE:
                full_move -= 1
                index = len(self.gridLayoutRef.children[full_move].children) - 2
            if index >= 0:
                label = self.gridLayoutRef.children[full_move].children[index]
                if quality.isPerfect():
                    label.color = (50/256, 161/256, 144/256,1)
                elif quality.isGood():
                    label.color = (105/256, 163/256, 38/256,1)
                elif quality.isOk():
                    label.color = (1,1,1,1)
                elif quality.isImprecision():
                    label.color = (255/256, 213/256, 0,1)
                elif quality.isError():
                    label.color = (214/256, 137/256, 4/256,1)
                elif quality.isBlunder():
                    label.color = (105/256, 15/256, 12/256,1)
            index -= 1
            color = not color

    def addMainFullMoveEntry(self, fullMoveCount):
        entry = GridLayout(cols=3, cols_minimum={0:30, 1:50, 2:50})
        entry.add_widget(MoveLabel(str(fullMoveCount) + ". ", None, None, markup=True))
        self.gridLayoutRef.add_widget(entry)
        self.gridLayoutRef.size = (0, self.gridLayoutRef.size[1]+self.textHeight)
        return entry
