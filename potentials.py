from binance import Client
import pandas as pd
import ta

client = Client("","")

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
    df['FastSMA'] = df.Close.rolling(7).mean()
    df['SlowSMA'] = df.Close.rolling(25).mean()
    df.dropna(inplace=True)

def wait_trigger_Stock_RSI_MACD(kline,dline,rsi,macd):
    if kline < 20 and dline < 20 and rsi > 50 and macd > 0: #wait for the signals to hit)
        return True
    else:
        return False

def Buy_Trigger_Fast_SMA_Bounce(FastSMA,SlowSMA,Close):
    if FastSMA > SlowSMA:
        if Close < SlowSMA:
            return True
        else:
            off_perc = round(((Close - SlowSMA) / Close * 100),2)
            print(f'Close off SlowSMA by:{off_perc}%')
            return False
    else:
        print('Downtrend')
        return False

def strategy(pair):
    print(f'Currency:{pair}')
    df = gethourlydata(pair)
    applytechnicals(df)
    kline = df['%K'].iloc[-1]
    dline = df['%D'].iloc[-1]
    rsi = df.rsi.iloc[-1]
    macd = df.macd.iloc[-1]
    Close = df.Close.iloc[-1]
    FastSMA = df.FastSMA.iloc[-1]
    SlowSMA = df.SlowSMA.iloc[-1]
    trigger1 = ''
    trigger2 = ''
    print(f'Close:{round(Close,2)}')
    if wait_trigger_Stock_RSI_MACD(kline,dline,rsi,macd): #wait for the signals to hit
        trigger1=f'Prepare for BUY - Stock RSI MACD'
    if Buy_Trigger_Fast_SMA_Bounce(FastSMA,SlowSMA,Close): #wait for the signals to hit
        trigger2=f'Prepare for BUY - Stock RSI MACD'

    print(f'Trigger Stoch RSI MACD:{trigger1}')
    print(f'Trigger Fast SMA Bounce:{trigger2}')
    print()


coinlist = ('BTCUSDT','ETHUSDT','LTCUSDT','ADAUSDT','XRPUSDT','SOLUSDT','BNBUSDT','DOTUSDT','BATUSDT','RUNEUSDT')
    
for coin in coinlist:    
    strategy(coin)
