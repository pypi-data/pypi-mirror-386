SELECT
  s_store_name,
  s_store_id,
  SUM(CASE WHEN (
    d_day_name = 'Sunday'
  ) THEN ss_sales_price ELSE NULL END) AS sun_sales,
  SUM(CASE WHEN (
    d_day_name = 'Monday'
  ) THEN ss_sales_price ELSE NULL END) AS mon_sales,
  SUM(CASE WHEN (
    d_day_name = 'Tuesday'
  ) THEN ss_sales_price ELSE NULL END) AS tue_sales,
  SUM(CASE WHEN (
    d_day_name = 'Wednesday'
  ) THEN ss_sales_price ELSE NULL END) AS wed_sales,
  SUM(CASE WHEN (
    d_day_name = 'Thursday'
  ) THEN ss_sales_price ELSE NULL END) AS thu_sales,
  SUM(CASE WHEN (
    d_day_name = 'Friday'
  ) THEN ss_sales_price ELSE NULL END) AS fri_sales,
  SUM(CASE WHEN (
    d_day_name = 'Saturday'
  ) THEN ss_sales_price ELSE NULL END) AS sat_sales
FROM date_dim
JOIN store_sales ON d_date_sk = ss_sold_date_sk
JOIN store ON s_store_sk = ss_store_sk
WHERE
  s_gmt_offset = -6
  AND d_year = 1999
GROUP BY
  s_store_name,
  s_store_id
ORDER BY
  s_store_name,
  s_store_id,
  sun_sales,
  mon_sales,
  tue_sales,
  wed_sales,
  thu_sales,
  fri_sales,
  sat_sales
LIMIT 100