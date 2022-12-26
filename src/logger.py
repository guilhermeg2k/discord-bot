import logging


class Logger:

    def __init__(self) -> None:
        # create logger
        self.logger = logging.getLogger('bot-logger')
        self.logger.setLevel(logging.INFO)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s ->  %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(ch)

    def get_logger(self) -> logging.Logger:
        return self.logger


'''
Exemplos de logs:
    logger.debug('debug message'): Funcionamento detalhado.
    logger.info('info message'): Funcionamento esperado.
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
'''
