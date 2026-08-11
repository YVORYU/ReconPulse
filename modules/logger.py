import logging
import colorlog

formatter = colorlog.ColoredFormatter(
    '%(log_color)s[%(levelname)s]%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }

)

logger = colorlog.getLogger("reconpulse")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 屏蔽第三方库（requests 等）的 DEBUG 日志，避免刷屏
logging.getLogger("urllib3").setLevel(logging.WARNING)

def info(msg):
    logger.info(msg)

def warn(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def critical(msg):
    logger.critical(msg)

