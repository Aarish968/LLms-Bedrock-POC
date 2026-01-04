"""Enhanced logging configuration for job-specific logging."""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

import structlog
from api.core.config import get_settings


def setup_enhanced_logging():
    """Setup enhanced logging with separate job logging capability."""
    settings = get_settings()
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    (logs_dir / "jobs").mkdir(exist_ok=True)
    
    # Configure structlog for server logs (keep existing configuration)
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="ISO"),
    ]
    
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger for server logs
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler for server logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Server log formatter
    if settings.LOG_FORMAT == "json":
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Optional: File handler for server logs
    if hasattr(settings, 'SERVER_LOG_FILE') and settings.SERVER_LOG_FILE:
        file_handler = logging.FileHandler(logs_dir / "server.log")
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_server_logger(name: str) -> structlog.BoundLogger:
    """Get a server logger (not job-specific)."""
    return structlog.get_logger(name)


def get_log_summary() -> Dict[str, Any]:
    """Get logging system summary."""
    logs_dir = Path("logs")
    jobs_dir = logs_dir / "jobs"
    
    server_log_file = logs_dir / "server.log"
    
    summary = {
        "logs_directory": str(logs_dir),
        "jobs_logs_directory": str(jobs_dir),
        "server_log_exists": server_log_file.exists(),
        "job_log_files_count": len(list(jobs_dir.glob("*.log"))) if jobs_dir.exists() else 0,
    }
    
    if server_log_file.exists():
        summary["server_log_size_bytes"] = server_log_file.stat().st_size
    
    return summary