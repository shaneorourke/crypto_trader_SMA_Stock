import sqlite3 as sql
from datetime import datetime
from binance import Client
import binance_keys as bk
from rich.console import Console
from rich.theme import Theme

conn = sql.connect('Trader.db')
c = conn.cursor()

customer_theme = Theme({'info':"bold green italic",'integer':'blue bold','pos_warning':'yellow bold italic','neg_warning':'red bold'})
console = Console(color_system='auto',theme=customer_theme)

client = Client(api_key=bk.API_KEY,api_secret=bk.SECRET_KEY)

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


## Last Update
c.execute('SELECT last_update FROM last_update ORDER BY last_update DESC LIMIT 1')
result = c.fetchone()
result = clean_up_sql_out(result,0)
time_now = datetime.now()
console.print(f'[info]Last Update[/info][integer]:{result}[/integer]')
console.print(f'[info]Datetime Now[/info][integer]:{str(time_now)}[/integer]')

console.print()


c.execute('SELECT Currency FROM position')
currencies = c.fetchall()
for curr in currencies:
    curr=clean_up_sql_out(curr,0)
    curr=curr.replace("'","")

    console.print(f'[info]##### CURRENCY[/info][integer]:{curr}[/integer][info] #####[/info]')

    ## Last Buy Price
    c.execute(f'SELECT price FROM orders WHERE Currency="{curr}" and market = "BUY" ORDER BY market_date DESC limit 1')
    buy_price = c.fetchall()
    buy_price = clean_up_sql_out(buy_price,1)

    ## Made First Sale
    c.execute(f'SELECT count(*) FROM orders WHERE Currency="{curr}" and market = "SELL"')
    sale_made = c.fetchall()
    sale_made = clean_up_sql_out(sale_made,1)

    ## Position Open
    c.execute(f'SELECT position FROM position WHERE Currency="{curr}"')
    result = c.fetchall()
    pos = clean_up_sql_out(result,0)
    if pos == '0':
        position = 'BUYING'
    else:
        position = 'SELLING'
    console.print(f'[info]Position[/info][integer]:{position}[/integer]')
    if position == 'SELLING':
        console.print(f'[info]Buy Price[/info][integer]:{buy_price}[/integer]')

    ## Current Price
    price=client.get_symbol_ticker(symbol=curr)
    console.print(f'[info]Current Price[/info][integer]:{float(price["price"])}[/integer]')

    ## Profitability
    #c.execute(f"""with last_order as (select market, market_date from orders WHERE Currency="{curr}" ORDER BY market_date DESC LIMIT 1)
    #            , order_check as(select case when market = 'BUY' then (SELECT round(sum(case when market = "SELL" then price else price*-1 end),2) as profit FROM orders WHERE Currency="{curr}" and market_date != (SELECT market_date FROM last_order)) else (SELECT round(sum(case when market = "SELL" then price else price*-1 end),2) as profit FROM orders WHERE Currency="{curr}") end FROM last_order)
    #            select * from order_check""")
    #result = c.fetchall()
    curr_profit = clean_up_sql_out(result,1)
    #if sale_made !='0':
    #    if curr_profit != 'None':
    #        profit = round((float(curr_profit)/float(price['price']))*100,2)
    #        console.print(f'[info]Profit Percentage[/info][integer]:{profit}%[/integer]')
    #        qty = 0.001
    #        usdt_value = float(price['price']) * qty
    #        usdt_profit = usdt_value*(profit/100)
    #        console.print(f'[info]USDT Profit:$[/info][integer]{round(usdt_profit,2)}[/integer]')

    ## Take Profit Distance
    current_price = float(price['price'])
    c.execute(f'SELECT round({current_price}-round(price+(price * 0.01),2),2) FROM orders WHERE market = "BUY" ORDER BY market_date DESC LIMIT 1')
    result = c.fetchall()
    tp_dist = clean_up_sql_out(result,1)
    ## Take Profit Details Est
    c.execute('SELECT round(price+(price * 0.01),2) FROM orders WHERE market = "BUY" ORDER BY market_date DESC LIMIT 1')
    result = c.fetchall()
    if position == 'SELLING':
        tp = clean_up_sql_out(result,1)
        console.print(f'[info]Take Profit[/info][integer]:{tp} ({tp_dist})[/integer]')

    ## Stop Distnance Est
    current_price = float(price['price'])
    c.execute(f'SELECT round({current_price}-round(price-(price * 0.015),2),2) FROM orders WHERE market = "BUY" ORDER BY market_date DESC LIMIT 1')
    result = c.fetchall()
    stop_dist = clean_up_sql_out(result,1)
    ## Stop Details Est
    c.execute('SELECT round(price-(price * 0.015),2) FROM orders WHERE market = "BUY" ORDER BY market_date DESC LIMIT 1')
    result = c.fetchall()
    if position == 'SELLING':
        stop = clean_up_sql_out(result,1)
        console.print(f'[info]Stop Limit[/info][integer]:{stop} ({stop_dist})[/integer]')

    ## P and L
    if position == 'SELLING':
        PL = round(float(price['price']) - float(buy_price),2)
        console.print(f'[info]Profit & Loss[/info][integer]:{PL}[/integer]')

    ## Current Trade Profit
    if position == 'SELLING':
        current_trade_profit = round((PL / float(buy_price) ) * 100,2)
        console.print(f'[info]Current Trade Profit[/info][integer]:{current_trade_profit}%[/integer]')

    ## Current Trade USDT Profit
    if position == 'SELLING':
        c.execute(f'select quantity from orders where market = "BUY" order by market_date desc limit 1')
        result = c.fetchone()
        quantity = float(clean_up_sql_out(result,1))
        usdt_value = float(price['price']) * quantity
        usdt_profit = usdt_value*(current_trade_profit/100)
        console.print(f'[info]USDT Profit:$[/info][integer]{round(usdt_profit,2)}[/integer]')


    ## Take Profit Details Est
    c.execute('SELECT binance_buy FROM logs ORDER BY log_datetime DESC LIMIT 1')
    result = c.fetchall()
    binance_buy = clean_up_sql_out(result,0)
    if binance_buy == '0':
        binance_buy = False
    else:
        binance_buy = True
    console.print(f'[info]Binance Buy[/info][integer]:{binance_buy}[/integer]')

    console.print()
    
## Profitability
c.execute(f"""with last_order as (select market, market_date from orders ORDER BY market_date DESC LIMIT 1)
            , order_check as(select case when market = 'BUY' then (SELECT round(sum(case when market = "SELL" then price else price*-1 end),2) as profit FROM orders WHERE market_date != (SELECT market_date FROM last_order)) else (SELECT round(sum(case when market = "SELL" then price else price*-1 end),2) as profit FROM orders) end FROM last_order)
            select * from order_check""")
result = c.fetchall()
tot_profit = clean_up_sql_out(result,1)
if sale_made !='0':
    if tot_profit != 'None':
        total_profit = round((float(tot_profit)/float(price['price']))*100,2)
        console.print(f'[info]##### Total Profit Percentage[/info][integer]:{total_profit}%[/integer]')
        qty = 0.001
        usdt_value = float(price['price']) * qty
        usdt_profit = usdt_value*(total_profit/100)
        console.print(f'[info]Total USDT Profit:$[/info][integer]{round(usdt_profit,2)}[/integer]')

## Days Active
c.execute(f"select round(julianday('now') - JULIANDAY(min(log_datetime)),2) from logs")
result = c.fetchall()
days_active = clean_up_sql_out(result,1)
console.print(f'[info]Days Active:[/info][integer]{days_active}[/integer]')

## Winning Trades
c.execute(f"""with buys as (select Currency, Price, row_number() over (partition by Currency order by market_date ASC) as rownum from orders where market = 'BUY')
, sales as (select Currency, Price, row_number() over (partition by Currency order by market_date ASC) as rownum from orders where market = 'SELL')
, trades as (select buys.Currency, case when sales.Price - buys.Price <= 0 then 'loss' else 'win' end as win_loss from buys inner join sales on buys.Currency = sales.Currency and buys.rownum = sales.rownum)
select count(*) from trades where win_loss = 'win'""")
result = c.fetchall()
wins = clean_up_sql_out(result,1)
console.print(f'[info]Winning Trades:[/info][integer]{wins}[/integer]')

## Losing Trades
c.execute(f"""with buys as (select Currency, Price, row_number() over (partition by Currency order by market_date ASC) as rownum from orders where market = 'BUY')
, sales as (select Currency, Price, row_number() over (partition by Currency order by market_date ASC) as rownum from orders where market = 'SELL')
, trades as (select buys.Currency, case when sales.Price - buys.Price <= 0 then 'loss' else 'win' end as win_loss from buys inner join sales on buys.Currency = sales.Currency and buys.rownum = sales.rownum)
select count(*) from trades where win_loss = 'loss'""")
result = c.fetchall()
losses = clean_up_sql_out(result,1)
console.print(f'[info]Losing Trades:[/info][integer]{losses}[/integer]')
