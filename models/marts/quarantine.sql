select * from {{ ref('stg_order_events') }} where disposition!='accepted'
