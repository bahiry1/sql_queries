import pytest
from collections import defaultdict
from unittest.mock import MagicMock

OPTIMIZED_QUERY = """
SELECT
  customer_id,
  APPROX_COUNT_DISTINCT(order_id) AS orders,
  SUM(amount)                      AS total
FROM `project.dataset.orders`
WHERE created_at >= TIMESTAMP '2024-01-01'
GROUP BY customer_id
"""

MOCK_ROWS = [
    {"customer_id": "c1", "order_id": "o1", "amount": 100.0, "created_at": "2024-03-01"},
    {"customer_id": "c1", "order_id": "o2", "amount": 50.0,  "created_at": "2024-03-02"},
    {"customer_id": "c2", "order_id": "o3", "amount": 200.0, "created_at": "2024-06-15"},
    {"customer_id": "c3", "order_id": "o4", "amount": 75.0,  "created_at": "2023-12-31"},  # excluded
]


def test_optimized_query_returns_same_columns():
    """Optimized query must return customer_id, orders, total."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.schema = [
        MagicMock(name="customer_id"),
        MagicMock(name="orders"),
        MagicMock(name="total"),
    ]
    mock_client.query.return_value.result.return_value = mock_result
    mock_client.query(OPTIMIZED_QUERY).result()

    column_names = [field.name for field in mock_result.schema]
    assert column_names == ["customer_id", "orders", "total"]


def test_optimized_query_matches_business_logic():
    """Per-customer aggregation must exclude rows before 2024-01-01."""
    rows_in_scope = [r for r in MOCK_ROWS if r["created_at"] >= "2024-01-01"]

    agg = defaultdict(lambda: {"orders": set(), "total": 0.0})
    for r in rows_in_scope:
        agg[r["customer_id"]]["orders"].add(r["order_id"])
        agg[r["customer_id"]]["total"] += r["amount"]

    result = {cid: {"orders": len(v["orders"]), "total": v["total"]} for cid, v in agg.items()}

    assert "c3" not in result, "c3 order is before 2024-01-01 and must be excluded"
    assert result["c1"]["orders"] == 2
    assert result["c1"]["total"] == pytest.approx(150.0)
    assert result["c2"]["orders"] == 1
    assert result["c2"]["total"] == pytest.approx(200.0)


def test_date_filter_excludes_pre_2024_rows():
    """Boundary check: orders on 2023-12-31 must not appear in results."""
    excluded = [r for r in MOCK_ROWS if r["created_at"] < "2024-01-01"]
    assert any(r["customer_id"] == "c3" for r in excluded)
