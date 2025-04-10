import threading
import inspect
import os
from datetime import datetime
from .path import logger_path

class Logger:
    COLORS = {
        'FATAL': '\033[91m',  
        'ERROR': '\033[91m',  
        'WARNING': '\033[93m', 
        'INFO': '\033[92m',    
        'VERBOSE': '\033[94m', 
        'RESET': '\033[0m'     
    }
    
    def __init__(self, log_to_file=False, log_level='VERBOSE'):
        self.log_to_file = log_to_file
        self.log_level = log_level
        self.current_log_file = self._get_log_file_name()
        self.last_log_time = datetime.now().hour
        self.log_levels = {
            'FATAL': 0,
            'ERROR': 1,
            'WARNING': 2,
            'INFO': 3,
            'VERBOSE': 4
        }
        if self.log_to_file:
            self.file = open(self.current_log_file, 'a', encoding='utf-8')
        
    # name
    def _get_log_file_name(self):
        logger_path.mkdir(exist_ok=True)
        return logger_path / datetime.now().strftime("DemonSlayerLog-%Y%m%d-%H%M.txt")
    
    # flash
    def _check_log_file(self):
        current_hour = datetime.now().hour
        if current_hour != self.last_log_time:
            self.last_log_time = current_hour
            if hasattr(self, 'file'):
                self.file.close()
            self.current_log_file = self._get_log_file_name()
            self.file = open(self.current_log_file, 'a', encoding='utf-8')
    
    # close file
    def close(self):
        if self.log_to_file and hasattr(self, 'file'):
            self.file.close()
    
    def _get_caller_info(self):
        frame = inspect.currentframe()
        try:
            # 跳过logger.py的调用栈
            while frame:
                frame = frame.f_back
                if frame and os.path.basename(frame.f_code.co_filename) != 'logger.py':
                    break
            
            if frame:
                info = inspect.getframeinfo(frame)
                filename = os.path.basename(info.filename)
                return f"{filename}:{info.lineno}"
            return "unknown:0"
        finally:
            del frame
    
    # log
    def log(self, level, message):
        if self.log_levels[level] > self.log_levels[self.log_level]:
            return
            
        if self.log_to_file:
            self._check_log_file()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caller_info = self._get_caller_info()
        
        formatted_message = f"{self.COLORS[level]}[{timestamp}][{level}][{caller_info}] {message}{self.COLORS['RESET']}"
        print(formatted_message)
        
        if self.log_to_file:
            self.file.write(f"[{timestamp}][{level}][{caller_info}] {message}\n")
            self.file.flush()

# 全局变量
logger = Logger(log_to_file=False, log_level='VERBOSE')

def fatal(message):
    logger.log('FATAL', message)

def error(message):
    logger.log('ERROR', message)

def warning(message):
    logger.log('WARNING', message)

def info(message):
    logger.log('INFO', message)

def verbose(message):
    logger.log('VERBOSE', message)
