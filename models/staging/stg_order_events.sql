with typed as (
 select trim(order_id) as order_id, try_cast(order_date as date) as order_date,
 trim(customer_id) as customer_id, trim(product_id) as product_id,
 try_cast(quantity as integer) as quantity,
 try_cast(unit_price as decimal(12,2)) as unit_price, event_id
 from {{ ref('raw_orders') }}
), checked as (
 select t.*,
 case
 when order_id is null or order_id = '' then 'missing_order_id'
 when order_date is null then 'invalid_date'
 when quantity is null or quantity <= 0 then 'invalid_quantity'
 when unit_price is null or unit_price < 0 then 'invalid_price'
 when c.customer_id is null then 'unknown_customer'
 when p.product_id is null then 'unknown_product'
 else 'valid' end as quality_status
 from typed t
 left join {{ ref('customers') }} c on t.customer_id=c.customer_id
 left join {{ ref('products') }} p on t.product_id=p.product_id
), ranked as (
 select *,row_number() over(partition by order_id order by event_id desc) as event_rank
 from checked
)
select *,case when quality_status!='valid' then quality_status
 when event_rank>1 then 'superseded_event' else 'accepted' end as disposition
from ranked
