select market,count(*) as orders,sum(quantity) as units,
 cast(sum(revenue) as decimal(18,2)) as revenue
from {{ ref('fct_orders') }} group by market
