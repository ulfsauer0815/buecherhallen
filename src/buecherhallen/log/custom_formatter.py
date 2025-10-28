import logging
import os


class CustomFormatter(logging.Formatter):
    magenta = "\x1b[35;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    @staticmethod
    def __colors_enabled():
        no_color_env = os.environ.get('NO_COLOR')
        if no_color_env is not None and no_color_env.lower() in ('', '1', 'true', 'yes'):
            return False
        return True

    colored_output = __colors_enabled()

    COLORS = {
        logging.DEBUG: magenta,
        logging.INFO: blue,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def __get_format(self, level):
        if self.colored_output:
            return f"[%(asctime)s] [{self.COLORS.get(level)}%(levelname)s{self.reset}] %(message)s"
        else:
            return f"[%(asctime)s] [%(levelname)s] %(message)s"

    def format(self, record):
        log_fmt = self.__get_format(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
