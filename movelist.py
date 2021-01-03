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

def loadVariationNode(instance, value):
    if instance.mapNodes.get(value, None) is not None:
        instance.controller.updateCurrentNode(instance.mapNodes[value])

class MoveLabel(Label):
    moveColor = ObjectProperty(None)
    highlighted = BooleanProperty(None)

    def __init__(self, text, node, controller, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.node = node
        self.controller = controller

    def on_kv_post(self, base_widget):
        return super().on_kv_post(base_widget)
    pass

class VariationLabel(Label):
    mapNodes = {}
    old_y = NumericProperty(0)

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller

    def on_texture_size(self, instance, value):
        if self.parent is None:
            return
        self.parent.y += self.texture_size[1] - self.old_y
        print("self.old_y = ",self.old_y)
        print("self.y = ",self.texture_size[1])
        self.old_y = self.texture_size[1]

class MoveList(ScrollView):
    gridLayoutRef = ObjectProperty(None)
    textHeight = 20
    gameStr = ""
    listFullMoveEntry = []
    mapVariationPerEntry = {}

    def update_moves(self, controller):
        if str(controller.game.game()) == self.gameStr:
            for entry in self.listFullMoveEntry:
                for child in entry.children:
                    child.highlighted = child.node == controller.game
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
            fullmove_number = prevBoard.fullmove_number - 1
            if len(self.listFullMoveEntry) <= fullmove_number:
                self.addMainFullMoveEntry(fullmove_number, controller)
            entry = self.getFullMoveEntry(fullmove_number)

            index = 2 if prevBoard.turn == chess.WHITE else 3
            # create new move
            if len(entry.children) < index :
                self.add_move_in_entry(curGame, controller, entry)
            elif entry.children[-index].node != curGame:
                # otherwise update directly the widget
                entry.children[-index].node = curGame
                san = prevBoard.san(curGame.move)
                entry.children[-index].text = "[ref=move]"+san+"[ref=move]"
                entry.children[-index].moveColor = (0.75,0.75,0.75,1)
            # last entry is complete iif its black who has played
            lastEntryComplete = index == 3

            self.remove_all_variation(fullmove_number, lastEntryComplete)
            # Check for variation
            for variation in curGame.variations :
                # Only handle non mainline here
                if not variation.is_mainline():
                    self.add_variation(fullmove_number, lastEntryComplete, variation, controller)

            # check highlightedness
            entry.children[-index].highlighted = entry.children[-index].node == controller.game
            lastGame = curGame
            curGame = curGame.next()
            prevBoard = board

        # remove all unused indexes
        fullmove_number = prevBoard.fullmove_number
        while len(self.listFullMoveEntry) > fullmove_number:
            self.remove_move()

        # remove last entry black move if incomplete
        if not lastEntryComplete :
            entry = self.getFullMoveEntry(-1)
            if len(entry.children) > 2:
                entry.remove_widget(entry.children[0])

    def add_move_in_entry(self, gameNode, controller, entry):
        san = ""
        if gameNode is not None:
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
        self.gridLayoutRef.size = (0, self.gridLayoutRef.size[1]-self.textHeight)
        self.listFullMoveEntry.pop()

    def clearList(self):
        self.gridLayoutRef.clear_widgets()
        self.gridLayoutRef.size = (0, 0)
        self.listFullMoveEntry.clear()

    def postAnalysis(self, moveQualityList):
        full_move = -1
        index = 2
        color = chess.WHITE
        for quality in moveQualityList:
            # skip move count when playing white
            if index < len(self.listFullMoveEntry):

                if color == chess.WHITE:
                    full_move += 1
                    index = len(self.getFullMoveEntry(full_move).children) - 2

                label = self.getFullMoveEntry(full_move).children[index]
                if quality.isPerfect():
                    label.moveColor = (50/256, 161/256, 144/256,1)
                elif quality.isGood():
                    label.moveColor = (105/256, 163/256, 38/256,1)
                elif quality.isOk():
                    label.moveColor = (0.75,0.75,0.75,1)
                elif quality.isImprecision():
                    label.moveColor = (255/256, 213/256, 0,1)
                elif quality.isError():
                    label.moveColor = (214/256, 137/256, 4/256,1)
                elif quality.isBlunder():
                    label.moveColor = (105/256, 15/256, 12/256,1)

            index -= 1
            color = not color

    def addMainFullMoveEntry(self, fullMoveCount, controller):
        entry = GridLayout(cols=3, cols_minimum={0:30, 1:50, 2:50})
        entry.add_widget(MoveLabel(str(fullMoveCount+1) + ". ", None, None, markup=True))
        self.gridLayoutRef.add_widget(entry)
        self.gridLayoutRef.size = (0, self.gridLayoutRef.size[1]+self.textHeight)
        self.listFullMoveEntry.append(entry)
        self.add_move_in_entry(None, controller, entry)
        self.add_move_in_entry(None, controller, entry)
        return entry

    def remove_all_variation(self, fullmove_number, lastEntryComplete):
        varList = self.mapVariationPerEntry.get(str(fullmove_number)+("black" if lastEntryComplete else "white"), [])
        if varList is not None:
            for var in varList:
                self.gridLayoutRef.size = (0, self.gridLayoutRef.size[1]-var.size[1])
                self.gridLayoutRef.remove_widget(var)
        self.mapVariationPerEntry[str(fullmove_number)+("black" if lastEntryComplete else "white")] = None

    def add_variation(self, fullmove_number, lastEntryComplete, variation, controller):
        if self.mapVariationPerEntry[str(fullmove_number)+("black" if lastEntryComplete else "white")] is None:
            self.mapVariationPerEntry[str(fullmove_number)+("black" if lastEntryComplete else "white")] = []
        listVar = self.mapVariationPerEntry[str(fullmove_number)+("black" if lastEntryComplete else "white")]

        varLabel = VariationLabel(controller, markup=True, text_size=(self.size[0]-10, None))
        varLabel.bind(on_ref_press=loadVariationNode)

        curGame = variation
        prevBoard = curGame.parent.board()
        board = curGame.board()
        index = 0

        text = str(prevBoard.fullmove_number) + "." + (" ... " if not lastEntryComplete else " ")

        while curGame is not None:
            board = curGame.board()

            if prevBoard.turn == chess.WHITE and curGame != variation:
                text += str(prevBoard.fullmove_number) + ". "

            san = prevBoard.san(curGame.move)
            ref = str(index)
            text += "[ref="+ref+"]"+san+"[ref="+ref+"] "
            varLabel.mapNodes[ref] = curGame


            curGame = curGame.next()
            prevBoard = board
            index += 1

        varLabel.text = text
        varLabel.texture_update()

        widx = self.gridLayoutRef.children.index(self.getFullMoveEntry(fullmove_number))

        self.gridLayoutRef.add_widget(varLabel, widx)
        self.gridLayoutRef.size = (0, self.gridLayoutRef.size[1]+varLabel.texture_size[1])
        listVar.append(varLabel)


    def getFullMoveEntry(self, fullMoveCount):
        return self.listFullMoveEntry[fullMoveCount]
