import sqlite3 as sql
from datetime import datetime
conn = sql.connect('Trader.db')
c = conn.cursor()

replace = ['(',')',',','./data/','csv','.','[',']']
replace_number = ['(',')',',','[',']']

def clean_up_sql_out(text,isnumber):
    if isnumber == 1:
        for s in replace_number:
            text = str(text).replace(s,'')      
    else:
        for s in replace:
            text = str(text).replace(s,'')
    return text

def sql_output(sql,printout,isnumber):
    c.execute(sql)
    result = c.fetchall()
    result = clean_up_sql_out(result,isnumber)
    print(f'{printout}{result}')

#Last Update
sql_output('select last_update from last_update order by last_update desc limit 1','Last  Update:',0)

#Datetimenow
datetimenow = datetime.now()
print(f"Datetime Now:'{datetimenow}'")

#Total Orders
sql_output('select count(*) from orders','Total Orders:',1)

#Profits
sql_output("""with sells as (select sum(price) as total from orders where market='SELL')
, buys as (select sum(price) as total from orders where market='BUY')
select case when (select total from sells) - (select total from buys) is NULL then 0 else (select total from sells) - (select total from buys)  end as profit
""",'Profit:',1)

#Last Run
last_run = """with headers as(select "Currency","Open","High","Low","Close","K","D","RSI","MACD","index","Time",1 as "order")
, data as (select Currency,Open,High,Low,Close,round("%K",2),round("%D",2),round(rsi,2),round(macd,2),"index",Time,2 from hourlydata order by "Index" DESC LIMIT 1)
, joined as (select * from headers
union 
select * from data)
select Currency,Open,High,Low,Close,K,D,RSI,MACD,"index",Time from joined order by "order" ASC"""
c.execute(last_run)
last_run = c.fetchall()
print('Last Run:')
for row in last_run:
    print(row)