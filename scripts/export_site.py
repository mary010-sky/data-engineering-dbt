"""Publish validated pipeline output; independently reconcile seeded input in cents."""
import csv,json
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parents[1]
def main():
    db=duckdb.connect(str(ROOT/'warehouse/retail.duckdb'),read_only=True)
    def rows(sql):
        cursor=db.execute(sql)
        return [dict(zip([c[0] for c in cursor.description],r)) for r in cursor.fetchall()]
    def scalar(sql):return db.execute(sql).fetchone()[0]
    raw=list(csv.DictReader((ROOT/'seeds/raw_orders.csv').open(encoding='utf-8')))
    latest={}
    for r in raw:
        if r['order_id'] not in latest or int(r['event_id'])>int(latest[r['order_id']]['event_id']):latest[r['order_id']]=r
    valid_customers={r['customer_id'] for r in csv.DictReader((ROOT/'seeds/customers.csv').open())}
    valid_products={r['product_id'] for r in csv.DictReader((ROOT/'seeds/products.csv').open())}
    expected_cents=0;expected_count=0
    for r in latest.values():
        try:
            datetime.strptime(r['order_date'],'%Y-%m-%d')
            q=int(r['quantity']);p=Decimal(r['unit_price'])
            if q<=0 or p<0 or r['customer_id'] not in valid_customers or r['product_id'] not in valid_products:continue
            expected_cents += int(p*100)*q;expected_count+=1
        except (ValueError,ArithmeticError):continue
    total=scalar('select sum(revenue) from fct_orders')
    assert total==Decimal(expected_cents)/100
    assert scalar('select count(*) from fct_orders')==expected_count==1000
    assert scalar('select count(*) from quarantine')==6
    run=json.loads((ROOT/'target/run_results.json').read_text(encoding='utf-8'))
    tests=[r for r in run['results'] if r['unique_id'].startswith('test.')]
    assert tests and all(t['status']=='pass' for t in tests)
    assert all(r['status'] in ('success','pass') for r in run['results'])
    validation={'status':'passed','input_events':len(raw),'accepted_orders':expected_count,'quarantined_events':6,'invalid_events':5,'superseded_events':1,'revenue_usd':str(total),'independent_expected_cents':expected_cents,'dbt_tests':len(tests),'dbt_tests_passed':sum(t['status']=='pass' for t in tests),'dbt_nodes':len(run['results']),'duckdb_version':duckdb.__version__,'generated_at':datetime.now(timezone.utc).isoformat()}
    payload={'validation':validation,'markets':rows('select * from market_sales order by revenue desc'),'daily':rows('select * from daily_sales order by order_date'),'quarantine':rows('select event_id,order_id,disposition from quarantine order by event_id')}
    out=ROOT/'site/data';out.mkdir(parents=True,exist_ok=True)
    (out/'pipeline.json').write_text(json.dumps(payload,default=str,indent=2),encoding='utf-8')
    (ROOT/'evidence').mkdir(exist_ok=True)
    (ROOT/'evidence/pipeline-validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    for table in ['daily_sales','market_sales','quarantine']:
        with (out/f'{table}.csv').open('w',newline='',encoding='utf-8') as f:
            data=rows(f'select * from {table}')
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print(json.dumps(validation,indent=2))
if __name__=='__main__':main()
