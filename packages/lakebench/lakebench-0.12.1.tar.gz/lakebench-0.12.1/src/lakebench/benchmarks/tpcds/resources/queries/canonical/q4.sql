WITH year_total AS (
  SELECT
    c_customer_id AS customer_id,
    c_first_name AS customer_first_name,
    c_last_name AS customer_last_name,
    c_preferred_cust_flag AS customer_preferred_cust_flag,
    c_birth_country AS customer_birth_country,
    c_login AS customer_login,
    c_email_address AS customer_email_address,
    d_year AS dyear,
    SUM(
      (
        (
          ss_ext_list_price - ss_ext_wholesale_cost - ss_ext_discount_amt
        ) + ss_ext_sales_price
      ) / 2
    ) AS year_total,
    's' AS sale_type
  FROM customer
  JOIN store_sales ON c_customer_sk = ss_customer_sk
  JOIN date_dim ON ss_sold_date_sk = d_date_sk
  GROUP BY
    c_customer_id,
    c_first_name,
    c_last_name,
    c_preferred_cust_flag,
    c_birth_country,
    c_login,
    c_email_address,
    d_year
  UNION ALL
  SELECT
    c_customer_id AS customer_id,
    c_first_name AS customer_first_name,
    c_last_name AS customer_last_name,
    c_preferred_cust_flag AS customer_preferred_cust_flag,
    c_birth_country AS customer_birth_country,
    c_login AS customer_login,
    c_email_address AS customer_email_address,
    d_year AS dyear,
    SUM(
      (
        (
          (
            cs_ext_list_price - cs_ext_wholesale_cost - cs_ext_discount_amt
          ) + cs_ext_sales_price
        ) / 2
      )
    ) AS year_total,
    'c' AS sale_type
  FROM customer
  JOIN catalog_sales ON c_customer_sk = cs_bill_customer_sk
  JOIN date_dim ON cs_sold_date_sk = d_date_sk
  GROUP BY
    c_customer_id,
    c_first_name,
    c_last_name,
    c_preferred_cust_flag,
    c_birth_country,
    c_login,
    c_email_address,
    d_year
  UNION ALL
  SELECT
    c_customer_id AS customer_id,
    c_first_name AS customer_first_name,
    c_last_name AS customer_last_name,
    c_preferred_cust_flag AS customer_preferred_cust_flag,
    c_birth_country AS customer_birth_country,
    c_login AS customer_login,
    c_email_address AS customer_email_address,
    d_year AS dyear,
    SUM(
      (
        (
          (
            ws_ext_list_price - ws_ext_wholesale_cost - ws_ext_discount_amt
          ) + ws_ext_sales_price
        ) / 2
      )
    ) AS year_total,
    'w' AS sale_type
  FROM customer
  JOIN web_sales ON c_customer_sk = ws_bill_customer_sk
  JOIN date_dim ON ws_sold_date_sk = d_date_sk
  GROUP BY
    c_customer_id,
    c_first_name,
    c_last_name,
    c_preferred_cust_flag,
    c_birth_country,
    c_login,
    c_email_address,
    d_year
)
SELECT
  t_s_secyear.customer_id,
  t_s_secyear.customer_first_name,
  t_s_secyear.customer_last_name,
  t_s_secyear.customer_preferred_cust_flag
FROM year_total AS t_s_firstyear
JOIN year_total AS t_s_secyear ON t_s_secyear.customer_id = t_s_firstyear.customer_id
JOIN year_total AS t_c_firstyear ON t_s_firstyear.customer_id = t_c_firstyear.customer_id
JOIN year_total AS t_c_secyear ON t_s_firstyear.customer_id = t_c_secyear.customer_id
JOIN year_total AS t_w_firstyear ON t_s_firstyear.customer_id = t_w_firstyear.customer_id
JOIN year_total AS t_w_secyear ON t_s_firstyear.customer_id = t_w_secyear.customer_id
WHERE
  t_s_firstyear.sale_type = 's'
  AND t_c_firstyear.sale_type = 'c'
  AND t_w_firstyear.sale_type = 'w'
  AND t_s_secyear.sale_type = 's'
  AND t_c_secyear.sale_type = 'c'
  AND t_w_secyear.sale_type = 'w'
  AND t_s_firstyear.dyear = 2001
  AND t_s_secyear.dyear = 2001 + 1
  AND t_c_firstyear.dyear = 2001
  AND t_c_secyear.dyear = 2001 + 1
  AND t_w_firstyear.dyear = 2001
  AND t_w_secyear.dyear = 2001 + 1
  AND t_s_firstyear.year_total > 0
  AND t_c_firstyear.year_total > 0
  AND t_w_firstyear.year_total > 0
  AND CASE
    WHEN t_c_firstyear.year_total > 0
    THEN t_c_secyear.year_total / t_c_firstyear.year_total
    ELSE NULL
  END > CASE
    WHEN t_s_firstyear.year_total > 0
    THEN t_s_secyear.year_total / t_s_firstyear.year_total
    ELSE NULL
  END
  AND CASE
    WHEN t_c_firstyear.year_total > 0
    THEN t_c_secyear.year_total / t_c_firstyear.year_total
    ELSE NULL
  END > CASE
    WHEN t_w_firstyear.year_total > 0
    THEN t_w_secyear.year_total / t_w_firstyear.year_total
    ELSE NULL
  END
ORDER BY
  t_s_secyear.customer_id,
  t_s_secyear.customer_first_name,
  t_s_secyear.customer_last_name,
  t_s_secyear.customer_preferred_cust_flag
LIMIT 100