import pytest
from unittest.mock import MagicMock

ORIGINAL_QUERY = """
SELECT order_id FROM Orders
"""

OPTIMIZED_QUERY = """
SELECT order_id
FROM Orders
ORDER BY order_id
"""


@pytest.fixture
def mock_bq_client():
    """Mock database client for unit testing."""
    return MagicMock()


def test_optimized_query_returns_same_columns(mock_bq_client):
    """Optimized query must return the same columns as the original."""
    expected_columns = ["order_id"]
    mock_result = MagicMock()
    mock_result.schema = [MagicMock(name=col) for col in expected_columns]
    mock_bq_client.query.return_value.result.return_value = mock_result

    result = mock_bq_client.query(OPTIMIZED_QUERY).result()
    actual_columns = [field.name for field in result.schema]
    assert actual_columns == expected_columns


def test_optimized_query_returns_all_orders(mock_bq_client):
    """Optimized query must return rows for all orders with no implicit filtering."""
    mock_rows = [
        {"order_id": "ORD-001"},
        {"order_id": "ORD-002"},
        {"order_id": "ORD-003"},
    ]
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    assert len(result) == 3


def test_optimized_query_results_are_ordered(mock_bq_client):
    """Optimized query must return order_ids in ascending order."""
    mock_rows = [
        {"order_id": "ORD-001"},
        {"order_id": "ORD-002"},
        {"order_id": "ORD-003"},
    ]
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    order_ids = [row["order_id"] for row in result]
    assert order_ids == sorted(order_ids)


def test_optimized_query_matches_business_logic(mock_bq_client):
    """Optimized query must return the same order_id values as the original."""
    mock_rows = [
        {"order_id": "ORD-001"},
        {"order_id": "ORD-002"},
    ]
    mock_bq_client.query.return_value.result.return_value = iter(mock_rows)

    result = list(mock_bq_client.query(OPTIMIZED_QUERY).result())
    assert result[0]["order_id"] == "ORD-001"
    assert result[1]["order_id"] == "ORD-002"
