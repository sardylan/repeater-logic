import datetime
import logging
import threading
import time
from enum import Enum

from RPi import GPIO

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

rootLogger = logging.getLogger()
rootLogger.level = logging.WARN

fileHandler = logging.FileHandler("repeater.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

_logger = logging.getLogger(__name__)

PIN_RX_LOCAL = 11
PIN_TX_LOCAL = 13

PIN_RX_REMOTE = 16
PIN_TX_REMOTE = 18

TAIL_DURATION = 1000


class State(Enum):
    OFF = "Off"
    INIT = "Initialization"
    WAITING = "Waiting"
    RELAY_LOCAL = "Relaying local signal"
    RELAY_REMOTE = "Relaying remote signal"
    BEACON = "Sendind Beacon"
    DEINIT = "Deinitialization"


class Repeater:
    def __init__(self):
        self._thread_beacon_trigger = None

        self._state = State.OFF

        self._rx_local = False
        self._rx_remote = False

        self._tx_local = False
        self._tx_remote = False

        self._tx_local_off_start = False

        self._beacon_time = False

    def run(self):
        self._register_gpio()
        self._prepare_beacon_thread()

        self._state = State.INIT

        while True:
            self._loop()

            print("%s | Local: %s %s - Remote: %s %s - Beacon: %s - State: %s" % (
                datetime.datetime.now(),
                ">RX<" if GPIO.input(PIN_RX_LOCAL) == GPIO.LOW else " rx ",
                ">TX<" if GPIO.input(PIN_TX_LOCAL) == GPIO.HIGH else " tx ",
                ">RX<" if GPIO.input(PIN_RX_REMOTE) == GPIO.LOW else " rx ",
                ">TX<" if GPIO.input(PIN_TX_REMOTE) == GPIO.HIGH else " tx ",
                " BC " if self._beacon_time else " bc ",
                self._state
            ))

            time.sleep(.1)

    def _register_gpio(self):
        _logger.info("GPIO Configuration")

        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(channel=PIN_RX_LOCAL, direction=GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(channel=PIN_RX_REMOTE, direction=GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(channel=PIN_TX_LOCAL, direction=GPIO.OUT, pull_up_down=GPIO.PUD_OFF, initial=GPIO.LOW)
        GPIO.setup(channel=PIN_TX_REMOTE, direction=GPIO.OUT, pull_up_down=GPIO.PUD_OFF, initial=GPIO.LOW)

    def _prepare_beacon_thread(self):
        self._thread_beacon_trigger = threading.Thread(target=self._thread_beacon_loop)
        self._thread_beacon_trigger.daemon = True
        self._thread_beacon_trigger.start()

    def _thread_beacon_loop(self):
        while self._thread_beacon_trigger.is_alive():
            time.sleep(10)
            self._beacon_time = True

    def _loop(self):
        _logger.info("Running loop")

        self._read_rx_pin()
        self._compute_logic()
        self._parse_state()
        self._set_tx_pins()

    def _read_rx_pin(self):
        _logger.info("GPIO Configuration")

        self._rx_local = True if GPIO.input(PIN_RX_LOCAL) == GPIO.LOW else False
        self._rx_remote = True if GPIO.input(PIN_RX_REMOTE) == GPIO.LOW else False

    def _compute_logic(self):
        _logger.info("Computing logic")

        if self._state == State.OFF:
            pass

        elif self._state == State.INIT:
            self._state = State.WAITING

        elif self._state == State.WAITING:
            if self._beacon_time:
                self._state = State.BEACON
            else:
                if self._rx_local:
                    self._state = State.RELAY_LOCAL
                elif self._rx_remote:
                    self._state = State.RELAY_REMOTE

        elif self._state == State.RELAY_LOCAL:
            if not self._rx_local:
                self._state = State.WAITING

        elif self._state == State.RELAY_REMOTE:
            if not self._rx_remote:
                self._state = State.WAITING

        elif self._state == State.BEACON:
            if not self._beacon_time:
                self._state = State.WAITING

        elif self._state == State.DEINIT:
            self._state = State.OFF

    def _parse_state(self):
        _logger.info("Parsing new state")

        if self._state == State.OFF:
            self._tx_local = False
            self._tx_remote = False

        elif self._state == State.INIT:
            self._tx_local = False
            self._tx_remote = False

        elif self._state == State.WAITING:
            self._tx_local = False
            self._tx_remote = False

        elif self._state == State.RELAY_LOCAL:
            self._tx_local = True
            self._tx_remote = True

        elif self._state == State.RELAY_REMOTE:
            self._tx_local = True
            self._tx_remote = False

        elif self._state == State.BEACON:
            self._tx_local = True
            self._tx_remote = False
            self._beacon_play_start()

        elif self._state == State.DEINIT:
            self._tx_local = False
            self._tx_remote = False

    def _set_tx_pins(self):
        _logger.info("GPIO Configuration")

        if self._tx_local:
            self._tx_local_off_start = None
            self._set_tx_pin(PIN_TX_LOCAL, True)

        else:
            if not self._tx_local_off_start:
                self._tx_local_off_start = datetime.datetime.now()

            tx_end = self._tx_local_off_start + datetime.timedelta(milliseconds=TAIL_DURATION)
            if tx_end <= datetime.datetime.now():
                self._tx_local_off_start = None
                self._set_tx_pin(PIN_TX_LOCAL, False)

        if self._tx_remote != bool(GPIO.input(PIN_TX_REMOTE) == GPIO.HIGH):
            GPIO.output(PIN_TX_REMOTE, self._tx_remote)

    def _beacon_play_start(self):
        threading.Thread(target=self._beacon_play).start()

    def _beacon_play(self):
        time.sleep(3)
        self._beacon_time = False

    @staticmethod
    def _set_tx_pin(pin, value):
        if value != bool(GPIO.input(pin) == GPIO.HIGH):
            GPIO.output(pin, value)


if __name__ == "__main__":
    _logger.info("START")

    repeater = Repeater()
    repeater.run()

    _logger.info("END")
