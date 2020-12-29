import analysis
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty


class EvaluationBar(Widget):
    eval = NumericProperty(0.00)
    pov = StringProperty("WHITE")
    bgColor = ObjectProperty((0, 0, 0))
    pass
