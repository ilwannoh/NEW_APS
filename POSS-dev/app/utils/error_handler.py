import logging
import traceback
import functools
from typing import Callable, Dict, Any, Optional, Type, Union, List
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorLevel(Enum) :
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorType(Enum) :
    DATA_ERROR = 'DATA ERROR'
    CALCULATION_ERROR = 'CALCULATION ERROR'
    FILE_ERROR = 'FILE ERROR'
    VALIDATION_ERROR = 'VALIDATION ERROR'
    RUNTIME_ERROR = 'RUNTIME ERROR'
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'

"""
사용자 정의 이외의 기본 클래스
"""
class AppError(Exception) :
    def __init__(self, message : str, error_type : ErrorType = ErrorType.UNKNOWN_ERROR,
                 details : Optional[Dict[str, Any]] = None) :
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

"""
데이터 처리 관련 오류
"""
class DataError(AppError) :
    def __init__(self, message : str, details : Optional[Dict[str, Any]] = None) :
        super().__init__(message, ErrorType.DATA_ERROR, details)

"""
계산 관련 오류
"""
class CalculationError(AppError) :
    def __init__(self, message : str, details : Optional[Dict[str, Any]] = None) :
        super().__init__(message, ErrorType.CALCULATION_ERROR, details)

"""
파일 처리 관련 오류
"""
class FileError(AppError) :
    def __init__(self, message : str, details : Optional[Dict[str, Any]] = None) :
        super().__init__(message, ErrorType.FILE_ERROR, details)

"""
유효성 검증 관련 오류
"""
class ValidationError(AppError) :
    def __init__(self, message : str, details : Optional[Dict[str, Any]] = None) :
        super().__init__(message, ErrorType.VALIDATION_ERROR, details)

"""
오류 로깅 함수
"""
def log_error(error : Union[Exception, str],
              level : ErrorLevel = ErrorLevel.ERROR,
              error_type : Optional[ErrorType] = None,
              details : Optional[Dict[str, Any]] = None) -> None :
    if isinstance(error, AppError) :
        message = f'[{error.error_type.value}] {error.message}'
        details = error.details
    elif isinstance(error, Exception) :
        message = f'[{error_type.value if error_type else ErrorType.UNKNOWN_ERROR.value}] {str(error)}'
    else :
        message = f'[{error_type.value if error_type else ErrorType.UNKNOWN_ERROR.value}] {error}'

    if details :
        message += f' - 상세 정보 : {details}'

    if level == ErrorLevel.INFO :
        logger.info(message)
    elif level == ErrorLevel.WARNING :
        logger.warning(message)
    elif level == ErrorLevel.ERROR :
        logger.error(message)
    elif level == ErrorLevel.CRITICAL :
        logger.critical(message)

    if level in (ErrorLevel.ERROR, ErrorLevel.CRITICAL) :
        logger.error(traceback.format_exc())

"""
오류를 처리하는 함수
"""
def handle_error(error : Exception,
                 show_dialog : bool = True,
                 level : ErrorLevel = ErrorLevel.ERROR,
                 callback : Optional[Callable] = None) -> None :
    if isinstance(error, AppError) :
        log_error(error, level)
    else :
        error_type = None
        if 'data' in str(error).lower() :
            error_type = ErrorType.DATA_ERROR
        elif 'file' in str(error).lower() or 'path' in str(error).lower() :
            error_type = ErrorType.FILE_ERROR
        elif 'calculation' in str(error).lower() or 'math' in str(error).lower() :
            error_type = ErrorType.CALCULATION_ERROR
        else :
            error_type = ErrorType.RUNTIME_ERROR

        log_error(error, level, error_type)

    if callback :
        try :
            callback(error)
        except Exception as callback_error :
            log_error(f'콜백 함수 실행 중 오류 : {str(callback_error)}', ErrorLevel.ERROR)

"""
함수 데코레이션 설정
"""
def error_handler(func = None, *,
                  show_dialog : bool = True,
                  handle_exceptions : List[Type[Exception]] = None,
                  default_return : Any = None,
                  level : ErrorLevel = ErrorLevel.ERROR,
                  callback : Optional[Callable] = None) :
    if func is None :
        return functools.partial(
            error_handler,
            show_dialog = show_dialog,
            handle_exceptions = handle_exceptions,
            default_return = default_return,
            level = level,
            callback = callback
        )
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) :
        try :
            return func(*args, *kwargs)
        except Exception as e :
            if handle_exceptions and not any(isinstance(e, exc) for exc in handle_exceptions) :
                raise e
            
            handle_error(e, show_dialog, level, callback)

            return default_return

    return wrapper


"""
안전한 작업 수행을 위한 함수
"""
def safe_operation(operation_func, error_message, *args, **kwargs) :
    try :
        return operation_func(*args, **kwargs)
    except Exception as e :
        log_error(f'{error_message} : {str(e)}', ErrorLevel.ERROR)
        return None