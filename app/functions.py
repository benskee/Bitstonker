import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import create_engine


def remove_image(name):
    for filename in os.listdir('app/static/'):
        if filename.startswith(name):
            os.remove('app/static/' + filename)

def date_df(df):
    for date in range(len(df['date'])):
            df.loc[date, "date"] = datetime.strptime(df.loc[date, "date"], '%Y-%m-%d').date()

def get_stonk_df(stonk):
    api_key = os.environ['SECRET_KEY']
    stonk_alpha = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stonk}&outputsize=full&apikey={api_key}')
    this_df = stonk_alpha.json()
    df_stonk = pd.DataFrame.from_dict(this_df['Time Series (Daily)'],orient='index')
    df_stonk.reset_index(inplace=True)
    df_stonk.rename(columns={'index':'date', '5. adjusted close': 'stonk_close'}, inplace=True)
    df_stonk.drop(columns=['1. open', '2. high', '3. low', '4. close', '6. volume', '7. dividend amount','8. split coefficient'], axis=1, inplace=True)
    for num in ['stonk_close']:
        df_stonk[num] = df_stonk[num].astype(float, copy=True)
    date_df(df_stonk)
    df_stonk.set_index('date', inplace=True)
    return df_stonk

def stonk_start(df_1, df_2):
    df_1 = df_1.loc[df_1['date'] > df_2.index[len(df_2)-1]]
    df_1.reset_index(inplace=True)
    df_1.drop(columns=['index'], axis=1, inplace=True)
    return df_1

def generate_price(df_1):
    price_list = []
    for date in df_1.index:
        if date > 3 and np.isnan(df_1.stonk_close[date]) == True:
            for i in range(4):
                if np.isnan(df_1.stonk_close[date-i]) == False:
                    price = float(format(df_1.stonk_close[date-i]*10000/float(df_1.close_price[date]), '.8f'))
                    price_list.append(price)
                    break
                    
        elif df_1.stonk_close[date]:        
            price = float(format(df_1.stonk_close[date]*10000/float(df_1.close_price[date]), '.8f'))
            price_list.append(price)
    df_1['btc_price'] = price_list
    return df_1

def generate_stonk_price(df):
    stonk2_price_list = []
    for date in df.index:
        if df.stonk_close[date]:        
            stonk2_price = float(format(df.stonk_close[date]/df.stonk2_close[date], '.8f'))
            stonk2_price_list.append(stonk2_price)
    df['stonk2_price'] = stonk2_price_list
    return df

def validate_start_end(df, start_date, end_date):
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = df['date'][0]

    if not end_date:
        end_date = df['date'][len(df)-1]
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    if start_date < df['date'][0]:
        start_date = df['date'][0]

    if end_date > df['date'][len(df)-1]:
        end_date = df['date'][len(df)-1]

    start = df.loc[df['date'] == start_date].index[0]
    end = df.loc[df['date'] == end_date].index[0]  
    
    return (start, end)

def generate_dollar_graph(df, start, end, name, text_1, text_2, text_3):
    figure, ax1 = plt.subplots(figsize=(15, 12))
    plt.grid(True)
    ax1.plot(df.date[start:end+1], df[(f'{name}_price')][start:end+1].fillna(method='ffill'), label=text_3, color='orange')
    plt.title(text_1, fontsize=18)
    plt.ylabel(text_2, fontsize=16)
    ax2 = plt.twinx()
    ax2.set_ylabel(f'Price in Dollars', fontsize=16)
    ax2.plot(df.date[start:end+1], df.stonk_close[start:end+1].fillna(method='ffill'), label='Dollars', color='green')
    ax2.tick_params(axis='y')
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    lines = lines_1 + lines_2
    labels = labels_1 + labels_2
    ax1.legend(lines, labels, loc=2)
    graph = f'{name}_{str(datetime.now())[-5:]}.png'
    plt.savefig(f'app/static/{graph}');
    return graph

def generate_graph(df, start, end, name, text_1, text_2, text_3):
    plt.subplots(figsize=(15, 12))
    plt.grid(True)
    plt.plot(df.date[start:end+1], df[(f'{name}_price')][start:end+1].fillna(method='ffill'), color='orange')
    plt.title(text_1, fontsize=18)
    plt.ylabel(text_2, fontsize=16)
    plt.legend([text_3], loc=2, fontsize=12)
    graph = f'{name}_{str(datetime.now())[-5:]}.png'
    plt.savefig(f'app/static/{graph}');
    return graph

def adjust_start(df, start):
    adj_start = 0
    for day in range(1, len(df)-1):
        if np.isnan(df.stonk_close[start + adj_start]) == True:
            adj_start += 1
        else:
            break
    return start + adj_start

def adjust_end(df, end):
    adj_end = 0
    for day in range(1, len(df)-1):
        if np.isnan(df.stonk_close[end - adj_end]) == True:
            adj_end += 1
        else:
            break
    return end - adj_end

def rnd(entry):
    return (round(entry, 2))

def create_df_btc():
    SQL_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    cnx = create_engine(SQL_URI)
    conn = cnx.connect()
    df_btc = pd.read_sql_table('user', cnx)
    conn.close()
    cnx.dispose()
    df_btc.rename(columns={'price':'close_price'}, inplace=True)
    date_df(df_btc)
    df_btc.set_index('date', inplace=True)
    return df_btc

def check_stonks(stonk1, stonk2):
    if not stonk1 and not stonk2:
        stonk1 = "COKE"
        stonk2 = "PEP"

    elif not stonk1:
        stonk1="SPY"

    elif not stonk2:
        stonk2="GBTC"
    return (stonk1, stonk2)

