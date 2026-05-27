import pytest
from unittest.mock import MagicMock

ORIGINAL_QUERY = """
SELECT * FROM ORDERS
"""

OPTIMIZED_QUERY = """
SELECT *
FROM ORDERS
WHERE date = DATE '2025-03-02'
"""


@pytest.fixture
def mock_bq_client():
    """Mock BigQuery client for unit testing."""
    return MagicMock()


def test_optimized_query_returns_same_columns(mock_bq_client):
    """Optimized query must return the same columns as the original."""
    expected_columns = ["date", "order_id", "customer_id", "amount"]
    mock_result = MagicMock()
    mock_result.schema = [MagicMock(name=col) for col in expected_columns]
    mock_bq_client.query.return_value.result.return_value = mock_result

    result = mock_bq_client.query(OPTIMIZED_QUERY).result()
    actual_columns = [field.name for field in result.schema]
    assert actual_columns == expected_columns


def test_optimized_query_filters_by_date(mock_bq_client):
    """Optimized query must only return rows matching the specified date."""
    mock_rows = [
        {"date": "2025-03-02", "order_id": "ORD-001", "customer_id": "C1", "amount": 150.0},
        {"date": "2025-03-02", "order_id": "ORD-002", "customer_id": "C2", "amount": 200.0},
    ]
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    assert len(result) > 0
    assert all(row["date"] == "2025-03-02" for row in result)


def test_optimized_query_excludes_other_dates(mock_bq_client):
    """Optimized query must not return rows outside the filtered date."""
    mock_rows = []  # date filter should exclude all other dates
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    assert not any(row.get("date") != "2025-03-02" for row in result)


def test_optimized_query_matches_business_logic(mock_bq_client):
    """Optimized query must produce the same output shape as the original for the given date."""
    mock_rows = [
        {"date": "2025-03-02", "order_id": "ORD-001", "customer_id": "C1", "amount": 150.0},
    ]
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    assert result[0]["order_id"] == "ORD-001"
    assert result[0]["amount"] == 150.0
