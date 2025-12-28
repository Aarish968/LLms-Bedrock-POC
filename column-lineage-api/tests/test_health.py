"""Health check endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_basic_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data


def test_detailed_health_check(client: TestClient, mock_database):
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "services" in data
    assert "database" in data["services"]
    assert "system" in data["services"]


def test_readiness_check(client: TestClient, mock_database):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_liveness_check(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_check_database_failure(client: TestClient):
    """Test readiness check when database is down."""
    with pytest.patch('api.dependencies.database.DatabaseManager') as mock_db:
        mock_instance = mock_db.return_value
        mock_instance.test_connection.return_value = False
        
        response = client.get("/health/ready")
        assert response.status_code == 503