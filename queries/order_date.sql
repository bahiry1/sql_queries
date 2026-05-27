-- Optimized: added date filter to reduce full table scan
SELECT *
FROM ORDERS
WHERE date = DATE '2025-03-02'
