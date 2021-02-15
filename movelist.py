from scrollview_no_blur import BetterScrollView
import chess
import chess.pgn
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty, ListProperty
from kivy.base import Builder
Builder.load_file("./kv/movelist.kv")


def loadNode(self, touch):
    if self.node is not None and self.controller is not None and self.collide_point(
            touch.pos[0], touch.pos[1]):
        self.controller.updateCurrentNode(self.node)


san_optimizer = {}
dict_optimizer = {}


def get_board(node: chess.pgn.GameNode) -> chess.Board():
    if(node in dict_optimizer):
        return dict_optimizer[node]
    else:
        iter_board = node.end().board()
        iter_node = node.end()
        while(iter_board.move_stack != [] and iter_node not in dict_optimizer and iter_node is not None):
            dict_optimizer.update([(iter_node, iter_board.copy())])
            move = iter_board.pop()
            if(iter_node is not None and move is not None):
                san_optimizer.update([(iter_node, iter_board.san(move))])
            pass
            iter_node = iter_node.parent
        if(isinstance(node, chess.pgn.Game)):
            dict_optimizer.update([(node, node.board())])
        else:
            prev_board = get_board(node.parent)
            board: chess.Board = prev_board.copy()
            board.push(node.move)
            dict_optimizer.update([(node, node.board())])
        return dict_optimizer[node]


def get_san(node: chess.pgn.ChildNode) -> str:
    if(node in san_optimizer):
        return san_optimizer[node]
    else:
        # trick to generate san as we define it when we want the relevant board
        get_board(node)
        return san_optimizer[node]
    pass


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


class GridLayoutMinHeight(GridLayout):
    pass

class VariationStack(StackLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MoveList(BetterScrollView):
    gridLayoutRef = ObjectProperty(None)
    # WARNING THIS IS HORRIBLE CODE
    # if the old coord is the same as the new but rounded we don't care and we do not update
    # on the actualisation of the variable we set it to be integer
    x = NumericProperty(0, comparator=lambda oldValue,
                        newValue: oldValue == int(newValue))
    y = NumericProperty(0, comparator=lambda oldValue,
                        newValue: oldValue == int(newValue))

    def on_kv_post(self, base_widget):
        self.scroll_wheel_distance *= 3
        return super().on_kv_post(base_widget)

    def on_x(self, instance, x):
        self.x = int(x)

    def on_y(self, instance, y):
        self.y = int(y)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()

    def reset(self):
        self.game = None
        self.listFullMoveEntry = []
        self.mapVariationPerEntry = {}
        self.mapMove = {}
        self.mapVariation = {}
        self.oldMove = None

    def addFullVariation(self, gameNode, controller):
        curGame = gameNode
        while(curGame is not None):
            self.new_move(curGame, controller)
            if curGame is not gameNode:
                for variation in curGame.variations:
                    if curGame.next() is not variation:
                        self.addFullVariation(variation, controller)
            curGame = curGame.next()

    def update_moves(self, controller):
        self.reset()
        self.clearList()
        self.game = controller.game.game()

        curGame = self.game
        while(curGame is not None):
            self.new_move(curGame, controller)
            for variation in curGame.variations[1:]:
                self.addFullVariation(variation, controller)
            curGame = curGame.next()

    def new_move(self, gameNode: chess.pgn.GameNode, controller):
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

                color = not gameNode.turn()
                fullmove_number = (gameNode.ply()) // 2 + 1
                fullMoveCount = fullmove_number - \
                    1 if color == chess.WHITE else fullmove_number - 2

                if color == chess.WHITE:
                    # add entry
                    self.addMainFullMoveEntry(fullMoveCount, controller)
                entry = self.getFullMoveEntry(fullMoveCount)
                self.add_move_in_entry(gameNode, controller, entry)
            # else
            else:
                # find variation from parent
                variation = self.mapVariation.get(gameNode.parent, None)

                color = not gameNode.turn()
                fullmove_number = (gameNode.ply()) // 2 + 1
                fullMoveCount = fullmove_number - \
                    1 if color == chess.WHITE else fullmove_number - 2

                self.add_variation(
                    fullMoveCount,
                    color == chess.WHITE,
                    gameNode,
                    controller,
                    variation)

            if self.mapMove.get(gameNode, None) is not None:
                widget = self.mapMove[gameNode]

        # update highlight
        if self.oldMove is not None:
            self.oldMove.highlighted = False
        if widget is not None:
            self.oldMove = widget
            self.oldMove.highlighted = True

    def add_move_in_entry(
            self,
            gameNode: chess.pgn.GameNode,
            controller,
            entry):
        san = get_san(gameNode)

        moveWidget = MoveLabel(san, gameNode, controller)
        moveWidget.bind(on_touch_down=loadNode)
        entry.add_widget(moveWidget)
        self.mapMove[gameNode] = moveWidget
        return moveWidget

    def go_to_bottom(self):
        if(self.gridLayoutRef.height > self.height):
            self.scroll_y = 0

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
                label.moveColor = quality.getColor()

            index -= 1
            color = not color

    def addMainFullMoveEntry(self, fullMoveCount, controller):
        entry = GridLayoutMinHeight(
            cols=3)
        entry.add_widget(MoveLabel("   " + str(fullMoveCount + 1) +
                                   ". ", None, None))
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
            0, self.gridLayoutRef.size[1] - var.size[1])
        self.gridLayoutRef.remove_widget(var)

    def create_variation(self, variation, controller):
        box = VariationBox()
        stack = VariationStack()
        box.add_widget(stack)

        prevNode = variation.parent

        text = " " + str((prevNode.ply() + 1) // 2) + "." + (
            " ... " if prevNode.turn == chess.BLACK else " ") + get_san(variation)

        label = VariationLabel(text, variation, controller, markup=True)
        label.bind(on_touch_down=loadNode)
        stack.add_widget(label)

        self.mapMove[variation] = label
        self.mapVariation[variation] = box

        return box

    def add_variation(
            self,
            fullmove_number,
            lastEntryComplete,
            variation,
            controller,
            originVariation):

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
        if originVariation is not None and len(
                variation.parent.variations) == 1:
            stack = originVariation.children[-1]

            prevNode = variation.parent
            text = " "
            if prevNode.turn == chess.WHITE:
                text += str((prevNode.ply() + 1) // 2) + ". "

            text += get_san(variation)

            label = VariationLabel(text, variation, controller, markup=True)
            label.bind(on_touch_down=loadNode)
            lastLabel = stack.children[0]
            lastLabel.next = label
            label.prev = lastLabel
            stack.add_widget(label)

            self.mapMove[variation] = label
            self.mapVariation[variation] = originVariation

        if originVariation is not None and len(
                variation.parent.variations) > 1:
            stack = originVariation.children[-1]
            base = self.mapMove[variation.parent]
            base_next = base.next
            if base_next is not None:
                # break link in variation label
                base_next.prev = None
                base.next = None
                # remove all label in original variation
                while len(
                        stack.children) > 0 and stack.children[0] is not base:
                    stack.remove_widget(stack.children[0])
                # create old variation
                box = self.create_variation(base_next.node, controller)
                curLabel = base_next.next
                while curLabel is not None:
                    self.add_variation(
                        0, False, curLabel.node, controller, box)
                    curLabel = curLabel.next
                listBoxChildren = originVariation.children[:-1]
                listBoxChildren.reverse()
                for boxChild in listBoxChildren:
                    originVariation.remove_widget(boxChild)
                    box.add_widget(boxChild)
                originVariation.add_widget(box)

            # create new sub variation
            box = self.create_variation(variation, controller)
            originVariation.children[0].last = False
            originVariation.add_widget(box)

    def getFullMoveEntry(self, fullMoveCount):
        return self.listFullMoveEntry[fullMoveCount]
