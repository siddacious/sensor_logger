class ScreenStateMachine:
    def __init__(self, display=None):
        if display is None:
            try:
                from board import DISPLAY
            except ImportError as err:
                print("No display given or found")
                raise err
        self._display = display
        self._backlight = 0.4

    def incr_backlight(self, button_state):
        print("incr")
        self._backlight = min(self._backlight + 0.1, 1.0)

    def decr_backlight(self, button_state):
        print("decr")
        self._backlight = max(self._backlight - 0.1, 0.0)

    def service(self):
        self._display.brightness = self._backlight
