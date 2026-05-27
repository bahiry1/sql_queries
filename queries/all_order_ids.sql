-- Retrieves all order IDs from the Orders table.
-- WARNING: full table scan — activate the filter below for date-scoped runs.
SELECT order_id
FROM Orders
-- WHERE order_date >= DATE '2025-01-01'  -- recommended: enables partition/index pruning
ORDER BY order_id
