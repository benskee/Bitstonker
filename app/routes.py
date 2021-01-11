from . import app
from flask import render_template, request, redirect
import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        stonk = ""
        df_btc = ""
        graph = ""
        graph_display = "none"
        
        

    if request.method == "POST":
        stonk = request.form.get('stonk').upper()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        graph_display = "block"

        if not stonk:
            stonk = "SPY"

        #get stonk dataframe
        api_key = os.getenv('SECRET_KEY')
        stonk_alpha = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stonk}&outputsize=full&apikey={api_key}')
        this_df = stonk_alpha.json()
        df_stonk = pd.DataFrame.from_dict(this_df['Time Series (Daily)'],orient='index')

        #reduce stonk data to close price
        df_stonk.reset_index(inplace=True)
        df_stonk.rename(columns={'index':'date', '5. adjusted close': 'stonk_close'}, inplace=True)
        df_stonk.drop(columns=['1. open', '2. high', '3. low', '4. close', '6. volume', '7. dividend amount','8. split coefficient'], axis=1, inplace=True)
        for num in ['stonk_close']:
            df_stonk[num] = df_stonk[num].astype(float, copy=True)
        for date in range(len(df_stonk['date'])):
            df_stonk['date'][date] = datetime.strptime(df_stonk['date'][date], '%Y-%m-%d').date()
        # get bitcoin data
        btc_alpha = requests.get('https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&apikey={api_key}')
        btc_df = btc_alpha.json()
        df_btc = pd.DataFrame.from_dict(btc_df['Time Series (Digital Currency Daily)'],orient='index')
        df_btc.reset_index(inplace=True)
        if not end_date:
            end_date = df_btc['index'][0]
        for date in range(len(df_btc['index'])):
            df_btc['index'][date] = datetime.strptime(df_btc['index'][date], '%Y-%m-%d').date()
        df_btc.rename(columns=lambda x: x.replace(' ', '').lower(), inplace=True)
        df_btc.rename(columns={"index":"date", '2a.high(usd)':'high', '3b.low(usd)':'low'}, inplace=True)
        df_btc.drop(columns=['1a.open(usd)', '1b.open(usd)', '2b.high(usd)',
            '3a.low(usd)', '4a.close(usd)', '4b.close(usd)',
            '5.volume', '6.marketcap(usd)'], axis=1, inplace=True)
        for num in ['high', 'low']:
            df_btc[num] = df_btc[num].astype(float, copy=True)
        df_btc['btc_average'] = df_btc[['high', 'low']].mean(axis=1)
        df_btc.drop(columns=['high', 'low'], axis=1, inplace=True)

        #combine charts and account for stock market days
        df_btc.set_index('date', inplace=True)
        df_stonk.set_index('date', inplace=True)
        df_btc['stonk_close'] = df_stonk['stonk_close']
        df_btc = df_btc.reset_index()

        #get stock price in bitcoin
        btc_price_list = []
        for date in df_btc.index:
            if df_btc.stonk_close[date]:        
                btc_price = float(format(df_btc.stonk_close[date]*10000/df_btc.btc_average[date], '.8f'))
                btc_price_list.append(btc_price)
        df_btc['btc_price'] = btc_price_list

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = df_btc['date'][len(df_btc)-1]

        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        if start_date < df_btc['date'][len(df_btc)-1]:
            start_date = df_btc['date'][len(df_btc)-1]

        if end_date > df_btc['date'][0]:
            end_date = df_btc['date'][0]

        start = df_btc.loc[df_btc['date'] == start_date].index[0]
        end = df_btc.loc[df_btc['date'] == end_date].index[0]

        for filename in os.listdir('app/static/'):
            if filename.startswith('image_'):
                os.remove('app/static/' + filename)

        graph = f'image_{str(datetime.now())[-5:]}.png'
        plt.subplots(figsize=(15, 12))
        plt.grid(True)
        plt.plot(df_btc.date[end:start], df_btc.btc_price[end:start].fillna(method='ffill'), color='orange')
        plt.plot(df_btc.date[end:start], df_btc.stonk_close[end:start].fillna(method='ffill'), color='green')
        plt.title(f'{stonk} Daily Stock Price in Bitcoin', fontsize=18)
        plt.ylabel('Price in Tens of Thousands of Sats (.0001 bitcoin) | Dollars', fontsize=16)
        plt.legend(['Bitcoin', 'Dollars'], loc=2)
        plt.savefig(f'app/static/{graph}');

        adj_start = 0

        for day in range(0, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[start - adj_start]) == True:
                adj_start -= day
            else:
                break

        adj_end = 0

        for day in range(0, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[end + adj_end]) == True:
                adj_end += day
            else:
                break
            

        usd_start_price = round(df_btc.stonk_close[start - adj_start], 2)
        btc_start_price = round(df_btc.btc_price[start - adj_start], 2)
        usd_end_price = round(df_btc.stonk_close[end + adj_end], 2)
        btc_end_price = round(df_btc.btc_price[end + adj_end], 2)
        usd_roi = usd_end_price - usd_start_price
        usd_roi_pct = round((usd_roi/usd_start_price), 2)*100
        btc_roi = round(btc_end_price - btc_start_price, 2)
        btc_roi_pct = round((btc_roi/btc_start_price), 2)*100

        return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph, graph_display=graph_display, 
        usd_start_price=usd_start_price, btc_start_price=btc_start_price, usd_end_price=usd_end_price, btc_end_price=btc_end_price,
        usd_roi=usd_roi, usd_roi_pct=usd_roi_pct, btc_roi=btc_roi, btc_roi_pct=btc_roi_pct)
    return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph, graph_display=graph_display)
        

@app.route("/about")
def about():
    return render_template("about.html")