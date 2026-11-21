-- Query 1 (JOIN): every order with product, category, and the user who entered it
SELECT o.order_id, o.order_date, o.customer_name,
       p.name AS product, c.name AS category,
       o.quantity, o.quantity * p.price AS total_price,
       u.username AS entered_by
FROM orders o
JOIN product  p ON o.product_id  = p.product_id
JOIN category c ON p.category_id = c.category_id
JOIN users    u ON o.user_id     = u.user_id
ORDER BY o.order_date;

-- Query 2 (GROUP BY + ORDER BY): product count, average price and total stock per category
SELECT c.name AS category,
       COUNT(p.product_id)        AS product_count,
       ROUND(AVG(p.price), 2)     AS avg_price,
       SUM(p.stock)               AS total_stock
FROM category c
LEFT JOIN product p ON p.category_id = c.category_id
GROUP BY c.name
ORDER BY product_count DESC, avg_price DESC;

-- Query 3 (Subquery): products that have never been ordered (candidates for a discount)
SELECT p.product_id, p.name, p.price, p.stock
FROM product p
WHERE p.product_id NOT IN (SELECT o.product_id FROM orders o)
ORDER BY p.price DESC;
