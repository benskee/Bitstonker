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

    if request.method == "POST":
        stonk = request.form.get('stonk').upper()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        

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

        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
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
        plt.ylabel('Price in Tens of Thousands of Sats | Dollars', fontsize=16)
        plt.xlabel('Date', fontsize=16)
        plt.legend(['Bitcoin', 'Dollars'], loc=2)
        plt.savefig(f'app/static/{graph}');

        return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph)
    return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph)
        

@app.route("/about")
def about():
    return render_template("about.html")