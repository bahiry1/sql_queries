SELECT
  e.name,
  e.salary,
  AVG(e.salary) OVER (PARTITION BY e.department_id) AS dept_avg
FROM employees e
WHERE e.salary > 50000
