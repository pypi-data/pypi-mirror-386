#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
def start():
    print("import successful")
# constants
__author__ = 'shancx'
 
__author_email__ = 'shancx@126.com'

# @Time : 2023/09/27 下午8:52
# @Author : shanchangxi
# @File : util_log.py
import logging
from logging.handlers import RotatingFileHandler
import os
from shancx import crDir 
def _loggers(logger_name="loggers", root="./logs", phase="project", level=logging.INFO, screen=True, max_bytes=10*1024*1024, backup_count=5, overwrite=False,handlersflag=True):
    '''set up logger with rotating file handler'''
    l = logging.getLogger(logger_name)
    if handlersflag:
        if l.handlers:
            return l
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S') 
    log_file = os.path.join(root, '{}.log'.format(phase))
    crDir(log_file)
    # Use RotatingFileHandler with 'w' mode to overwrite log file if needed
    mode = 'w' if overwrite else 'a'
    fh = RotatingFileHandler(log_file, mode=mode, maxBytes=max_bytes, backupCount=backup_count)
    fh.setFormatter(formatter)    
    l.setLevel(level)
    l.addHandler(fh)    
    if screen:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        l.addHandler(sh)    
    return l


"""
logger = _loggers(logger_name="test_logger", root=curpathplus, phase="test_log", overwrite=True, screen=True)
# 测试日志输出
for i in range(5):
    logger.info(f"这是日志消息 {i+1}")
    time.sleep(1)
"""

import logging
def setlogger(level=logging.INFO):
 
    logging.basicConfig(
        level=level,  # 动态接受级别参数
        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
        force=True  # 强制覆盖现有配置（Python 3.8+）
    )
    return logging.getLogger()
'''
# 使用示例
if __name__ == "__main__":
    logger = setlogger(level=logging.DEBUG)  # 设置为DEBUG级别
    logger.debug("这条日志会显示")  # 默认情况下DEBUG不显示，但因为我们设置了级别，现在会显示
    logger.info("这是一条INFO日志")
'''

import os
from datetime import datetime
from shancx.NN import _loggers
from shancx import lock_file
from shancx.wait import check_lock
from shancx import crDir
logger =_loggers()
def check_process_data(UTC, sat_cd,basepath ="/mnt/wtx_weather_forecast/scx/test/lock_files" ): 
    try:
        UTCStr = UTC.strftime("%Y%m%d%H%M")
        file = f"/mnt/wtx_weather_forecast/scx/test/lock_files/{sat_cd}/{UTCStr[:4]}/{UTCStr[:8]}/File_{UTCStr}.lock"
        crDir(file)
        if not lock_file(file):
            if check_lock(file):
                logger.info("data is making or maked")
                return True ,file       
        return False,file        
    except Exception as e:
        logger.error(f"Error in check_and_process_data: {str(e)}")
        return False,file  
"""
flag1,file = check_process_data(UTC, "H9SEAS" )
if flag1:
    sys.exit() 
"""