\pset null '(null)'
-- A: filter before projection; AND binds more tightly than OR.
SELECT id, title FROM tasks
WHERE status = 'todo' AND minutes >= 20 ORDER BY id;
-- B: a tie-breaker makes ordering total for this snapshot.
SELECT id, title FROM tasks ORDER BY minutes DESC, id ASC LIMIT 2 OFFSET 1;
-- C: inner join returns one row for each matching pair.
SELECT t.id, t.title, p.name AS project, u.login AS creator
FROM tasks AS t JOIN projects AS p ON p.id = t.project_id
JOIN users AS u ON u.id = t.created_by ORDER BY t.id;
-- D: preserve empty projects; count the non-NULL child key, not count(*).
SELECT p.name, count(t.id) AS task_count, coalesce(sum(t.minutes), 0) AS total
FROM projects AS p LEFT JOIN tasks AS t ON t.project_id = p.id
GROUP BY p.id, p.name ORDER BY p.id;
-- E: WHERE filters rows, HAVING filters groups.
SELECT project_id, sum(minutes) AS total FROM tasks
WHERE status <> 'done' GROUP BY project_id HAVING sum(minutes) >= 30
ORDER BY project_id;
-- F: NULL comparisons produce unknown, not true.
SELECT NULL = NULL AS equality, NULL IS NULL AS is_null;
SELECT id FROM tasks WHERE description IS NULL ORDER BY id;
-- G: put the child condition in ON to keep projects with no todo tasks.
SELECT p.name, count(t.id) AS todo_count
FROM projects AS p LEFT JOIN tasks AS t
ON t.project_id=p.id AND t.status='todo'
GROUP BY p.id, p.name ORDER BY p.id;
