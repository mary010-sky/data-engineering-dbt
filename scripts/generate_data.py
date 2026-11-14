"""Deterministic educational inputs; deliberately malformed and duplicate events."""
import csv
from datetime import date,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def write(name,header,rows):
    with (ROOT/'seeds'/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
def main():
    (ROOT/'seeds').mkdir(exist_ok=True)
    (ROOT/'warehouse').mkdir(exist_ok=True)
    write('customers.csv',['customer_id','market'],[(f'C{i:03}', ['Peru','Chile','Colombia','Mexico'][i%4]) for i in range(1,21)])
    write('products.csv',['product_id','category'],[(f'P{i:03}',['Electronics','Home','Sports'][i%3]) for i in range(1,13)])
    rows=[]
    for i in range(1,1001):
        cents=500+(i*37)%9500
        rows.append([f'O{i:05}',str(date(2026,1,1)+timedelta(days=(i*13)%180)),f'C{1+i%20:03}',f'P{1+i%12:03}',1+i%5,f'{cents//100}.{cents%100:02}',i])
    rows += [rows[0][:-1]+[1001]]  # later event supersedes order O00001
    rows += [
      ['BAD01','not-a-date','C001','P001',1,'10.00',1002],
      ['BAD02','2026-01-01','C001','P001',-2,'10.00',1003],
      ['BAD03','2026-01-01','C001','P001',1,'',1004],
      ['BAD04','2026-01-01','UNKNOWN','P001',1,'10.00',1005],
      ['BAD05','2026-01-01','C001','UNKNOWN',1,'10.00',1006],
    ]
    write('raw_orders.csv',['order_id','order_date','customer_id','product_id','quantity','unit_price','event_id'],rows)
    print('Generated 1,006 events: 1,000 valid unique orders, 1 superseded event, 5 invalid events.')
if __name__=='__main__':main()
