import digitalio
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
    def __init__(self, name, mask, level=False, handler=None):
        self.name = name
        self.mask = mask
        self.level = level
        self.handler = handler


class ButtonStateMachine:
    def __init__(self, buttons, ordered_button_names):
        self._buttons = buttons
        self._button_states = {}
        self._init_button_state(ordered_button_names)

    def set_handler(self, name, handler):
        """Set the handler for the given button name"""
        self._button_states[name].handler = handler

    def _init_button_state(self, ordered_button_names):
        for idx, button_name in enumerate(ordered_button_names):
            mask = 1 << idx
            self._button_states[button_name] = ButtonState(name=button_name, mask=mask,)

    def service(self):
        pressed = self._buttons.get_pressed()
        for name, state in self._button_states.items():
            button_mask = state.mask
            is_pressed = (button_mask & pressed) > 0
            # was low and now is high
            if is_pressed and not state.level:
                self._button_states[name].level = is_pressed
                if state.handler:
                    state.handler(state)
            elif not is_pressed and state.level:
                self._button_states[name].level = is_pressed


if __name__ == "__main__":
    from screen_sm import ScreenStateMachine

    buttons = GamePadShift(
        digitalio.DigitalInOut(board.BUTTON_CLOCK),
        digitalio.DigitalInOut(board.BUTTON_OUT),
        digitalio.DigitalInOut(board.BUTTON_LATCH),
    )

    button_names = ["b", "a", "start", "select", "right", "down", "up", "left"]
    tester = ButtonStateMachine(buttons, button_names)
    screen_machine = ScreenStateMachine(board.DISPLAY)
    tester.set_handler("select", screen_machine.decr_backlight)
    tester.set_handler("start", screen_machine.incr_backlight)
    while True:
        tester.service()
        screen_machine.service()
        sleep(0.01)
