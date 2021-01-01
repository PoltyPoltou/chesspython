from kivy.core.window import Window
from kivy.uix.widget import Widget


class MyKeyboardListener(Widget):

    def __init__(self, **kwargs):
        super(MyKeyboardListener, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._bindings = {}

    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def bind_key(self, textKey, callback):
        '''
        textKey is the text representing the key, char for simple keys
        see kivy.core.window.__init__.py in dict with keycode association
        '''
        if(self._bindings.get(textKey, []) == []):
            dictTemp = {textKey: []}
            self._bindings.update(dictTemp)
        self._bindings[textKey].append(callback)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)
        for f in self._bindings.get(keycode[1], []):
            f()
        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'escape':
            print("Keyboard released")
            keyboard.release()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True
