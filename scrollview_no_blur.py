import kivy.uix.widget
import kivy.uix.scrollview
import time
from kivy.properties import ObjectProperty
from kivy.base import Builder
Builder.load_file("./kv/scrollview_no_blur.kv")


class BetterScrollView(kivy.uix.widget.Widget):
    real_scroll_widget: kivy.uix.scrollview.ScrollView = ObjectProperty()

    def add_widget(self, widget, index=0, canvas=None):
        if(self.real_scroll_widget is None):
            return super().add_widget(widget, index, canvas)
        else:
            return self.real_scroll_widget.add_widget(widget, index)

    pass
