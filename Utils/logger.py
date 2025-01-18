import logging


class LangLogger:
    def __init__(
        self,
        logger_name: str,
        log_level: int = logging.DEBUG,
    ):
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(log_level)
        self._log_fmt = logging.Formatter(
            fmt="[%(asctime)s][%(filename)s/%(lineno)s][%(levelname)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self._log_fmt)

        # Add Handler
        self._logger.addHandler(stream_handler)

    def debug(self, msg: str):
        self._logger.debug(msg)

    def info(self, msg: str):
        self._logger.info(msg)

    def warning(self, msg: str):
        self._logger.warning(msg)
    
    def error(self, msg: str):
        self._logger.error(msg)


def set_langsmith():
    pass