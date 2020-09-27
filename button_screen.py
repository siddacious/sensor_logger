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
class ButtonTest:
    def __init__(self):
        self._buttons = GamePadShift(
            digitalio.DigitalInOut(board.BUTTON_CLOCK),
            digitalio.DigitalInOut(board.BUTTON_OUT),
            digitalio.DigitalInOut(board.BUTTON_LATCH),
        )
        self._display = board.DISPLAY
        self._backlight = 0.4
        self._button_states = {
            "a" : False,
            "b" : False,
            "down" : False,
            "left" : False,
            "right" : False,
            "select" : False,
            "start" : False,
            "up" : False,
        }

    def _service_buttons(self):
        button = Buttons(
            *[
                self._buttons.get_pressed() & button
                for button in (
                    BUTTON_B,
                    BUTTON_A,
                    BUTTON_START,
                    BUTTON_SELECT,
                    BUTTON_RIGHT,
                    BUTTON_DOWN,
                    BUTTON_UP,
                    BUTTON_LEFT,
                )
            ]
        )
        if button.up and not self._button_states["up"]:
            self._button_states["up"] = button.up
            print("UP")
        elif not button.up and self._button_states["up"]:
            self._button_states["up"] = button.up

        if button.down and not self._button_states["down"]:
            self._button_states["down"] = button.down
            print("DOWN")
        elif not button.down and self._button_states["down"]:
            self._button_states["down"] = button.down

        if button.left and not self._button_states["left"]:
            self._button_states["left"] = button.left
            print("LEFT")
        elif not button.left and self._button_states["left"]:
            self._button_states["left"] = button.left

        if button.right and not self._button_states["right"]:
            self._button_states["right"] = button.right
            print("RIGHT")
        elif not button.right and self._button_states["right"]:
            self._button_states["right"] = button.right

        if button.a and not self._button_states["a"]:
            self._button_states["a"] = button.a
            print("A")
        elif not button.a and self._button_states["a"]:
            self._button_states["a"] = button.a

        if button.b and not self._button_states["b"]:
            self._button_states["b"] = button.b
            print("B")
        elif not button.b and self._button_states["b"]:
            self._button_states["b"] = button.b

        if button.start and not self._button_states["start"]:
            self._button_states["start"] = button.start
            self._backlight += 0.2
            if self._backlight > 1.0:
                self._backlight = 1.0
        elif not button.start and self._button_states["start"]:
            self._button_states["start"] = button.start

        if button.select and not self._button_states["select"]:
            self._backlight -= 0.2
            if self._backlight < 0:
                self._backlight = 0.0
            self._button_states["select"] = button.select
        elif not button.select and self._button_states["select"]:
            self._button_states["select"] = button.select
            

    def service(self):

        print("backlight:", self._backlight)
        self._display.brightness = self._backlight
        self._service_buttons()
# time.sleep(1)
    # _buttons = GamePadShift(
    #     digitalio.DigitalInOut(board.BUTTON_CLOCK),
    #     digitalio.DigitalInOut(board.BUTTON_OUT),
    #     digitalio.DigitalInOut(board.BUTTON_LATCH),
    # )
    #####################

    # @property
    # def button(self):

    #     return
if __name__ == "__main__":
    tester = ButtonTest()
    while True:
        tester.service()
        sleep(0.01)