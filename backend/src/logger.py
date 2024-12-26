import logging
from logging.handlers import RotatingFileHandler


class Logger:
    __shared_instance = None


    def __new__(cls, *args, **kwargs):
        if cls.__shared_instance is None:
            cls.__shared_instance = super().__new__(cls)
            cls.__shared_instance._logger = cls.__create_logger()
        return cls.__shared_instance


    @staticmethod
    def __create_logger() -> logging.Logger:
        logger = logging.getLogger("pricetracker")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        rotating_file_handler = RotatingFileHandler(
            "app_rotating.log", maxBytes=5 * 1024 * 1024, backupCount=3
        )
        rotating_file_handler.setLevel(logging.ERROR)
        rotating_file_handler.setFormatter(formatter)
        logger.addHandler(rotating_file_handler)

        return logger


    def log_debug(self, message: object):
        self._logger.debug(message)


    def log_info(self, message: object):
        self._logger.info(message)


    def log_error(self, message: object):
        self._logger.error(message)