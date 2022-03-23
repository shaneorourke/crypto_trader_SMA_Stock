from binance import Client
import pandas as pd
import ta
from datetime import datetime
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')

client = Client("","")

lags = config.get('DEFAULT','lags') # 5 lags is good, up for testing e.g. 25 NOT in live use 3-5 lags

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

def wait_trigger(trigger,kline,dline,rsi,macd):
    if trigger == '' and kline < 20 and dline < 20 and rsi > 50 and macd > 0: #wait for the signals to hit
        return True
    else:
        return False

def buy_trigger(trigger,kline,dline):
    if trigger == 'Preparing for BUY' and kline > 20 and dline > 20:#once signals are set above then wait for these for a buy
        return True
    else:
        False

def strategy(pair):
    df = gethourlydata(pair)
    applytechnicals(df)
    kline = df['%K'].iloc[-1]
    dline = df['%D'].iloc[-1]
    rsi = df.rsi.iloc[-1]
    macd = df.macd.iloc[-1]
    trigger=f''
    if wait_trigger(trigger,kline,dline,rsi,macd): #wait for the signals to hit
        trigger=f'Prepare for BUY'
    print(f'Currency:{pair}')
    print(f'Trigger:{trigger}')
    print()


coinlist = ('BTCUSDT','ETHUSDT','LTCUSDT','ADAUSDT','XRPUSDT','SOLUSDT','BNBUSDT','DOTUSDT','BATUSDT','RUNEUSDT')
    
for coin in coinlist:    
    strategy(coin)
