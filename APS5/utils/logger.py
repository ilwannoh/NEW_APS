import logging
import logging.handlers
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading
import os


class APSLogger:
    """
    APS 시스템을 위한 로거 클래스
    날짜별로 로그 파일을 분리하여 관리
    """
    
    _instance = None
    _lock = threading.Lock()
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.log_dir = Path('logs')
            self.log_dir.mkdir(exist_ok=True)
            
            # 기본 로그 설정
            self.default_level = logging.INFO
            self.max_bytes = 10 * 1024 * 1024  # 10MB
            self.backup_count = 5
            
            # 로그 포맧 설정
            self.formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            self.detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            self.initialized = True
    
    def get_logger(self, name: str, level: Optional[int] = None, 
                  use_detailed_format: bool = False) -> logging.Logger:
        """
        로거 인스턴스 반환 또는 생성
        
        Args:
            name: 로거 이름
            level: 로그 레벨
            use_detailed_format: 상세 포맧 사용 여부
        
        Returns:
            로거 인스턴스
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level or self.default_level)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level or self.default_level)
        formatter = self.detailed_formatter if use_detailed_format else self.formatter
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 추가 (날짜별 로테이션)
        file_handler = self._create_rotating_file_handler(name, use_detailed_format)
        logger.addHandler(file_handler)
        
        # 에러 로그 전용 핸들러
        if level != logging.ERROR:
            error_handler = self._create_error_file_handler(name, use_detailed_format)
            logger.addHandler(error_handler)
        
        logger.propagate = False
        self._loggers[name] = logger
        
        return logger
    
    def _create_rotating_file_handler(self, name: str, use_detailed_format: bool) -> logging.Handler:
        """
        날짜별 로테이션 파일 핸들러 생성
        """
        today = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f"{name}_{today}.log"
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        formatter = self.detailed_formatter if use_detailed_format else self.formatter
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_error_file_handler(self, name: str, use_detailed_format: bool) -> logging.Handler:
        """
        에러 전용 파일 핸들러 생성
        """
        today = datetime.now().strftime('%Y%m%d')
        error_log_file = self.log_dir / f"{name}_error_{today}.log"
        
        handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        handler.setLevel(logging.ERROR)
        formatter = self.detailed_formatter if use_detailed_format else self.formatter
        handler.setFormatter(formatter)
        
        return handler
    
    def set_log_level(self, name: str, level: int) -> None:
        """
        특정 로거의 로그 레벨 변경
        
        Args:
            name: 로거 이름
            level: 새로운 로그 레벨
        """
        if name in self._loggers:
            logger = self._loggers[name]
            logger.setLevel(level)
            
            for handler in logger.handlers:
                if not isinstance(handler, logging.handlers.RotatingFileHandler) or handler.level != logging.ERROR:
                    handler.setLevel(level)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """
        오래된 로그 파일 정리
        
        Args:
            days_to_keep: 보존할 일수
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in self.log_dir.glob('*.log*'):
            try:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    print(f"오래된 로그 파일 삭제: {log_file}")
            except Exception as e:
                print(f"로그 파일 삭제 실패: {log_file}, 오류: {e}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        로그 파일 통계 정보 반환
        
        Returns:
            로그 파일 통계
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0.0,
            'files_by_date': {},
            'error_files': 0
        }
        
        for log_file in self.log_dir.glob('*.log*'):
            try:
                file_size = log_file.stat().st_size
                stats['total_files'] += 1
                stats['total_size_mb'] += file_size / (1024 * 1024)
                
                # 날짜별 분류
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d')
                if file_date not in stats['files_by_date']:
                    stats['files_by_date'][file_date] = {'count': 0, 'size_mb': 0.0}
                
                stats['files_by_date'][file_date]['count'] += 1
                stats['files_by_date'][file_date]['size_mb'] += file_size / (1024 * 1024)
                
                # 에러 로그 파일 카운트
                if 'error' in log_file.name:
                    stats['error_files'] += 1
                    
            except Exception:
                continue
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats
    
    def create_audit_logger(self, name: str = 'audit') -> logging.Logger:
        """
        감사 로그 전용 로거 생성
        
        Args:
            name: 감사 로거 이름
        
        Returns:
            감사 로거
        """
        audit_logger = self.get_logger(f"{name}_audit", logging.INFO, use_detailed_format=True)
        
        # 감사 로그는 별도 포맧팅 사용
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        for handler in audit_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.setFormatter(audit_formatter)
        
        return audit_logger
    
    def log_system_info(self, logger_name: str = 'system') -> None:
        """
        시스템 정보를 로그에 기록
        
        Args:
            logger_name: 로거 이름
        """
        logger = self.get_logger(logger_name)
        
        try:
            import platform
            import psutil
            
            logger.info(f"="*50)
            logger.info(f"APS 시스템 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Python 버전: {platform.python_version()}")
            logger.info(f"운영체제: {platform.system()} {platform.release()}")
            logger.info(f"CPU 코어 수: {psutil.cpu_count()}")
            logger.info(f"메모리: {psutil.virtual_memory().total / (1024**3):.1f}GB")
            logger.info(f"디스크 여유 공간: {psutil.disk_usage('.').free / (1024**3):.1f}GB")
            logger.info(f"="*50)
            
        except ImportError:
            logger.info(f"APS 시스템 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("시스템 정보를 가져올 수 없습니다. (psutil 라이브러리 필요)")
    
    def __del__(self):
        """로거 정리"""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class PerformanceLogger:
    """
    성능 모니터링을 위한 로거
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times: Dict[str, datetime] = {}
    
    def start_timer(self, operation: str) -> None:
        """
        작업 시간 측정 시작
        
        Args:
            operation: 작업 이름
        """
        self.start_times[operation] = datetime.now()
        self.logger.info(f"[PERF] {operation} 시작")
    
    def end_timer(self, operation: str) -> float:
        """
        작업 시간 측정 종료
        
        Args:
            operation: 작업 이름
        
        Returns:
            소요 시간(초)
        """
        if operation not in self.start_times:
            self.logger.warning(f"[PERF] {operation} 시작 시간을 찾을 수 없습니다")
            return 0.0
        
        start_time = self.start_times.pop(operation)
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"[PERF] {operation} 완료: {duration:.3f}초")
        return duration
    
    def log_memory_usage(self, operation: str = "") -> None:
        """
        메모리 사용량 로그
        
        Args:
            operation: 작업 이름
        """
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.logger.info(f"[MEMORY] {operation} 메모리 사용량: {memory_mb:.1f}MB")
        except ImportError:
            self.logger.warning("[MEMORY] psutil 라이브러리가 설치되지 않아 메모리 사용량을 확인할 수 없습니다")


# 편의 함수들
def get_logger(name: str, level: Optional[int] = None, 
              use_detailed_format: bool = False) -> logging.Logger:
    """
    로거 인스턴스 반환
    
    Args:
        name: 로거 이름
        level: 로그 레벨
        use_detailed_format: 상세 포맧 사용 여부
    
    Returns:
        로거 인스턴스
    """
    aps_logger = APSLogger()
    return aps_logger.get_logger(name, level, use_detailed_format)


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    성능 로거 인스턴스 반환
    
    Args:
        name: 로거 이름
    
    Returns:
        성능 로거 인스턴스
    """
    logger = get_logger(f"{name}_performance", logging.INFO)
    return PerformanceLogger(logger)


def setup_logging(log_level: int = logging.INFO) -> None:
    """
    로깅 시스템 초기화
    
    Args:
        log_level: 기본 로그 레벨
    """
    aps_logger = APSLogger()
    aps_logger.default_level = log_level
    
    # 시스템 로거 생성 및 시스템 정보 로깅
    aps_logger.log_system_info()
    
    # 오래된 로그 정리
    aps_logger.cleanup_old_logs()


def cleanup_logs(days_to_keep: int = 30) -> None:
    """
    오래된 로그 파일 정리
    
    Args:
        days_to_keep: 보존할 일수
    """
    aps_logger = APSLogger()
    aps_logger.cleanup_old_logs(days_to_keep)


def get_log_stats() -> Dict[str, Any]:
    """
    로그 파일 통계 정보 반환
    
    Returns:
        로그 파일 통계
    """
    aps_logger = APSLogger()
    return aps_logger.get_log_stats()

