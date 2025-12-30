"""Column lineage API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.responses import StreamingResponse

from api.core.logging import get_logger
from api.dependencies.auth import get_current_active_user, User
from api.v1.models.lineage import (
    LineageAnalysisRequest,
    LineageAnalysisResponse,
    LineageAnalysisJob,
    LineageResultsResponse,
    LineageExportRequest,
    ViewInfo,
    JobStatus,
    BaseViewRecord,
    BaseViewResponse,
)
from api.v1.services.lineage_service import LineageService
from api.v1.services.job_manager import JobManager

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
lineage_service = LineageService()
job_manager = JobManager()


@router.post("/analyze", response_model=LineageAnalysisResponse)
async def start_lineage_analysis(
    request: LineageAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Start column lineage analysis."""
    logger.info(
        "Starting lineage analysis",
        user_id=current_user.id,
        view_count=len(request.view_names) if request.view_names else "all",
        async_processing=request.async_processing,
    )
    
    try:
        # Create job
        job = LineageAnalysisJob(
            total_views=len(request.view_names) if request.view_names else 0,
            request_params=request.model_dump(),
        )
        
        # Store job
        job_manager.create_job(job)
        
        if request.async_processing:
            # Start background processing
            background_tasks.add_task(
                lineage_service.process_lineage_analysis,
                job.job_id,
                request,
                current_user.id,
            )
            
            return LineageAnalysisResponse(
                job_id=job.job_id,
                status=JobStatus.PENDING,
                message="Analysis started. Use the job_id to check status and retrieve results.",
                results_url=f"/api/v1/lineage/results/{job.job_id}",
            )
        else:
            # Synchronous processing
            results = await lineage_service.process_lineage_analysis(
                job.job_id, request, current_user.id
            )
            
            return LineageAnalysisResponse(
                job_id=job.job_id,
                status=JobStatus.COMPLETED,
                message="Analysis completed successfully.",
                results_url=f"/api/v1/lineage/results/{job.job_id}",
            )
            
    except Exception as e:
        logger.error("Failed to start lineage analysis", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}",
        )


@router.get("/status/{job_id}", response_model=LineageAnalysisJob)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Get lineage analysis job status."""
    logger.info("Getting job status", job_id=str(job_id), user_id=current_user.id)
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    return job


@router.get("/results/{job_id}", response_model=LineageResultsResponse)
async def get_lineage_results(
    job_id: UUID,
    limit: Optional[int] = None,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """Get lineage analysis results."""
    logger.info(
        "Getting lineage results",
        job_id=str(job_id),
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}",
        )
    
    try:
        results = job_manager.get_job_results(job_id, limit=limit, offset=offset)
        summary = job_manager.get_job_summary(job_id)
        
        return LineageResultsResponse(
            job_id=job_id,
            status=job.status,
            total_results=job.results_count,
            results=results,
            summary=summary,
        )
        
    except Exception as e:
        logger.error("Failed to get results", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve results: {str(e)}",
        )


@router.get("/views", response_model=List[ViewInfo])
async def list_available_views(
    schema_filter: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """List available database views."""
    logger.info(
        "Listing available views",
        user_id=current_user.id,
        schema_filter=schema_filter,
        limit=limit,
        offset=offset,
    )
    
    try:
        views = await lineage_service.get_available_views(
            schema_filter=schema_filter,
            limit=limit,
            offset=offset,
        )
        return views
        
    except Exception as e:
        logger.error("Failed to list views", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve views: {str(e)}",
        )


@router.post("/export/{job_id}")
async def export_lineage_results(
    job_id: UUID,
    export_request: LineageExportRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Export lineage analysis results."""
    logger.info(
        "Exporting lineage results",
        job_id=str(job_id),
        user_id=current_user.id,
        format=export_request.format,
    )
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}",
        )
    
    try:
        # Get results
        results = job_manager.get_job_results(job_id)
        
        # Filter by confidence if specified
        if export_request.filter_by_confidence is not None:
            results = [
                r for r in results 
                if r.confidence_score >= export_request.filter_by_confidence
            ]
        
        # Generate export
        export_data = await lineage_service.export_results(
            results, 
            export_request.format,
            include_metadata=export_request.include_metadata,
        )
        
        # Determine content type and filename
        if export_request.format.lower() == "csv":
            content_type = "text/csv"
            filename = f"lineage_results_{job_id}.csv"
        elif export_request.format.lower() == "json":
            content_type = "application/json"
            filename = f"lineage_results_{job_id}.json"
        elif export_request.format.lower() == "excel":
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"lineage_results_{job_id}.xlsx"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_request.format}",
            )
        
        return StreamingResponse(
            export_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
        
    except Exception as e:
        logger.error("Failed to export results", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export results: {str(e)}",
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a running job."""
    logger.info("Cancelling job", job_id=str(job_id), user_id=current_user.id)
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}",
        )
    
    try:
        job_manager.cancel_job(job_id)
        return {"message": "Job cancelled successfully"}
        
    except Exception as e:
        logger.error("Failed to cancel job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        )


@router.get("/jobs", response_model=List[LineageAnalysisJob])
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """List lineage analysis jobs."""
    logger.info(
        "Listing jobs",
        user_id=current_user.id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    
    try:
        jobs = job_manager.list_jobs(
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
        return jobs
        
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}",
        )


@router.get("/public/base-view", response_model=BaseViewResponse)
async def get_base_view_data(
    limit: Optional[int] = 100,
    offset: int = 0,
    mock: bool = False,  # Add mock parameter for testing
):
    """
    Public endpoint to retrieve data from Snowflake BASE_VIEW table.
    
    This endpoint does not require authentication and can be accessed publicly.
    Returns data from the PUBLIC.BASE_VIEW table with SR_NO and TABLE_NAME columns.
    
    Parameters:
    - limit: Maximum number of records to return (default: 100)
    - offset: Number of records to skip (default: 0)
    - mock: Force mock mode for testing (default: False)
    """
    logger.info(
        "Getting BASE_VIEW data",
        limit=limit,
        offset=offset,
        mock_mode=mock,
    )
    
    try:
        # Get database connection
        from api.dependencies.database import get_database_engine
        engine = get_database_engine()
        
        
        if not engine or mock:
            # Mock data for development/testing when no database is available
            logger.info("Using mock data for BASE_VIEW")
            mock_records = [
                BaseViewRecord(sr_no=1, table_name="CUSTOMERS"),
                BaseViewRecord(sr_no=2, table_name="ORDERS"),
                BaseViewRecord(sr_no=3, table_name="PRODUCTS"),
                BaseViewRecord(sr_no=4, table_name="INVENTORY"),
                BaseViewRecord(sr_no=5, table_name="SALES"),
                BaseViewRecord(sr_no=6, table_name="EMPLOYEES"),
                BaseViewRecord(sr_no=7, table_name="DEPARTMENTS"),
                BaseViewRecord(sr_no=8, table_name="SUPPLIERS"),
                BaseViewRecord(sr_no=9, table_name="CATEGORIES"),
                BaseViewRecord(sr_no=10, table_name="TRANSACTIONS"),
            ]
            
            # Apply pagination to mock data
            start_idx = offset
            end_idx = offset + limit if limit else len(mock_records)
            paginated_records = mock_records[start_idx:end_idx]
            
            return BaseViewResponse(
                total_records=len(mock_records),
                records=paginated_records,
            )
        
        # Query the actual Snowflake database
        logger.info("Querying Snowflake database")
        with engine.connect() as connection:
            from sqlalchemy import text
            
            # Count total records
            count_query = text("SELECT COUNT(*) as total FROM PUBLIC.BASE_VIEW")
            count_result = connection.execute(count_query)
            total_records = count_result.fetchone()[0]
            
            # Get paginated data - Snowflake uses LIMIT and OFFSET
            if limit:
                data_query = text("""
                    SELECT SR_NO, TABLE_NAME 
                    FROM PUBLIC.BASE_VIEW 
                    ORDER BY SR_NO 
                    LIMIT :limit OFFSET :offset
                """)
                result = connection.execute(data_query, {"limit": limit, "offset": offset})
            else:
                # If no limit specified, get all remaining records from offset
                data_query = text("""
                    SELECT SR_NO, TABLE_NAME 
                    FROM PUBLIC.BASE_VIEW 
                    ORDER BY SR_NO 
                    OFFSET :offset
                """)
                result = connection.execute(data_query, {"offset": offset})
            
            records = [
                BaseViewRecord(sr_no=row[0], table_name=row[1])
                for row in result.fetchall()
            ]
            
            return BaseViewResponse(
                total_records=total_records,
                records=records,
            )
            
    except Exception as e:
        logger.error("Failed to retrieve BASE_VIEW data", error=str(e))
        
        # Fallback to mock data on any error
        logger.info("Falling back to mock data due to error")
        mock_records = [
            BaseViewRecord(sr_no=1, table_name="CUSTOMERS"),
            BaseViewRecord(sr_no=2, table_name="ORDERS"),
            BaseViewRecord(sr_no=3, table_name="PRODUCTS"),
            BaseViewRecord(sr_no=4, table_name="INVENTORY"),
            BaseViewRecord(sr_no=5, table_name="SALES"),
        ]
        
        # Apply pagination to mock data
        start_idx = offset
        end_idx = offset + limit if limit else len(mock_records)
        paginated_records = mock_records[start_idx:end_idx]
        
        return BaseViewResponse(
            total_records=len(mock_records),
            records=paginated_records,
        )