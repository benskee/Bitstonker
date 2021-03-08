import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from flask import render_template, flash
from app import app

def date_df(df):
    for date in range(len(df['date'])):
            df.loc[date, "date"] = datetime.strptime(df.loc[date, "date"], '%Y-%m-%d').date()

def get_stonk_df(stonk):
    api_key = os.environ['SECRET_KEY']
    stonk_alpha = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stonk}&outputsize=full&apikey={api_key}')
    this_df = stonk_alpha.json()
    if 'Error Message' in this_df:
        return this_df
    df_stonk = pd.DataFrame.from_dict(this_df['Time Series (Daily)'],orient='index')
    df_stonk.reset_index(inplace=True)
    df_stonk.rename(columns={'index':'date', '5. adjusted close': 'stonk_close'}, inplace=True)
    df_stonk.drop(columns=['1. open', '2. high', '3. low', '4. close', '6. volume', '7. dividend amount','8. split coefficient'], axis=1, inplace=True)
    for num in ['stonk_close']:
        df_stonk[num] = df_stonk[num].astype(float, copy=True)
    date_df(df_stonk)
    df_stonk.set_index('date', inplace=True)
    return df_stonk

def stonk_error(stonk):
    api_key = os.environ['SECRET_KEY']
    error_alpha = requests.get(f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={stonk}&apikey={api_key}' )
    this_error = error_alpha.json()
    if len(this_error["bestMatches"]) < 1:
        flash(f'{stonk} is not a recognized ticker.')
    else:
        guess = this_error["bestMatches"][0]["1. symbol"]
        flash(f"{stonk} is not a recognized ticker. Did you mean {guess}?")
    context= dict(graph="basic.png", graph_display="none")
    return context

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
    if len(df.loc[df['date'] == start_date].index) < 1:
        for i in range(4):
            if len(df.loc[df['date'] == start_date + timedelta(days = i)].index) > 0:
                start_date = start_date + timedelta(days = i)
                break
    if len(df.loc[df['date'] == start_date].index) < 1:
        start = end = ""
        return (start,end)
    
    start = df.loc[df['date'] == start_date].index[0]

    if len(df.loc[df['date'] == end_date].index) < 1:
        for i in range(4):
            if len(df.loc[df['date'] == end_date - timedelta(days = i)].index) > 0:
                end_date = end_date - timedelta(days = i)
                break

    if len(df.loc[df['date'] == end_date].index) < 1:
        start = end = ""
        return (start,end)

    end = df.loc[df['date'] == end_date].index[0]
    return (start, end)

def date_error():
    flash(f"Invalid dates. Please try again.")
    context= dict(graph="basic.png", graph_display="none")
    return context

def remove_image(name):
    for filename in os.listdir('app/static/'):
        if filename.startswith(name):
            os.remove('app/static/' + filename)

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

def populate_table(df, start, end):
    usd_start_price = rnd(df.stonk_close[start])
    btc_start_price = rnd(df.btc_price[start])
    usd_end_price = rnd(df.stonk_close[end])
    btc_end_price = rnd(df.btc_price[end])
    usd_roi = rnd(usd_end_price - usd_start_price)
    btc_roi = rnd(btc_end_price - btc_start_price)
    usd_roi_pct = "{0:.2%}".format(usd_roi/usd_start_price)
    btc_roi_pct = "{0:.2%}".format(btc_roi/btc_start_price)

    context_b = dict(usd_start_price = usd_start_price, btc_start_price = btc_start_price,
    usd_end_price = usd_end_price, btc_end_price = btc_end_price, usd_roi = usd_roi, 
    btc_roi = btc_roi, usd_roi_pct = usd_roi_pct, btc_roi_pct = btc_roi_pct, graph_display="block")
    return context_b

def check_stonks(stonk1, stonk2):
    if not stonk1 and not stonk2:
        stonk1 = "COKE"
        stonk2 = "PEP"

    elif not stonk1:
        stonk1="SPY"

    elif not stonk2:
        stonk2="GBTC"
    return (stonk1, stonk2)

def generate_stonk_price(df):
    stonk2_price_list = []
    for date in df.index:
        if df.stonk_close[date]:        
            stonk2_price = float(format(df.stonk_close[date]/df.stonk2_close[date], '.8f'))
            stonk2_price_list.append(stonk2_price)
    df['stonk2_price'] = stonk2_price_list
    return df

def combine_stonks(df_stonk, df_stonk2):
    df_stonk2.rename(columns={'stonk_close': 'stonk2_close'}, inplace=True)
    df_stonk2['stonk_close'] = df_stonk['stonk_close']
    df_stonk2 = df_stonk2.sort_index(ascending=True, axis=0)
    df_stonk2.reset_index(inplace=True)
    generate_stonk_price(df_stonk2)
    return df_stonk2

def s2s_populate_table(df_stonk2, start, end):
    stonk1_start_price = rnd(df_stonk2.stonk_close[start])
    stonk1_end_price = rnd(df_stonk2.stonk_close[end])
    stonk1_roi = rnd(stonk1_end_price - stonk1_start_price)
    stonk1_roi_pct = "{0:.2%}".format(stonk1_roi/stonk1_start_price)
    stonk2_start_price = rnd(df_stonk2.stonk2_close[start])
    stonk2_end_price = rnd(df_stonk2.stonk2_close[end])
    stonk2_roi = rnd(stonk2_end_price - stonk2_start_price)
    stonk2_roi_pct = "{0:.2%}".format(stonk2_roi/stonk2_start_price)
    start_price = rnd(df_stonk2.stonk2_price[start])
    end_price = rnd(df_stonk2.stonk2_price[end])
    roi = rnd(end_price - start_price)
    roi_pct = "{0:.2%}".format((df_stonk2.stonk2_price[end] - df_stonk2.stonk2_price[start])/df_stonk2.stonk2_price[start])

    context_b = dict(graph_display="block", stonk1_start_price=stonk1_start_price, 
    stonk1_end_price=stonk1_end_price, stonk1_roi=stonk1_roi, stonk1_roi_pct=stonk1_roi_pct, 
    stonk2_start_price=stonk2_start_price, stonk2_end_price=stonk2_end_price,
    stonk2_roi=stonk2_roi, stonk2_roi_pct=stonk2_roi_pct, start_price=start_price, 
    end_price=end_price, roi=roi, roi_pct=roi_pct)

    return context_b

def previous5():
    df_btc = create_df_btc()
    last5 = df_btc[-5:]
    last5.reset_index(inplace=True)
    context = {}
    for row in range(0,5):
        context[f'date{row}']=last5.date[row]
        context[f'price{row}']=last5.close_price[row]
        
    return context
