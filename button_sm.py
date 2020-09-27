import digitalio
from gamepadshift import GamePadShift
import board
from time import sleep
import analogio

from collections import namedtuple
Buttons = namedtuple("Buttons", "b a start select right down up left")

# Button Constants
BUTTON_LEFT = const(128)
BUTTON_UP = const(64)
BUTTON_DOWN = const(32)
BUTTON_RIGHT = const(16)
BUTTON_SELECT = const(8)
BUTTON_START = const(4)
BUTTON_A = const(2)
BUTTON_B = const(1)
class ButtonState:
    def __init__ (self, name, mask, level=False, handler=None):
        self.name = name
        self.mask=mask
        self.level = level
        self.handler = handler
class ButtonStateMachine:
    def __init__(self):
        self._buttons = GamePadShift(
            digitalio.DigitalInOut(board.BUTTON_CLOCK),
            digitalio.DigitalInOut(board.BUTTON_OUT),
            digitalio.DigitalInOut(board.BUTTON_LATCH),
        )
        self._display = board.DISPLAY
        self._backlight = 0.4
        self._button_states = {}
        self._init_button_state()
        self.set_handler('select', self._decr_backlight)
        self.set_handler('start', self._incr_backlight)

    def set_handler(self, name, handler):
        """Set the handler for the given button name"""
        self._button_states[name].handler = handler

    def _init_button_state(self):
        for idx, button_name in enumerate(["b", "a", "start", "select", "right", "down", "up", "left"]):
            mask = 1<<idx
            self._button_states[button_name] = ButtonState(
                name=button_name,
                mask=mask,
            )
    def _incr_backlight(self, button_state):
        self._backlight = min(self._backlight + 0.1, 1.0)
    def _decr_backlight(self, button_state):
        self._backlight = max(self._backlight - 0.1, 0.0)

    def _service_buttons(self):
        pressed = self._buttons.get_pressed()
        for name, state in self._button_states.items():
            button_mask = state.mask
            is_pressed =  (button_mask & pressed) > 0
            # was low and now is high
            if is_pressed and not state.level:
                self._button_states[name].level = is_pressed
                if state.handler:
                    state.handler(state)
            elif not is_pressed and state.level:
                self._button_states[name].level = is_pressed
    def _service_screen(self):
        self._display.brightness = self._backlight


    def service(self):

        self._service_buttons()
        self._service_screen()

if __name__ == "__main__":
    tester = ButtonStateMachine()
    while True:
        tester.service()
        sleep(0.01)