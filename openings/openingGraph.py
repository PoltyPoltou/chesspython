from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from io import StringIO
from typing import Dict, Optional, Set, Tuple
import chess.pgn
import chess
from kivy.app import App
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.input.motionevent import MotionEvent
from kivy.graphics.transformation import Matrix
from kivy.properties import ColorProperty, ObjectProperty, NumericProperty, BooleanProperty, DictProperty, AliasProperty
Builder.load_file("kv/opening.kv")


class OpeningLabel(Label):
    instances = set()
    sizeFactor = NumericProperty()
    line_width = NumericProperty(1.5)

    has_variant = BooleanProperty(False)
    has_children = BooleanProperty(False)
    selected = BooleanProperty(False)

    box_width = NumericProperty()
    box_height = NumericProperty()

    box_left = NumericProperty()
    box_right = NumericProperty()
    box_bottom = NumericProperty()
    box_top = NumericProperty()
    top_node: chess.pgn.GameNode = ObjectProperty(rebind=True, allownone=True)
    bottom_node: chess.pgn.GameNode = ObjectProperty(
        rebind=True, allownone=True)
    actual_node: chess.pgn.GameNode = ObjectProperty(
        rebind=True, allownone=True)
    mapNodeToChild = DictProperty(rebind=True)
    parent_node = ObjectProperty(rebind=True)
    top_node_label = ObjectProperty(rebind=True, allownone=True)
    bottom_node_label = ObjectProperty(rebind=True, allownone=True)

    def __init__(self, gameNode, parent_node=None, **kwargs):
        self.heights = []
        self.mapNodeToChild = {}
        self.cache_y = 0
        self.callback_on_select = lambda x: None
        if(parent_node is not None):
            self.parent_node = parent_node
        self.actual_node = gameNode
        super().__init__(**kwargs)
        if(self.parent_node is not None and self.parent_node.parent is not None):
            self.parent_node.parent.add_widget(self)
        self.on_parent(self, self.parent)
        self.on_actual_node(self, self.actual_node, True)
        self.calculate_heights()
        OpeningLabel.instances.add(self)

    def set_y(self, _0=None, _1=None):
        self.y = ((self.mapNodeToChild[self.top_node].y + self.mapNodeToChild[self.bottom_node].y) / 2) if self.has_children else (
            self.parent_node.pos_child(self.actual_node) if self.parent_node is not None and self.actual_node is not None else 0)

    def on_parent(self, instance, value):
        if(self.parent is not None):
            for label in self.mapNodeToChild.values():
                self.parent.add_widget(label)

    def calculate_heights(self):
        if(self.actual_node.variations == []):
            self.heights = []
        else:
            self.heights = [self.mapNodeToChild[child_node].calculate_heights(
            ) for child_node in self.actual_node.variations]
        OpeningLabel.set_all_y_coord()
        return (1 if self.heights == [] else sum(self.heights))

    @staticmethod
    def set_all_y_coord():
        for label in OpeningLabel.instances:
            label.set_y()

    def pos_child(self, child_node):
        y_pos = 0
        index = self.actual_node.variations.index(child_node)
        if(self.parent_node is not None):
            y_pos += self.parent_node.pos_child(self.actual_node)
        if(index != 0):
            y_pos += sum(self.heights[:index])*self.height
        return y_pos

    def on_actual_node(self, instance=None, value=None, init=False):
        flag_updated = False
        for variation_node in self.actual_node.variations:
            if(variation_node not in self.mapNodeToChild):
                self.mapNodeToChild.update(
                    [(variation_node, OpeningLabel(variation_node, self))])
                flag_updated = True
        if(self.actual_node.variations != []):
            self.top_node = self.actual_node.variations[-1]
            self.bottom_node = self.actual_node.variations[0]
        if(flag_updated and not init):
            label_iter = self
            while(label_iter.parent_node is not None):
                label_iter = label_iter.parent_node
            label_iter.calculate_heights()

    def on_selected(self, instance, value):
        if(value):
            for label in OpeningLabel.instances:
                if(label is not instance):
                    label.selected = False

    def on_touch_up(self, touch: MotionEvent):
        if(touch.button == "left" and abs(touch.dx)+abs(touch.dy) == 0):
            rx, ry = self.to_window(touch.x, touch.y, False)
            if(self.parent.parent.collide_point(rx, ry)):
                t_x, t_y = touch.x + self.parent.x, touch.y + self.parent.y
                t_x -= self.parent.parent.center_x
                t_y -= self.parent.parent.center_y
                t_x, t_y = t_x/self.parent.getScalingFactor(), t_y/self.parent.getScalingFactor()
                t_x += self.parent.parent.center_x
                t_y += self.parent.parent.center_y
                t_x, t_y = t_x - self.parent.x, t_y - self.parent.y
                if(self.collide_point(t_x, t_y)):
                    self.selected = True
                    if(self.callback_on_select is not None):
                        self.callback_on_select(self.actual_node)
                    return True  # stop spreading in widget tree
        return super().on_touch_up(touch)


class OpeningNavigator(RelativeLayout):
    ZOOMPERSCROLL = 5  # represents a % detla
    scaling = NumericProperty(1)
    active = BooleanProperty(False)

    def __init__(self, callback_on_select=lambda x: None, **kw):
        self.callback_on_select = callback_on_select
        super().__init__(**kw)

    def add_widget(self, widget, index=0, canvas=None):
        if(isinstance(widget, OpeningLabel)):
            widget.callback_on_select = self.callback_on_select
        return super().add_widget(widget, index=index, canvas=canvas)

    def on_touch_move(self, touch: MotionEvent):
        if "button" in touch.profile:
            if(touch.button == 'left'):
                if("pos" in touch.profile and self.parent.collide_point(touch.x, touch.y)):
                    self.x += touch.dx / self.getScalingFactor()
                    self.y += touch.dy / self.getScalingFactor()
                    return True  # stop dispatching event through the widget tree
        return super().on_touch_move(touch)

    def on_touch_down(self, touch):
        if "button" in touch.profile:
            if(touch.button == "scrolldown" or touch.button == "scrollup"):
                if("pos" in touch.profile and self.parent.collide_point(touch.x, touch.y)):
                    sign = (touch.button == "scrolldown") - \
                        (touch.button == "scrollup")
                    if(self.scaling > OpeningNavigator.ZOOMPERSCROLL/100 or not touch.button == "scrollup"):
                        self.scaling = self.scaling + sign * OpeningNavigator.ZOOMPERSCROLL/100
        return super().on_touch_down(touch)

    def getScalingFactor(self):
        return self.scaling


class OpeningContainer(BoxLayout, StencilView):
    def __init__(self, game: chess.pgn.Game, callback_on_select, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.nav = OpeningNavigator(callback_on_select)
        self.nav.add_widget(OpeningLabel(game))
        self.add_widget(self.nav)

    def toggleactivate(self):
        self.nav.active = not self.nav.active

    def select_node(self, game: chess.pgn.GameNode):
        for child in self.nav.children:
            if(isinstance(child, OpeningLabel)):
                if(child.actual_node is game):
                    child.selected = True

    def find_node(self, game: chess.pgn.GameNode) -> OpeningLabel:
        for child in self.nav.children:
            if(isinstance(child, OpeningLabel)):
                if(child.actual_node is game):
                    return child

    def remove_node_and_children(self, game: chess.pgn.GameNode):
        label = self.find_node(game)
        if(label.parent_node is not None):
            if(label.parent_node.top_node is label.actual_node and label.parent_node.top_node is label.parent_node.bottom_node):
                label.parent_node.has_children = False
                label.parent_node.top_node = None
                label.parent_node.bottom_node = None
            else:
                label.parent_node.top_node = label.parent_node.actual_node.variations[-1]
                label.parent_node.bottom_node = label.parent_node.actual_node.variations[0]
                label.parent_node.has_variant = label.parent_node.top_node is not label.parent_node.bottom_node
            del label.parent_node.mapNodeToChild[label.actual_node]

        def remove_recursive_labels(openingLabel):
            openingLabel.parent.remove_widget(openingLabel)
            OpeningLabel.instances.remove(openingLabel)
            valuesList = list(openingLabel.mapNodeToChild.values())
            for child_label in valuesList:
                remove_recursive_labels(child_label)
        remove_recursive_labels(label)

    def actualize_node(self, game: chess.pgn.GameNode):
        for child in self.nav.children:
            if(isinstance(child, OpeningLabel)):
                if(child.actual_node is game):
                    child.on_actual_node()
                    break

    def actualize_graph(self, new_game: chess.pgn.Game):
        self.nav.clear_widgets()
        self.game = new_game
        OpeningLabel.instances = set()
        self.nav.add_widget(OpeningLabel(new_game))


if __name__ == "__main__":
    with open("./data/WHITE_opening.txt") as pgn:
        g = chess.pgn.read_game(pgn)
        app = App()
        app.root = FloatLayout()
        f = OpeningNavigator()
        app.root.add_widget(f)
        firstNode = OpeningLabel(g)
        f.add_widget(firstNode)
        app.run()
