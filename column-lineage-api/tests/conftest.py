"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.main import app
from api.core.config import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings fixture."""
    settings = get_settings()
    settings.DEBUG = True
    settings.JWT_SECRET_KEY = "test-secret-key"
    return settings


@pytest.fixture
def mock_database():
    """Mock database fixture."""
    with patch('api.dependencies.database.DatabaseManager') as mock_db:
        mock_instance = Mock()
        mock_instance.test_connection.return_value = True
        mock_instance.execute_query.return_value = []
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def auth_headers():
    """Authentication headers fixture."""
    # In a real test, you would generate a valid JWT token
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_view_ddl():
    """Sample view DDL for testing."""
    return """
    CREATE OR REPLACE VIEW TEST_VIEW AS
    SELECT 
        t1.column1,
        t1.column2,
        t2.column3 as renamed_column,
        SUM(t1.amount) as total_amount
    FROM table1 t1
    JOIN table2 t2 ON t1.id = t2.id
    GROUP BY t1.column1, t1.column2, t2.column3
    """


@pytest.fixture
def sample_lineage_results():
    """Sample lineage results for testing."""
    from api.v1.models.lineage import ColumnLineageResult, ColumnType
    
    return [
        ColumnLineageResult(
            view_name="TEST_VIEW",
            view_column="column1",
            column_type=ColumnType.DIRECT,
            source_table="table1",
            source_column="column1",
            confidence_score=1.0,
        ),
        ColumnLineageResult(
            view_name="TEST_VIEW",
            view_column="total_amount",
            column_type=ColumnType.DERIVED,
            source_table="table1",
            source_column="amount",
            confidence_score=0.8,
        ),
    ]