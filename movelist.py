import chess
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty, ListProperty


def loadNode(self, touch):
    if self.node is not None and self.controller is not None and self.collide_point(touch.pos[0], touch.pos[1]):
        self.controller.updateCurrentNode(self.node)


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


class VariationLabel(MoveLabel):

    def __init__(self, text, node, controller, **kwargs):
        super().__init__(text, node, controller, **kwargs)
        self.next = None
        self.prev = None


class VariationBox(BoxLayout):
    last = BooleanProperty(True, rebind=True)

    def addSubVariation(self):
        varBox = VariationBox(padding=(10, 0, 0, 0))
        self.add_widget(varBox)
        return varBox


class VariationStack(StackLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MoveList(ScrollView):
    gridLayoutRef = ObjectProperty(None)
    # WARNING THIS IS HORRIBLE CODE
    # if the old coord is the same as the new but rounded we don't care and we do not update
    # on the actualisation of the variable we set it to be integer
    x = NumericProperty(0, comparator=lambda oldValue,
                        newValue: oldValue == int(newValue))
    y = NumericProperty(0, comparator=lambda oldValue,
                        newValue: oldValue == int(newValue))

    def on_x(self, instance, x):
        self.x = int(x)

    def on_y(self, instance, y):
        self.y = int(y)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()

    def reset(self):
        self.gameStr = ""
        self.game = None
        self.listFullMoveEntry = []
        self.mapVariationPerEntry = {}
        self.mapMove = {}
        self.mapVariation = {}
        self.oldMove = None

    def update_moves(self, controller):
        if str(controller.game.game()) == self.gameStr:
            for entry in self.listFullMoveEntry:
                for child in entry.children:
                    child.highlighted = child.node is controller.game
                    self.oldMove = child
            return

        self.reset()
        self.clearList()
        self.game = controller.game.game()
        self.gameStr = str(self.game)

        lastGame = self.game
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

            # create new move
            widget = self.add_move_in_entry(curGame, controller, entry)
            # last entry is complete iif its black who has played
            lastEntryComplete = prevBoard.turn == chess.BLACK

            self.remove_all_variation(fullmove_number, lastEntryComplete)
            # Check for variation
            for variation in curGame.variations:
                # Only handle non mainline here
                if not variation.is_mainline():
                    self.add_variation(
                        fullmove_number, lastEntryComplete, variation, controller, None)

            # check highlightedness
            widget.highlighted = widget.node is controller.game
            if widget.highlighted:
                self.oldMove = widget
            lastGame = curGame
            curGame = curGame.next()
            prevBoard = board

        # remove all unused indexes
        fullmove_number = prevBoard.fullmove_number
        while len(self.listFullMoveEntry) > fullmove_number:
            self.remove_move()

        # remove last entry black move if incomplete
        if not lastEntryComplete:
            entry = self.getFullMoveEntry(-1)
            if len(entry.children) > 2:
                entry.remove_widget(entry.children[0])

    def new_move(self, gameNode, controller):
        # if game is completely different we update every move
        if self.game is None or self.game.game() is not gameNode.game():
            self.update_moves(controller)
            return

        if gameNode is gameNode.game():
            return

        widget = self.mapMove.get(gameNode, None)

        # check if game node is not already registered
        if widget is None:
            # Otherwise we need to add it
            # check if mainline
            if gameNode.is_mainline():

                board = gameNode.board()
                color = not board.turn
                fullMoveCount = board.fullmove_number - \
                    1 if color == chess.WHITE else board.fullmove_number - 2

                if color == chess.WHITE:
                    # add entry
                    self.addMainFullMoveEntry(fullMoveCount, controller)
                entry = self.getFullMoveEntry(fullMoveCount)
                self.add_move_in_entry(gameNode, controller, entry)
            # else
            else:
                # find variation from parent
                variation = self.mapVariation.get(gameNode.parent, None)

                board = gameNode.board()
                color = not board.turn
                fullMoveCount = board.fullmove_number - \
                    1 if color == chess.WHITE else board.fullmove_number - 2

                self.add_variation(fullMoveCount, color ==
                                   chess.WHITE, gameNode, controller, variation)

            if self.mapMove.get(gameNode, None) is not None:
                widget = self.mapMove[gameNode]

        # update highlight
        if self.oldMove is not None:
            self.oldMove.highlighted = False
        if widget is not None:
            self.oldMove = widget
            self.oldMove.highlighted = True

    def add_move_in_entry(self, gameNode, controller, entry):
        san = ""
        if gameNode is not None:
            board = gameNode.parent.board()
            move = gameNode.move
            san = board.san(move)

        moveWidget = MoveLabel(san, gameNode, controller, markup=True)
        moveWidget.bind(on_touch_down=loadNode)
        entry.add_widget(moveWidget)
        if(self.gridLayoutRef.height > self.height):
            self.scroll_y = 0
        self.mapMove[gameNode] = moveWidget
        return moveWidget

    def remove_move(self):
        self.gridLayoutRef.remove_widget(self.gridLayoutRef.children[0])
        self.listFullMoveEntry.pop()

    def clearList(self):
        self.gridLayoutRef.clear_widgets()
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
                    label.moveColor = (50/256, 161/256, 144/256, 1)
                elif quality.isGood():
                    label.moveColor = (105/256, 163/256, 38/256, 1)
                elif quality.isOk():
                    label.moveColor = (0.75, 0.75, 0.75, 1)
                elif quality.isImprecision():
                    label.moveColor = (255/256, 213/256, 0, 1)
                elif quality.isError():
                    label.moveColor = (214/256, 137/256, 4/256, 1)
                elif quality.isBlunder():
                    label.moveColor = (105/256, 15/256, 12/256, 1)

            index -= 1
            color = not color

    def addMainFullMoveEntry(self, fullMoveCount, controller):
        entry = GridLayoutMinHeight(
            cols=3)
        entry.add_widget(MoveLabel(str(fullMoveCount+1) +
                                   ". ", None, None, markup=True))
        self.gridLayoutRef.add_widget(entry)
        self.listFullMoveEntry.append(entry)
        return entry

    def remove_all_variation(self, fullmove_number, lastEntryComplete):
        variationKey = str(fullmove_number) + \
            ("black" if lastEntryComplete else "white")
        varList = self.mapVariationPerEntry.get(variationKey, [])
        if varList is not None:
            for var in varList:
                self.remove_variation(var)
        self.mapVariationPerEntry[variationKey] = None

    def remove_variation(self, var):
        self.gridLayoutRef.size = (
            0, self.gridLayoutRef.size[1]-var.size[1])
        self.gridLayoutRef.remove_widget(var)

    def create_variation(self, variation, controller):
        box = VariationBox()
        stack = VariationStack()
        box.add_widget(stack)

        prevBoard = variation.parent.board()

        text = str(prevBoard.fullmove_number) + "." + (" ... " if prevBoard.turn == chess.BLACK else " ") + \
            prevBoard.san(variation.move)

        label = VariationLabel(text, variation, controller, markup=True)
        label.bind(on_touch_down=loadNode)
        stack.add_widget(label)

        self.mapMove[variation] = label
        self.mapVariation[variation] = box

        return box

    def add_variation(self, fullmove_number, lastEntryComplete, variation, controller, originVariation):

        # start of variation from mainline
        if originVariation is None and variation.parent.is_mainline():
            box = self.create_variation(variation, controller)
            variationKey = str(fullmove_number) + \
                ("black" if lastEntryComplete else "white")

            if self.mapVariationPerEntry.get(variationKey, None) is None:
                self.mapVariationPerEntry[variationKey] = []

            listVar = self.mapVariationPerEntry[variationKey]

            if len(listVar) > 0:
                box.last = False
            listVar.append(box)

            widx = self.gridLayoutRef.children.index(
                self.getFullMoveEntry(fullmove_number))

            self.gridLayoutRef.add_widget(box, widx)

        # continue same variation than parent
        if originVariation is not None and len(variation.parent.variations) == 1:
            stack = originVariation.children[-1]

            prevBoard = variation.parent.board()

            text = " "
            if prevBoard.turn == chess.WHITE:
                text += str(prevBoard.fullmove_number) + ". "

            text += prevBoard.san(variation.move)

            label = VariationLabel(text, variation, controller, markup=True)
            label.bind(on_touch_down=loadNode)
            lastLabel = stack.children[0]
            lastLabel.next = label
            label.prev = lastLabel
            stack.add_widget(label)

            self.mapMove[variation] = label
            self.mapVariation[variation] = originVariation

        if originVariation is not None and len(variation.parent.variations) > 1:
            stack = originVariation.children[-1]
            base = self.mapMove[variation.parent]
            base_next = base.next
            if base_next is not None:
                # break link in variation label
                base_next.prev = None
                base.next = None
                # remove all label in original variation
                while len(stack.children) > 0 and stack.children[0] is not base:
                    stack.remove_widget(stack.children[0])
                # create old variation
                box = self.create_variation(base_next.node, controller)
                curLabel = base_next.next
                while curLabel is not None:
                    self.add_variation(
                        0, False, curLabel.node, controller, box)
                    curLabel = curLabel.next
                originVariation.add_widget(box)

            # create new sub variation
            box = self.create_variation(variation, controller)
            originVariation.children[0].last = False
            originVariation.add_widget(box)

    def getFullMoveEntry(self, fullMoveCount):
        return self.listFullMoveEntry[fullMoveCount]


class GridLayoutMinHeight(GridLayout):
    pass
