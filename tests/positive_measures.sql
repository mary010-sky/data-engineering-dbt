select order_id from {{ ref('fct_orders') }} where quantity<=0 or revenue<0
