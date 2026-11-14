select e.order_id,e.order_date,e.customer_id,e.product_id,e.quantity,e.unit_price,
 cast(e.quantity*e.unit_price as decimal(14,2)) as revenue,
 c.market,p.category
from {{ ref('stg_order_events') }} e
join {{ ref('customers') }} c using(customer_id)
join {{ ref('products') }} p using(product_id)
where e.disposition='accepted'
