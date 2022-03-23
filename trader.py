from binance import Client
import binance_keys
import pandas as pd
import ta
import os
import sqlite3 as sql
from datetime import datetime
import csv
import time
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')

conn = sql.connect('Trader.db')
c = conn.cursor()

client = Client(binance_keys.API_KEY,binance_keys.SECRET_KEY)

binance_buy = config.get('DEFAULT','binance_buy')
lags = config.get('DEFAULT','lags') # 5 lags is good, up for testing e.g. 25 NOT in live use 3-5 lags
printout = config.get('DEFAULT','printout')

if binance_buy == 'True':
    binance_buy = True
else:
    binance_buy = False

if printout == 'True':
    printout = True
else:
    printout = False


today = datetime.now().date()
today = str(today).replace('-','')

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

def write_to_file(log_file_name,text):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_path = os.path.join('logs',today)
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    file_name = os.path.join(file_path,log_file_name)
    text = str(datetime.now()) + '||' + str(text)
    with open(f'{file_name}', 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow([text])
        f.close()

def get_usdt_holdings():
    usdt = client.get_asset_balance('USDT')
    return usdt['free']

def get_minimum_trade_amount(pair):
    filters = client.get_symbol_info(f'{pair}')["filters"]
    minimum_qty = 0
    for i in filters:
        if i["filterType"] == "LOT_SIZE":
            minimum_qty=i['minQty']
    return minimum_qty

def get_quantity(pair,close):
    usdt = float(get_usdt_holdings())
    qty = float(usdt) / float(close)
    minimum_qty = float(get_minimum_trade_amount(pair))
    if 'e-' in str(qty):
        qty = 0
    else:
        position_of_1 = str(minimum_qty).find('1',)
        minimum_qty = float(str(minimum_qty)[:position_of_1+1])

        usdt = float(str(usdt)[:position_of_1+1])
        qty = float(str(qty)[:position_of_1+1])
    return qty

def last_update():
    c.execute(f'DELETE FROM last_update')
    c.execute(f'INSERT INTO last_update VALUES("{datetime.now()}")')
    conn.commit()

def gethourlydata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol,'1h','50 hours ago UTC'))
    frame = frame.iloc[:,:5]
    frame.columns = ['Time','Open','High','Low','Close']
    frame[['Open','High','Low','Close']] = frame[['Open','High','Low','Close']].astype(float)
    frame.Time = pd.to_datetime(frame.Time, unit='ms')
    frame['Currency'] = symbol
    return frame

def applytechnicals(df):
    df['%K'] = ta.momentum.stoch(df.High,df.Low,df.Close,window=14,smooth_window=3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.Close,window=14)
    df['macd'] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)

def market_order(curr,qty,buy=True,binance_buy=False,price=float,trigger=str):
    log_datetime = datetime.now()
    error = 0
    if buy:
        side='BUY'
    else:
        side='SELL'
    if binance_buy:
        try:
            order = client.create_order(symbol=curr,side=side,type='MARKET',quantity=qty)
        except Exception as e:
            write_to_file(f'{curr}',f'{log_datetime}:Binance Error:{e}')
            error = 1
        buyprice = float(order['fills'][0]['price'])
        db_order = f'''INSERT INTO orders (Currency, quantity, market, price, trigger) 
                        VALUES("{curr}",{qty},"{side}",{buyprice},"{trigger}")'''
    else:
        db_order = f'''INSERT INTO orders (Currency, quantity, market, price, trigger) 
                        VALUES("{curr}",{qty},"{side}",{buyprice},"{trigger}")'''
    c.execute(db_order)
    conn.commit()
    return error

def update_position(pair,open=True):
    c.execute(f'UPDATE position SET position = {open} WHERE Currency = "{pair}"')
    conn.commit()

def get_position(pair):
    c.execute(f'SELECT position FROM position WHERE Currency = "{pair}" ORDER BY market_date DESC limit 1')
    pos = c.fetchone()
    pos = clean_up_sql_out(pos,0)
    if pos == 'None' or pos == None:
        c.execute(f'INSERT INTO position (Currency, position) VALUES ("{pair}",False)')
    conn.commit()
    return pos

def update_trigger(pair,trigger):
    c.execute(f'UPDATE trigger SET trigger = {trigger} WHERE Currency = "{pair}"')
    conn.commit()

def get_trigger(pair):
    c.execute(f'SELECT trigger FROM trigger WHERE Currency = "{pair}" ORDER BY market_date DESC limit 1')
    trig = c.fetchone()
    trig = clean_up_sql_out(trig,0)
    if trig == 'None' or trig == None:
        c.execute(f'INSERT INTO trigger VALUES ("{pair}","None",NULL)')
    conn.commit()
    return trig

def wait_trigger(position,trigger,kline,dline,rsi,macd):
    if (position == '0' or position == 0) and trigger == '' and kline < 20 and dline < 20 and rsi > 50 and macd > 0: #wait for the signals to hit
        return True
    else:
        return False

def buy_trigger(position,trigger,kline,dline):
    if (position == '0' or position == 0) and trigger == 'waiting' and kline > 20 and dline > 20:#once signals are set above then wait for these for a buy
        return True
    else:
        False

def sell_trigger(position,kline,dline):
    if (position == '1' or position == 1) and kline > 20 and dline > 20:#once signals are set above then wait for these for a buy
        return True
    else:
        False

def insert_log(Currency,position,trigger,close,kline,dline,rsi,macd,quantity,binance_buy,lags,printout=False):
    c.execute(f'''INSERT INTO logs (Currency,position,trigger,close,kline,dline,rsi,macd,quantity,binance_buy,lags) 
                VALUES ("{Currency}","{position}","{trigger}",{close},{kline},{dline},{rsi},{macd},{quantity},{binance_buy},{lags})''')
    conn.commit()
    if printout:
        print(f'Currency:{Currency}')
        print(f'position:{position}')
        print(f'Trigger:{trigger}')
        print(f'Close:{round(close,2)}')
        print(f'Kline:{round(kline,2)}')
        print(f'Dline:{round(dline,2)}')
        print(f'RSI:{round(rsi,2)}')
        print(f'MACD:{round(macd,2)}')
        print(f'Quantity:{round(quantity,2)}')
        print(f'binance_buy:{binance_buy}')
        print(f'Lags:{lags}')
        print()

def strategy(pair,binance_buy,printout):
    position = get_position(pair)
    trigger = get_trigger(pair)
    if trigger == 'None' or trigger == None:
        trigger = ''
    df = gethourlydata(pair)
    applytechnicals(df)
    df.to_sql(con=conn,name='hourlydata',if_exists='append')
    conn.commit()
    close = df.Close.iloc[-1]
    kline = df['%K'].iloc[-1]
    dline = df['%D'].iloc[-1]
    rsi = df.rsi.iloc[-1]
    macd = df.macd.iloc[-1]
    qty = float(get_quantity(pair,close))
    if qty == 0:
        binance_buy = False
    if wait_trigger(position,trigger,kline,dline,rsi,macd): #wait for the signals to hit
        update_trigger(pair,'waiting')
    if buy_trigger(position,trigger,kline,dline): #once signals are set above then wait for these for a buy
        error = market_order(pair,qty,True,binance_buy,df.close,'')
        if error != 1:
            update_position(pair,True)
    if sell_trigger(position,kline,dline):
        error = market_order(pair,qty,False,binance_buy,df.close,'')
        if error != 1:
            update_position(pair,False)
            update_trigger(pair,'')
    insert_log(pair,position,trigger,close,kline,dline,rsi,macd,qty,binance_buy,lags,printout)

strategy('BTCUSDT',binance_buy,printout)

