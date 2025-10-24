WITH cross_items AS (
  SELECT
    i_item_sk AS ss_item_sk
  FROM item
  JOIN (
    SELECT
      iss.i_brand_id AS brand_id,
      iss.i_class_id AS class_id,
      iss.i_category_id AS category_id
    FROM store_sales
    JOIN item AS iss ON ss_item_sk = iss.i_item_sk
    JOIN date_dim AS d1 ON ss_sold_date_sk = d1.d_date_sk
    WHERE d1.d_year BETWEEN 1999 AND 1999 + 2
    INTERSECT
    SELECT
      ics.i_brand_id,
      ics.i_class_id,
      ics.i_category_id
    FROM catalog_sales
    JOIN item AS ics ON cs_item_sk = ics.i_item_sk
    JOIN date_dim AS d2 ON cs_sold_date_sk = d2.d_date_sk
    WHERE d2.d_year BETWEEN 1999 AND 1999 + 2
    INTERSECT
    SELECT
      iws.i_brand_id,
      iws.i_class_id,
      iws.i_category_id
    FROM web_sales
    JOIN item AS iws ON ws_item_sk = iws.i_item_sk
    JOIN date_dim AS d3 ON ws_sold_date_sk = d3.d_date_sk
    WHERE d3.d_year BETWEEN 1999 AND 1999 + 2
  ) AS subquery
  ON item.i_brand_id = subquery.brand_id AND item.i_class_id = subquery.class_id AND item.i_category_id = subquery.category_id
), avg_sales AS (
  SELECT
    AVG(quantity * list_price) AS average_sales
  FROM (
    SELECT
      ss_quantity AS quantity,
      ss_list_price AS list_price
    FROM store_sales
    JOIN date_dim ON ss_sold_date_sk = d_date_sk
    WHERE d_year BETWEEN 1999 AND 1999 + 2
    UNION ALL
    SELECT
      cs_quantity AS quantity,
      cs_list_price AS list_price
    FROM catalog_sales
    JOIN date_dim ON cs_sold_date_sk = d_date_sk
    WHERE d_year BETWEEN 1999 AND 1999 + 2
    UNION ALL
    SELECT
      ws_quantity AS quantity,
      ws_list_price AS list_price
    FROM web_sales
    JOIN date_dim ON ws_sold_date_sk = d_date_sk
    WHERE d_year BETWEEN 1999 AND 1999 + 2
  ) AS x
)
SELECT
  channel,
  i_brand_id,
  i_class_id,
  i_category_id,
  SUM(sales),
  SUM(number_sales)
FROM (
  SELECT
    'store' AS channel,
    i_brand_id,
    i_class_id,
    i_category_id,
    SUM(ss_quantity * ss_list_price) AS sales,
    COUNT(*) AS number_sales
  FROM store_sales
  JOIN item ON ss_item_sk = i_item_sk
  JOIN date_dim ON ss_sold_date_sk = d_date_sk
  WHERE
    ss_item_sk IN (
      SELECT
        ss_item_sk
      FROM cross_items
    )
    AND d_year = 1999 + 2
    AND d_moy = 11
  GROUP BY
    i_brand_id,
    i_class_id,
    i_category_id
  HAVING
    SUM(ss_quantity * ss_list_price) > (
      SELECT
        average_sales
      FROM avg_sales
    )
  UNION ALL
  SELECT
    'catalog' AS channel,
    i_brand_id,
    i_class_id,
    i_category_id,
    SUM(cs_quantity * cs_list_price) AS sales,
    COUNT(*) AS number_sales
  FROM catalog_sales
  JOIN item ON cs_item_sk = i_item_sk
  JOIN date_dim ON cs_sold_date_sk = d_date_sk
  WHERE
    cs_item_sk IN (
      SELECT
        ss_item_sk
      FROM cross_items
    )
    AND d_year = 1999 + 2
    AND d_moy = 11
  GROUP BY
    i_brand_id,
    i_class_id,
    i_category_id
  HAVING
    SUM(cs_quantity * cs_list_price) > (
      SELECT
        average_sales
      FROM avg_sales
    )
  UNION ALL
  SELECT
    'web' AS channel,
    i_brand_id,
    i_class_id,
    i_category_id,
    SUM(ws_quantity * ws_list_price) AS sales,
    COUNT(*) AS number_sales
  FROM web_sales
  JOIN item ON ws_item_sk = i_item_sk
  JOIN date_dim ON ws_sold_date_sk = d_date_sk
  WHERE
    ws_item_sk IN (
      SELECT
        ss_item_sk
      FROM cross_items
    )
    AND d_year = 1999 + 2
    AND d_moy = 11
  GROUP BY
    i_brand_id,
    i_class_id,
    i_category_id
  HAVING
    SUM(ws_quantity * ws_list_price) > (
      SELECT
        average_sales
      FROM avg_sales
    )
) AS y
GROUP BY
ROLLUP (
  channel,
  i_brand_id,
  i_class_id,
  i_category_id
)
ORDER BY
  channel,
  i_brand_id,
  i_class_id,
  i_category_id
LIMIT 100