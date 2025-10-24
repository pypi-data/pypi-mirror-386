# -*- coding: utf-8 -*-
import os

from fastcodedog.context.context import ctx_instance
from fastcodedog.generation.api.config import Config
from fastcodedog.generation.base.file import File
from fastcodedog.generation.base.function import Function
from fastcodedog.generation.base.required_import import Import
from fastcodedog.generation.base.text import Text
from fastcodedog.generation.base.variable import Variable


class Log(File):
    def __init__(self):
        super().__init__(name='log',
                         file_path=os.path.join(ctx_instance.project.directory, 'util', 'log.py'),
                         package=f'{ctx_instance.project.package}.util.log')
        self.blocks.append(Variable('logger_', None))
        self.blocks.append(self.get_get_logger())
        self.blocks.append(self.get_enable_console_log())
        self.blocks.append(Variable('logger', value='get_logger()'))

    def get_get_logger(self):
        function = Function('get_logger')
        content =f"""global logger_
if logger_:
    return logger_

logger_ = logging.getLogger()
if logger_.hasHandlers():
    logger_.handlers.clear()
logger_.setLevel(log_level)

rotating_file_handler = ConcurrentRotatingFileHandler(log_filename, mode='a', maxBytes=int(log_max_bytes),
                                                      backupCount=int(log_backup_count), encoding=log_encoding)
rotating_file_handler.setLevel(log_level)
rotating_file_handler.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
logger_.addHandler(rotating_file_handler)

if log_console:
    enable_console_log(logger_)

return logger_
        """
        function.blocks.append(Text(content, possible_imports=['import logging', 'from concurrent_log_handler import ConcurrentRotatingFileHandler',
                                   Import('logging_config', Config().package), 'from review.config.config import log_filename','from review.config.config import log_level','from review.config.config import log_encoding','from review.config.config import log_datefmt','from review.config.config import log_format','from review.config.config import log_max_bytes','from review.config.config import log_backup_count','from review.config.config import log_console']))
        return function

    def get_enable_console_log(self):
        function = Function('enable_console_log', possible_imports=['import logging',
                                                                    Import('logging_config', Config().package)])
        function.params['logger_'] = Function.Parameter('logger_', nullable=False)
        content = f"""console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))
logger_.addHandler(console_handler)
"""
        function.blocks.append(Text(content, possible_imports=['from review.config.config import log_filename','from review.config.config import log_level','from review.config.config import log_encoding','from review.config.config import log_datefmt','from review.config.config import log_format','from review.config.config import log_max_bytes','from review.config.config import log_backup_count','from review.config.config import log_console']))
        return function
