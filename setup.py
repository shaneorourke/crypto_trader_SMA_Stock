import sqlite3 as sql
conn = sql.connect('Trader.db')
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS orders (Currency text, quantity float, market text, price float, trigger text, market_date timestamp DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

c.execute('CREATE TABLE IF NOT EXISTS position (Currency text, position boolean, market_date timestamp DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

c.execute('CREATE TABLE IF NOT EXISTS trigger (Currency text, trigger text, market_date timestamp DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

c.execute('CREATE TABLE IF NOT EXISTS last_update (last_update timestamp DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

c.execute('CREATE TABLE IF NOT EXISTS logs (Currency text, position text, trigger text, close float, kline float, dline float, rsi float, macd float, quantity float, binance_buy boolean, lags integer, log_datetime timestamp DEFAULT CURRENT_TIMESTAMP)')
conn.commit()