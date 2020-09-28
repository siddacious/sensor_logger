"""
Sending data to Adafruit IO and receiving it.
"""
from random import randint
import time
from collections import namedtuple

import analogio
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
import neopixel

from adafruit_bme680 import Adafruit_BME680_I2C as PHT_SENSOR

from gamepadshift import GamePadShift

import rtc

"""Simple test for using adafruit_motorkit with a DC motor"""
try:
    board.DISPLAY.brightness = 0.4
except AttributeError as attr:
    pass

i2c = board.I2C()

import rtc


def _curr_time_str():
    current_time = time.localtime()
    current_time.tm_hour
    current_time.tm_min
    current_time.tm_sec


# TODOS:
# get time from IO
# log errors to txt file
# show current tmp/hum in big nums
# auto dim after delay
# show RSSI on screen
# unblock requests
# send
# block on _wait_for_ready to verify ready pin is high
# def _wait_response_cmd(self, cmd, num_responses=None, *, param_len_16=False):
# def _wait_response_cmd(self, cmd, num_responses=None, *, param_len_16=False):

####################
def volts(analog_in):
    return 2 * 3.3 * (analog_in.value / 65535)


class SensorLogger:
    def __init__(self, i2c_bus=None):
        # Get wifi details and more from a secrets.py file
        try:
            from secrets import secrets

            self._secrets = secrets
        except ImportError:
            raise RuntimeError(
                "WiFi secrets are kept in secrets.py, please add them there!"
            )
        try:
            from settings import settings

            self._settings = settings
        except ImportError:
            raise RuntimeError("Settings file settings.py missing")
        if i2c_bus:
            self._i2c = i2c_bus
        else:
            self._i2c = board.I2C()
        self._error_log_file = settings["error_log_filename"]
        self.io = None
        self._initialize_wifi()
        self._initialize_sensors()
        self._initialize_io()
        # self.battery = analogio.AnalogIn(board.BATTERY)
        self.temperature_feed = None
        self.humidity_feed = None
        self.batt_volts_feed = None

    def _log_exceptions(func):
        # pylint:disable=protected-access
        def _decorator(self, *args, **kwargs):
            retval = None
            try:
                retval = func(self, *args, **kwargs)
                return retval
            except Exception as e:
                err_str = "ERROR in %s\n%s\n" % (func.__name__, e)
                if self._settings["log_errors_to_file"]:
                    import storage

                    storage.remount("/", False)
                    with open(self._error_log_file, "a") as err_log:
                        err_log.write(err_str)
                    storage.remount("/", True)
                print(err_str)

            return retval

        return _decorator

    def _initialize_wifi(self):

        # Get wifi details and more from a secrets.py file
        try:
            from secrets import secrets

            self._secrets = secrets
        except ImportError as e:
            print("WiFi secrets are kept in secrets.py, please add them there!")
            raise e from None

        # ESP32 Setup
        try:
            esp32_cs = DigitalInOut(board.D13)
            esp32_ready = DigitalInOut(board.D11)
            esp32_reset = DigitalInOut(board.D12)
        except AttributeError:
            esp32_cs = DigitalInOut(board.D9)
            esp32_ready = DigitalInOut(board.D10)
            esp32_reset = DigitalInOut(board.D5)

        self._spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self._esp = adafruit_esp32spi.ESP_SPIcontrol(
            self._spi, esp32_cs, esp32_ready, esp32_reset, service_function=self.service
        )
        status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
        self.wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(
            self._esp, self._secrets, status_light
        )

    def service(self):
        button_machine.service()
        screen_machine.service()

    @_log_exceptions
    def _initialize_io(self):
        aio_username = self._secrets["aio_username"]
        aio_key = self._secrets["aio_key"]

        # Create an instance of the Adafruit IO HTTP client
        self.io = IO_HTTP(aio_username, aio_key, self.wifi)
        clock = rtc.RTC()
        clock.datetime = self.io.receive_time()
        self._initialize_feeds()

    @_log_exceptions
    def _initialize_feeds(self):
        self.temperature_feed = self.io.get_feed("temperature")
        self.humidity_feed = self.io.get_feed("humidity")
        # self.batt_volts_feed = self.io.get_feed("batt-volts")

    @_log_exceptions
    def _initialize_sensors(self):
        if not self.io:
            self._initialize_io
        self.temp_sensor = PHT_SENSOR(self._i2c)
        self.humidity_sensor = self.temp_sensor

    @_log_exceptions
    def log_sensors(self):
        print("verifying feeds")
        if not (self.humidity_feed and self.temperature_feed):
            self._initialize_feeds()
        temp = self.temp_sensor.temperature
        hum = self.humidity_sensor.humidity

        print(
            "\033[1mBMP Tmemperature:\033[0m %0.3f k ºC"
            % self.humidity_sensor.temperature
        )
        print("\033[1mSHT Humidity:\033[0m %0.2f %%" % hum)

        self.io.send_data(self.temperature_feed["key"], temp)
        self.io.send_data(self.humidity_feed["key"], hum)

        print("Data sent!")


if __name__ == "__main__":
    from button_sm import ButtonStateMachine
    from screen_sm import ScreenStateMachine

    buttons = GamePadShift(
        DigitalInOut(board.BUTTON_CLOCK),
        DigitalInOut(board.BUTTON_OUT),
        DigitalInOut(board.BUTTON_LATCH),
    )

    button_names = ["b", "a", "start", "select", "right", "down", "up", "left"]
    button_machine = ButtonStateMachine(buttons, button_names)
    screen_machine = ScreenStateMachine(board.DISPLAY)
    button_machine.set_handler("select", screen_machine.decr_backlight)
    button_machine.set_handler("start", screen_machine.incr_backlight)

    last_write = time.monotonic()
    logger = SensorLogger(i2c_bus=i2c)
    while True:

        logger.service()
        if abs(time.monotonic() - last_write > 15):
            last_write = time.monotonic()
            logger.log_sensors()
            print(
                "took %d seconds to send sensor data" % (time.monotonic() - last_write)
            )
