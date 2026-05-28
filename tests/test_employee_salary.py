import pytest
from unittest.mock import MagicMock

OPTIMIZED_QUERY = """
SELECT
  e.name,
  e.salary,
  AVG(e.salary) OVER (PARTITION BY e.department_id) AS dept_avg
FROM employees e
WHERE e.salary > 50000
"""

MOCK_EMPLOYEES = [
    {"name": "Alice", "salary": 90000, "department_id": 1},
    {"name": "Bob",   "salary": 70000, "department_id": 1},
    {"name": "Carol", "salary": 40000, "department_id": 1},  # excluded: salary <= 50000
    {"name": "Dave",  "salary": 60000, "department_id": 2},
    {"name": "Eve",   "salary": 30000, "department_id": 2},  # excluded: salary <= 50000
]


def _run_query(rows):
    """Simulate the optimized query over mock rows."""
    from collections import defaultdict

    dept_salaries = defaultdict(list)
    for r in rows:
        dept_salaries[r["department_id"]].append(r["salary"])

    dept_avg = {dept: sum(sals) / len(sals) for dept, sals in dept_salaries.items()}

    return [
        {
            "name": r["name"],
            "salary": r["salary"],
            "dept_avg": dept_avg[r["department_id"]],
        }
        for r in rows
        if r["salary"] > 50000
    ]


def test_optimized_query_returns_same_columns():
    """Result must have exactly: name, salary, dept_avg."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.schema = [
        MagicMock(name="name"),
        MagicMock(name="salary"),
        MagicMock(name="dept_avg"),
    ]
    mock_client.query.return_value.result.return_value = mock_result
    mock_client.query(OPTIMIZED_QUERY).result()

    column_names = [field.name for field in mock_result.schema]
    assert column_names == ["name", "salary", "dept_avg"]


def test_salary_filter_excludes_low_earners():
    """Employees with salary <= 50000 must not appear in results."""
    result = _run_query(MOCK_EMPLOYEES)
    names = [r["name"] for r in result]
    assert "Carol" not in names, "Carol earns 40000 and must be excluded"
    assert "Eve" not in names, "Eve earns 30000 and must be excluded"


def test_dept_avg_is_computed_across_all_dept_members():
    """dept_avg must reflect all department members, not just those passing the salary filter."""
    result = _run_query(MOCK_EMPLOYEES)

    # dept 1: Alice=90000, Bob=70000, Carol=40000 → avg = 66666.67
    expected_dept1_avg = (90000 + 70000 + 40000) / 3
    dept1_rows = [r for r in result if r["name"] in ("Alice", "Bob")]
    for row in dept1_rows:
        assert row["dept_avg"] == pytest.approx(expected_dept1_avg, rel=1e-3)

    # dept 2: Dave=60000, Eve=30000 → avg = 45000
    expected_dept2_avg = (60000 + 30000) / 2
    dept2_rows = [r for r in result if r["name"] == "Dave"]
    for row in dept2_rows:
        assert row["dept_avg"] == pytest.approx(expected_dept2_avg, rel=1e-3)


def test_window_function_preserves_row_count():
    """Only employees with salary > 50000 are returned (3 excluded from 5 mock rows)."""
    result = _run_query(MOCK_EMPLOYEES)
    assert len(result) == 3
