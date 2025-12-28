"""Lineage API endpoint tests."""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from api.v1.models.lineage import LineageAnalysisRequest, JobStatus


def test_start_lineage_analysis(client: TestClient, auth_headers, mock_database):
    """Test starting lineage analysis."""
    request_data = {
        "view_names": ["TEST_VIEW"],
        "async_processing": False
    }
    
    with patch('api.v1.services.lineage_service.LineageService.process_lineage_analysis') as mock_process:
        mock_process.return_value = []
        
        response = client.post(
            "/api/v1/lineage/analyze",
            json=request_data,
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    assert data["status"] == "COMPLETED"
    assert "results_url" in data


def test_start_async_lineage_analysis(client: TestClient, auth_headers, mock_database):
    """Test starting async lineage analysis."""
    request_data = {
        "view_names": ["TEST_VIEW"],
        "async_processing": True
    }
    
    response = client.post(
        "/api/v1/lineage/analyze",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert "results_url" in data


def test_get_job_status(client: TestClient, auth_headers):
    """Test getting job status."""
    # First create a job
    request_data = {
        "view_names": ["TEST_VIEW"],
        "async_processing": True
    }
    
    create_response = client.post(
        "/api/v1/lineage/analyze",
        json=request_data,
        headers=auth_headers
    )
    
    job_id = create_response.json()["job_id"]
    
    # Then get its status
    response = client.get(
        f"/api/v1/lineage/status/{job_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["job_id"] == job_id
    assert "status" in data
    assert "created_at" in data


def test_get_job_status_not_found(client: TestClient, auth_headers):
    """Test getting status for non-existent job."""
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    
    response = client.get(
        f"/api/v1/lineage/status/{fake_job_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_list_available_views(client: TestClient, auth_headers, mock_database):
    """Test listing available views."""
    # Mock the database response
    mock_database.execute_query.return_value = [
        Mock(
            view_name="TEST_VIEW",
            schema_name="TEST_SCHEMA",
            database_name="TEST_DB",
            created_date=None,
            last_modified=None,
            column_count=5
        )
    ]
    
    response = client.get(
        "/api/v1/lineage/views",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    if data:  # If we have results
        assert "view_name" in data[0]
        assert "schema_name" in data[0]


def test_list_jobs(client: TestClient, auth_headers):
    """Test listing jobs."""
    response = client.get(
        "/api/v1/lineage/jobs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_unauthorized_access(client: TestClient):
    """Test unauthorized access to protected endpoints."""
    response = client.post("/api/v1/lineage/analyze", json={})
    assert response.status_code == 403  # No auth header


def test_invalid_request_data(client: TestClient, auth_headers):
    """Test invalid request data."""
    invalid_data = {
        "max_views": -1  # Invalid value
    }
    
    response = client.post(
        "/api/v1/lineage/analyze",
        json=invalid_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error