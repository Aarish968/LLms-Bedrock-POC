"""Job-specific logging system for background tasks."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID

import structlog

from api.core.config import get_settings


class JobLogger:
    """Job-specific logger that writes to separate log files."""
    
    def __init__(self, job_id: UUID, log_level: str = "INFO"):
        self.job_id = str(job_id)
        self.log_level = log_level
        self.log_file_path = self._setup_log_file()
        self.logger = self._setup_logger()
        
    def _setup_log_file(self) -> Path:
        """Create job-specific log file path."""
        settings = get_settings()
        
        # Create logs directory structure
        logs_dir = Path("logs")
        jobs_dir = logs_dir / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create job-specific log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"job_{self.job_id[:8]}_{timestamp}.log"
        log_file_path = jobs_dir / log_filename
        
        return log_file_path
    
    def _setup_logger(self) -> logging.Logger:
        """Setup job-specific logger with file handler."""
        logger_name = f"job_{self.job_id}"
        logger = logging.getLogger(logger_name)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(getattr(logging, self.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger (avoid duplicate logs)
        logger.propagate = False
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        self._log_with_context("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        self._log_with_context("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context."""
        self._log_with_context("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        self._log_with_context("debug", message, **kwargs)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with additional context."""
        # Format context if provided
        if kwargs:
            context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
            
        # Log to file
        getattr(self.logger, level)(full_message)
    
    def log_progress(self, current: int, total: int, message: str = ""):
        """Log progress information."""
        percentage = (current / total * 100) if total > 0 else 0
        progress_msg = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if message:
            progress_msg += f" - {message}"
        self.info(progress_msg)
    
    def log_view_processing(self, view_name: str, status: str, details: str = ""):
        """Log view processing status."""
        msg = f"View: {view_name} | Status: {status}"
        if details:
            msg += f" | Details: {details}"
        
        if status.upper() in ["ERROR", "FAILED"]:
            self.error(msg)
        elif status.upper() in ["WARNING", "SKIPPED"]:
            self.warning(msg)
        else:
            self.info(msg)
    
    def log_job_start(self, request_params: Dict[str, Any]):
        """Log job start with parameters."""
        self.info("=== JOB STARTED ===")
        self.info(f"Job ID: {self.job_id}")
        self.info(f"Started at: {datetime.now().isoformat()}")
        self.info("Request Parameters:")
        for key, value in request_params.items():
            self.info(f"  {key}: {value}")
        self.info("=" * 50)
    
    def log_job_completion(self, status: str, results_count: int = 0, error_message: str = ""):
        """Log job completion."""
        self.info("=== JOB COMPLETED ===")
        self.info(f"Job ID: {self.job_id}")
        self.info(f"Completed at: {datetime.now().isoformat()}")
        self.info(f"Final Status: {status}")
        
        if status == "COMPLETED":
            self.info(f"Results Count: {results_count}")
        elif status == "FAILED" and error_message:
            self.error(f"Error: {error_message}")
            
        self.info("=" * 50)
    
    def get_log_file_path(self) -> str:
        """Get the path to the log file."""
        return str(self.log_file_path)
    
    def get_log_content(self, lines: Optional[int] = None) -> str:
        """Get log file content."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                if lines:
                    # Get last N lines
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
                else:
                    return f.read()
        except FileNotFoundError:
            return "Log file not found"
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def cleanup(self):
        """Clean up logger handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


class JobLoggerManager:
    """Manages job loggers and provides centralized access."""
    
    _loggers: Dict[str, JobLogger] = {}
    
    @classmethod
    def get_logger(cls, job_id: UUID) -> JobLogger:
        """Get or create job logger."""
        job_id_str = str(job_id)
        
        if job_id_str not in cls._loggers:
            cls._loggers[job_id_str] = JobLogger(job_id)
            
        return cls._loggers[job_id_str]
    
    @classmethod
    def cleanup_logger(cls, job_id: UUID):
        """Clean up job logger."""
        job_id_str = str(job_id)
        
        if job_id_str in cls._loggers:
            cls._loggers[job_id_str].cleanup()
            del cls._loggers[job_id_str]
    
    @classmethod
    def list_job_logs(cls) -> Dict[str, str]:
        """List all job log files."""
        logs_dir = Path("logs/jobs")
        if not logs_dir.exists():
            return {}
            
        job_logs = {}
        for log_file in logs_dir.glob("job_*.log"):
            job_logs[log_file.stem] = str(log_file)
            
        return job_logs
    
    @classmethod
    def cleanup_old_logs(cls, max_age_days: int = 7):
        """Clean up old log files."""
        logs_dir = Path("logs/jobs")
        if not logs_dir.exists():
            return 0
            
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        cleaned_count = 0
        
        for log_file in logs_dir.glob("job_*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception:
                    pass  # Ignore cleanup errors
                    
        return cleaned_count