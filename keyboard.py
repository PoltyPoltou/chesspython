from kivy.core.window import Window


class KeyboardListener():

    _bindings = {}

    def initKeyboard(self):
        Window.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, key=None, codepoint=None, text=None, modifiers=None, **kwargs):
        for f in self._bindings.get(text, []):
            f(key, modifiers)

    def bind_key(self, key, callback):
        '''
        key must be according to Keyboard.keycodes
        callback must be a function that support two arguments (keycode and modifiers)
        '''
        if(self._bindings.get(key, []) == []):
            dictTemp = {key: []}
            self._bindings.update(dictTemp)
        self._bindings[key].append(callback)
