"""
核心日志管理器

提供日志管理器的完整实现，支持自定义日志器注册和默认日志器创建
"""

import threading
from typing import Dict, Optional, Type
from .protocol import LoggerProtocol


class LogManager:
    _loggers: Dict[str, LoggerProtocol] = {}
    _lock = threading.RLock()
    _initialized = False
    _default_logger_class: Optional[Type[LoggerProtocol]] = None

    @classmethod
    def set_default_logger_class(cls, logger_class: Type[LoggerProtocol]) -> None:
        cls._default_logger_class = logger_class

    @classmethod
    def _get_default_logger_class(cls) -> Type[LoggerProtocol]:
        if cls._default_logger_class is None:
            try:
                from jiuwen.extensions.common.log.default_impl import DefaultLogger
                cls._default_logger_class = DefaultLogger
            except ImportError:
                raise RuntimeError("No default logger class set and cannot import DefaultLogger from extensions")
        return cls._default_logger_class

    @classmethod
    def _get_log_config(cls) -> Optional[object]:
        try:
            from jiuwen.extensions.common.configs.log_config import log_config
            return log_config
        except ImportError:
            return None

    @classmethod
    def initialize(cls) -> None:
        with cls._lock:
            if cls._initialized:
                return

            default_logger_class = cls._get_default_logger_class()
            log_config = cls._get_log_config()

            if log_config:
                all_configs = log_config.get_all_configs()
                for log_type, config in all_configs.items():
                    if log_type not in cls._loggers:
                        cls._loggers[log_type] = default_logger_class(log_type, config)
            else:
                raise RuntimeError("LogConfig not available. Please ensure extensions.common.configs.log_config is properly configured.")

            cls._initialized = True

    @classmethod
    def register_logger(cls, log_type: str, logger: LoggerProtocol) -> None:
        if not isinstance(logger, LoggerProtocol):
            raise TypeError(f"Logger must implement LoggerProtocol, got {type(logger)}")

        with cls._lock:
            cls._loggers[log_type] = logger

    @classmethod
    def get_logger(cls, log_type: str) -> LoggerProtocol:
        """获取日志器，如果不存在则创建默认日志器"""
        if not cls._initialized:
            cls.initialize()

        with cls._lock:
            if log_type not in cls._loggers:
                default_logger_class = cls._get_default_logger_class()
                log_config = cls._get_log_config()
                
                if log_config:
                    config = log_config.get_custom_config(log_type)
                else:
                    raise RuntimeError(f"LogConfig not available. Cannot create logger for '{log_type}'.")
                
                cls._loggers[log_type] = default_logger_class(log_type, config)

            return cls._loggers[log_type]

    @classmethod
    def get_all_loggers(cls) -> Dict[str, LoggerProtocol]:
        if not cls._initialized:
            cls.initialize()
        return cls._loggers.copy()

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._loggers = {}
            cls._initialized = False
            cls._default_logger_class = None

    @classmethod
    def create_default_logger(cls, log_type: str, config: Dict = None) -> LoggerProtocol:
        if config is None:
            log_config = cls._get_log_config()
            if log_config:
                config = log_config.get_custom_config(log_type)
            else:
                raise RuntimeError(f"LogConfig not available. Cannot create logger for '{log_type}'.")
        
        default_logger_class = cls._get_default_logger_class()
        return default_logger_class(log_type, config) 