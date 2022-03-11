import logging
from sys import platform
from logging.handlers import RotatingFileHandler

# to see the log file run with tail -f <logfilename>
LOG_APP_FILENAME = 'app.log'
LOG_WORKER_FILENAME = 'worker.log'
if platform == "linux":
    print("Detected Linux, changing log dir to /var/log")
    LOG_WORKER_FILENAME = "/var/log/telemhub/worker.log"  # having permissions?
    LOG_APP_FILENAME = "/var/log/telemhub/app.log"  # having permissions?

# LOGLEVEL = logging.DEBUG
LOGLEVEL = logging.INFO
# LOGLEVEL = logging.WARNING

formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = RotatingFileHandler(log_file, mode='a', maxBytes=5 * 1024 * 1024,
                                  backupCount=2, encoding=None, delay=0)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger_app = setup_logger("logger_app", LOG_APP_FILENAME, LOGLEVEL)
logger_worker = setup_logger("logger_worker", LOG_WORKER_FILENAME, LOGLEVEL)
