"""
Sending data to Adafruit IO and receiving it.
"""
from random import randint
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import neopixel
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
import adafruit_bmp280
import adafruit_sht31d
import time
import analogio
def volts(analog_in):
    return 2*3.3*(analog_in.value/65535)
class SensorLogger:
    def __init__(self):
                # Get wifi details and more from a secrets.py file
        try:
            from secrets import secrets
            self._secrets = secrets
        except ImportError:
            raise RuntimeError("WiFi secrets are kept in secrets.py, please add them there!")
        try:
            from settings import settings
            self._settings = settings
        except ImportError:
            raise RuntimeError("Settings file settings.py missing")
        self._error_log_file = settings['error_log_filename']
        self._i2c = board.I2C()
        self._initialize_wifi()
        self._initialize_sensors()
        self._initialize_io()
        self.battery = analogio.AnalogIn(board.BATTERY)

    def _log_exceptions(func):
        # pylint:disable=protected-access
        def _decorator(self, *args, **kwargs):
            retval = None
            try:
                retval = func(self, *args, **kwargs)
                return retval
            except RuntimeError as e:
                err_str = "error in %s\n%s\n"%(func.__name__, e)
                if self._settings['log_errors_to_file']:
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
        except ImportError:
            print("WiFi secrets are kept in secrets.py, please add them there!")
            raise

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
        self._esp = adafruit_esp32spi.ESP_SPIcontrol(self._spi, esp32_cs, esp32_ready, esp32_reset)
        status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
        self.wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(self._esp, self._secrets, status_light)

    @_log_exceptions
    def _initialize_io(self):
        aio_username = self._secrets["aio_username"]
        aio_key = self._secrets["aio_key"]

        # Create an instance of the Adafruit IO HTTP client
        self.io = IO_HTTP(aio_username, aio_key, self.wifi)
        self._initialize_feeds()

    def _initialize_feeds(self):
        self.temperature_feed = self.io.get_feed("temperature")
        self.humidity_feed = self.io.get_feed("humidity")
        self.batt_volts_feed = self.io.get_feed("batt_volts")



    @_log_exceptions
    def _initialize_sensors(self):
        # Create library object using our Bus I2C port
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(self._i2c)

        # change this to match the location's pressure (hPa) at sea level
        self.bmp280.sea_level_pressure = 1013.25
        self.bmp280.mode = adafruit_bmp280.MODE_NORMAL
        self.bmp280.standby_period = adafruit_bmp280.STANDBY_TC_500
        self.bmp280.iir_filter = adafruit_bmp280.IIR_FILTER_X16
        self.bmp280.overscan_pressure = adafruit_bmp280.OVERSCAN_X16
        self.bmp280.overscan_temperature = adafruit_bmp280.OVERSCAN_X2

        time.sleep(1)
        self.sht = adafruit_sht31d.SHT31D(self._i2c)

    @_log_exceptions
    def log_sensors(self):
        temp = self.bmp280.temperature
        hum = self.sht.relative_humidity
        bv = volts(self.battery)
        print("\033[1mBMP Tmemperature:\033[0m %0.3f ºC" % self.sht.temperature)
        print("\033[1mSHT Humidity:\033[0m %0.2f %%" % hum)
        print("\033[1mBattery Voltage:\033[0m %0.2f %%" % bv)
        # Retrieve data value from the feed
        self.io.send_data(self.temperature_feed["key"], temp)
        self.io.send_data(self.humidity_feed["key"], hum)
        self.io.send_data(self.batt_volts_feed["key"], bv)
        print("Data sent!")



last_write = time.monotonic()
logger = SensorLogger()
while True:
    if not (self.humidity_feed and self.temperature_feed and self.batt_volts_feed):
        self._initialize_feeds()
        continue
    if abs(time.monotonic()-last_write >15):
        last_write = time.monotonic()
        logger.log_sensors()
        print("took %d ns to send sensor data"%(time.monotonic()-write_start))