SELECT
  customer_id,
  APPROX_COUNT_DISTINCT(order_id) AS orders,
  SUM(amount)                      AS total
FROM `project.dataset.orders`
WHERE created_at >= TIMESTAMP '2024-01-01'
GROUP BY customer_id
