import logging


class CustomFormatter(logging.Formatter):
    magenta = "\x1b[35;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        logging.DEBUG: magenta,
        logging.INFO: blue,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def __get_format(self, level):
        return f"[%(asctime)s] [{self.COLORS.get(level)}%(levelname)s{self.reset}] %(message)s"

    def format(self, record):
        log_fmt = self.__get_format(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
