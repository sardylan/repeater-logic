import logging
from enum import Enum

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

rootLogger = logging.getLogger()
rootLogger.level = logging.DEBUG

fileHandler = logging.FileHandler("repeater.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

_logger = logging.getLogger(__name__)


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
        self._state = State.OFF

    def run(self):
        _logger.info(self._state)


if __name__ == "__main__":
    _logger.info("START")

    repeater = Repeater()
    repeater.run()

    _logger.info("END")
