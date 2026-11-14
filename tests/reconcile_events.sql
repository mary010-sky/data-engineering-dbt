select 'unaccounted_events' as failure
where (select count(*) from {{ ref('raw_orders') }}) !=
 (select count(*) from {{ ref('fct_orders') }})+(select count(*) from {{ ref('quarantine') }})
