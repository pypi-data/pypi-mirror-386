WITH revenue0 AS (
    SELECT
        l_suppkey AS supplier_no,
        SUM(l_extendedprice * (1 - l_discount)) AS total_revenue
    FROM
        lineitem
    WHERE
        l_shipdate >= CAST('1995-03-01' AS DATE)
        AND l_shipdate < CAST('1995-06-01' AS DATE)
    GROUP BY
        l_suppkey
)
SELECT
    s_suppkey,
    s_name,
    s_address,
    s_phone,
    total_revenue
FROM
    supplier
    INNER JOIN revenue0 ON s_suppkey = supplier_no
WHERE
    total_revenue = (
        SELECT
            MAX(total_revenue)
        FROM
            revenue0
    )
ORDER BY
    s_suppkey