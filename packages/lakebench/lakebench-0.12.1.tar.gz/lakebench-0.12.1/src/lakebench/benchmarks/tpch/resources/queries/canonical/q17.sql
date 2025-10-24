SELECT
    SUM(l_extendedprice) / 7.0 AS avg_yearly
FROM
    lineitem
    INNER JOIN part ON p_partkey = l_partkey
WHERE
    p_brand = 'Brand#55'
    AND p_container = 'SM PACK'
    AND l_quantity < (
        SELECT
            0.2 * AVG(l_quantity)
        FROM
            lineitem
        WHERE
            l_partkey = p_partkey
    )