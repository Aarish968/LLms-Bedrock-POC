"""Background job executor using thread pool for non-blocking operations."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Callable, Any, Optional
from uuid import UUID
from datetime import datetime

from api.core.logging import get_logger

logger = get_logger(__name__)


class BackgroundJobExecutor:
    """Manages background job execution using thread pool to prevent blocking."""
    
    _instance: Optional['BackgroundJobExecutor'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackgroundJobExecutor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Thread pool for CPU/IO intensive tasks
            self.executor = ThreadPoolExecutor(
                max_workers=4,  # Adjust based on server capacity
                thread_name_prefix="lineage_worker"
            )
            
            # Track running jobs
            self.running_jobs: Dict[str, Future] = {}
            
            # Job completion callbacks
            self.completion_callbacks: Dict[str, Callable] = {}
            
            BackgroundJobExecutor._initialized = True
            logger.info("BackgroundJobExecutor initialized with 4 workers")
    
    async def submit_job(
        self, 
        job_id: UUID, 
        func: Callable, 
        *args, 
        completion_callback: Optional[Callable] = None,
        **kwargs
    ) -> None:
        """
        Submit a job to the thread pool for background execution.
        
        Args:
            job_id: Unique job identifier
            func: Function to execute in background
            *args: Arguments for the function
            completion_callback: Optional callback when job completes
            **kwargs: Keyword arguments for the function
        """
        job_id_str = str(job_id)
        
        try:
            logger.info(f"Submitting job to thread pool", job_id=job_id_str)
            
            # Submit to thread pool
            future = self.executor.submit(func, *args, **kwargs)
            
            # Track the job
            self.running_jobs[job_id_str] = future
            
            # Store completion callback if provided
            if completion_callback:
                self.completion_callbacks[job_id_str] = completion_callback
            
            # Monitor completion asynchronously (non-blocking)
            asyncio.create_task(self._monitor_job_completion(job_id_str, future))
            
            logger.info(f"Job submitted successfully", job_id=job_id_str)
            
        except Exception as e:
            logger.error(f"Failed to submit job", job_id=job_id_str, error=str(e))
            raise
    
    async def _monitor_job_completion(self, job_id: str, future: Future) -> None:
        """
        Monitor job completion without blocking the main thread.
        
        Args:
            job_id: Job identifier
            future: Future object representing the job
        """
        try:
            logger.info(f"Monitoring job completion", job_id=job_id)
            
            # Wait for completion without blocking the event loop
            result = await asyncio.wrap_future(future)
            
            logger.info(f"Job completed successfully", job_id=job_id)
            
            # Execute completion callback if exists
            callback = self.completion_callbacks.get(job_id)
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(job_id, result, None)
                    else:
                        callback(job_id, result, None)
                except Exception as callback_error:
                    logger.error(f"Completion callback failed", job_id=job_id, error=str(callback_error))
            
        except Exception as e:
            logger.error(f"Job failed during execution", job_id=job_id, error=str(e))
            
            # Execute error callback if exists
            callback = self.completion_callbacks.get(job_id)
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(job_id, None, e)
                    else:
                        callback(job_id, None, e)
                except Exception as callback_error:
                    logger.error(f"Error callback failed", job_id=job_id, error=str(callback_error))
        
        finally:
            # Clean up tracking
            self.running_jobs.pop(job_id, None)
            self.completion_callbacks.pop(job_id, None)
            
            # Note: Job logger cleanup is handled separately to allow log access after completion
    
    def is_job_running(self, job_id: UUID) -> bool:
        """Check if a job is currently running."""
        return str(job_id) in self.running_jobs
    
    def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        job_id_str = str(job_id)
        future = self.running_jobs.get(job_id_str)
        
        if future and not future.done():
            cancelled = future.cancel()
            if cancelled:
                logger.info(f"Job cancelled successfully", job_id=job_id_str)
                self.running_jobs.pop(job_id_str, None)
                self.completion_callbacks.pop(job_id_str, None)
            return cancelled
        
        return False
    
    def get_running_jobs_count(self) -> int:
        """Get the number of currently running jobs."""
        return len(self.running_jobs)
    
    def get_running_job_ids(self) -> list[str]:
        """Get list of currently running job IDs."""
        return list(self.running_jobs.keys())
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor and cancel all running jobs.
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        logger.info("Shutting down BackgroundJobExecutor")
        
        if not wait:
            # Cancel all running jobs
            for job_id, future in self.running_jobs.items():
                if not future.done():
                    future.cancel()
                    logger.info(f"Cancelled job during shutdown", job_id=job_id)
        
        # Shutdown the executor
        self.executor.shutdown(wait=wait)
        
        # Clear tracking
        self.running_jobs.clear()
        self.completion_callbacks.clear()
        
        logger.info("BackgroundJobExecutor shutdown complete")


# Global instance
background_executor = BackgroundJobExecutor()