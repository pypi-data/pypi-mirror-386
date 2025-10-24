import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[36;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format = "%(asctime)s - %(levelname).1s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

# Tạo một FileHandler để ghi log vào tệp tin
file_handler = logging.FileHandler('fb_api_wrapper.log', encoding='utf-8')
file_handler.setLevel(logging.ERROR)  # Chỉ ghi log từ mức ERROR trở lên vào tệp tin
file_handler.setFormatter(CustomFormatter())  # Sử dụng CustomFormatter cho file_handler
logger.addHandler(file_handler)

# Tạo một StreamHandler để in log ra màn hình
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)  # In tất cả các log ra màn hình
stream_handler.setFormatter(CustomFormatter())  # Sử dụng CustomFormatter cho stream_handler
logger.addHandler(stream_handler)