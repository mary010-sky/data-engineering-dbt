select 'revenue_mismatch' as failure
where (select sum(revenue) from {{ ref('fct_orders') }}) != (select sum(revenue) from {{ ref('daily_sales') }})
or (select sum(revenue) from {{ ref('fct_orders') }}) != (select sum(revenue) from {{ ref('market_sales') }})
