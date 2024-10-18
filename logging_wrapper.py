import os
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import os
import datetime

# custom handler for log list
# main handler is TimedRotatingFileHandler
class ListHandler(logging.Handler):
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        log_entry = self.format(record)
        self.log_list.append(log_entry)
        # self.log_list.append("\n")

class LoggingWrapper:
  def __init__(self, name):
      self.m_logger = logging.getLogger(name)
      
      self.basic_level = logging.INFO
      self.basic_formatter = '[%(asctime)s] [%(levelname)s] %(message)s'
      self.basic_file_max_bytes = 10 * 1024 * 1024  # 10MB
      self.basic_file_max_count = 10

      self.m_logger.setLevel(logging.DEBUG)
      self.m_logger.propagate = False

      self.log_dir = "logs"
      if not os.path.exists(self.log_dir):
          os.makedirs(self.log_dir)

      self.level_map = {
          "info": logging.INFO,
          "error": logging.ERROR,
          "warning": logging.WARNING,
          "debug": logging.DEBUG,
          "critical": logging.CRITICAL
      }

  def add_file_handler(self, level=None, formatter=None):
      """ Add new file handler to logger. """

      # Generate log filename based on the current date
      current_date = datetime.datetime.now().strftime('%Y-%m-%d')
      if level is None:
          level = self.basic_level
      else:
          level = self.level_map[level]

      if formatter is None:
          formatter = self.basic_formatter

      info_filename = f"info_{current_date}.log"
      log_filename_format = os.path.join(self.log_dir, info_filename)

      # Use TimedRotatingFileHandler with no suffix, and a fresh log file daily
      file_handler = TimedRotatingFileHandler(
          log_filename_format, 
          when="midnight", 
          interval=1, 
          backupCount=self.basic_file_max_count, 
          encoding='utf-8', 
          utc=False
      )
      
      # Ensure a fresh filename by not allowing a suffix
      file_handler.namer = None  # Remove suffix

      # Set level and formatter for the handler
      file_handler.setLevel(level)
      formatter = logging.Formatter(formatter)
      file_handler.setFormatter(formatter)

      # Add the file handler to the logger
      self.m_logger.addHandler(file_handler)


  def add_stream_handler(self, level=None, stream=None, formatter=None):
    """ 
    Add new stream handler to logger
    Parameter
      stream : stream IO of handler. If None(Default), it use stderr
    """
    if level == None:
      level = self.basic_level
    else:level=self.level_map[level]

    if formatter == None:
      formatter = self.basic_formatter

    stream_handler = logging.StreamHandler(stream)

    stream_handler.setLevel(level)
    formatter = logging.Formatter(formatter)
    stream_handler.setFormatter(formatter)

    self.m_logger.addHandler(stream_handler)

  def add_list_handler(self, log_list, level=None, formatter=None):
    if level == None:
      level = self.basic_level
    else:level=self.level_map[level]

    if formatter == None:
      formatter = self.basic_formatter

    list_handler = ListHandler(log_list)

    formatter = logging.Formatter(formatter)
    list_handler.setFormatter(formatter)

    self.m_logger.addHandler(list_handler)

  def _log(self, msg, level):
    _logger = self.m_logger

    if level == logging.CRITICAL:
      _logger.critical(msg)
    elif level == logging.ERROR:
      _logger.error(msg)
    elif level == logging.WARNING:
      _logger.warning(msg)
    elif level == logging.INFO:
      _logger.info(msg)
    elif level == logging.DEBUG:
      _logger.debug(msg)
    elif level == logging.NOTSET:
      _logger.info(msg)
    else:
      pass

  def critical(self, msg):
    self._log(msg, logging.CRITICAL)

  def error(self, msg):
    self._log(msg, logging.ERROR)

  def warning(self, msg):
    self._log(msg, logging.WARNING)

  def info(self, msg):
    self._log(msg, logging.INFO)

  def debug(self, msg):
    self._log(msg, logging.DEBUG)



if __name__ == "__main__":
  logger = LoggingWrapper(__name__)
  logger.add_stream_handler(logging.DEBUG)
  logger.add_file_handler(logging.DEBUG)

  for i in range(1):
    logger.critical("Critical log")
    logger.error("Error log")
    logger.warning("Warning log")
    logger.info("Info log")
    logger.debug("Debug log")
