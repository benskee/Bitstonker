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
        check = request.form.get('dollar_check')
        dollar_display = "none"
        df_btc = ""

        if not stonk:
            stonk = "SPY"

        #get stonk dataframe
        api_key = os.environ['SECRET_KEY']
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
        dir_list = os.listdir('app/csv/')
        btc_name = str(datetime.now())[:10]

        if len(dir_list) == 0 or btc_name + '.csv'!=dir_list[0]:
            for filename in os.listdir('app/csv/'):
                os.remove(f'app/csv/{filename}')

            btc_alpha = requests.get(f'https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&apikey={api_key}')
            btc_df = btc_alpha.json()
            btc_data = pd.DataFrame.from_dict(btc_df['Time Series (Digital Currency Daily)'],orient='index')
            btc_data.reset_index(inplace=True)
            btc_data.rename(columns=lambda x: x.replace(' ', '').lower(), inplace=True)
            btc_data.rename(columns={"index":"date", '2a.high(usd)':'high', '3b.low(usd)':'low'}, inplace=True)
            btc_data.drop(columns=['1a.open(usd)', '1b.open(usd)', '2b.high(usd)',
                '3a.low(usd)', '4a.close(usd)', '4b.close(usd)',
                '5.volume', '6.marketcap(usd)'], axis=1, inplace=True)
            for num in ['high', 'low']:
                btc_data[num] = btc_data[num].astype(float, copy=True)
            btc_data['btc_average'] = btc_data[['high', 'low']].mean(axis=1)
            btc_data.drop(columns=['high', 'low'], axis=1, inplace=True)
            btc_data.to_csv(rf'app/csv/{btc_name}.csv')
            df_btc = btc_data
        else:
            get_df_btc = pd.read_csv(f'app/csv/{btc_name}.csv')
            df_btc = get_df_btc

        for date in range(len(df_btc['date'])):
            df_btc['date'][date] = datetime.strptime(df_btc['date'][date], '%Y-%m-%d').date()
        df_btc.set_index('date', inplace=True)
        #combine charts and account for stock market days
        df_stonk.set_index('date', inplace=True)
        df_btc['stonk_close'] = df_stonk['stonk_close']
        df_btc.reset_index(inplace=True)

        #get stock price in bitcoin
        btc_price_list = []
        for date in df_btc.index:
            if df_btc.stonk_close[date]:        
                btc_price = float(format(df_btc.stonk_close[date]*10000/df_btc.btc_average[date], '.8f'))
                btc_price_list.append(btc_price)
        df_btc['btc_price'] = btc_price_list


        # ensure start and end dates are valid
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = df_btc['date'][len(df_btc)-1]

        if not end_date:
            end_date = df_btc['date'][0]
        else:
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

        # generate graph 
        graph = f'image_{str(datetime.now())[-5:]}.png'
        if check != None: 
            dollar_display = "block"
            plt.subplots(figsize=(15, 12))
            plt.grid(True)
            plt.plot(df_btc.date[end:start], df_btc.btc_price[end:start].fillna(method='ffill'), color='orange')
            plt.plot(df_btc.date[end:start], df_btc.stonk_close[end:start].fillna(method='ffill'), color='green')
            plt.title(f'{stonk} Daily Stock Price in Bitcoin', fontsize=18)
            plt.ylabel('Price in Ten Thousand Sats (.0001 Bitcoin) | Dollars', fontsize=16)
            plt.legend(['Bitcoin', 'Dollars'], loc=2)
            plt.savefig(f'app/static/{graph}');
        else:
            plt.subplots(figsize=(15, 12))
            plt.grid(True)
            plt.plot(df_btc.date[end:start], df_btc.btc_price[end:start].fillna(method='ffill'), color='orange')
            plt.title(f'{stonk} Daily Stock Price in Bitcoin', fontsize=18)
            plt.ylabel('Price in Ten Thousand Sats (.0001 Bitcoin)', fontsize=16)
            plt.legend(['Bitcoin'], loc=2)
            plt.savefig(f'app/static/{graph}');

        
        # account for start or end on day market is closed
        adj_start = 0

        for day in range(1, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[start - adj_start]) == True:
                adj_start += day
            else:
                break

        adj_end = 0

        for day in range(1, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[end + adj_end]) == True:
                adj_end += day
            else:
                break
            

        # populate table
        usd_start_price = round(df_btc.stonk_close[start - adj_start], 2)
        btc_start_price = round(df_btc.btc_price[start - adj_start], 2)
        usd_end_price = round(df_btc.stonk_close[end + adj_end], 2)
        btc_end_price = round(df_btc.btc_price[end + adj_end], 2)
        usd_roi = round(usd_end_price - usd_start_price, 2)
        usd_roi_pct = "{0:.2%}".format(usd_roi/usd_start_price)
        btc_roi = round(btc_end_price - btc_start_price, 2)
        btc_roi_pct = "{0:.2%}".format(btc_roi/btc_start_price)
        

        return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph, graph_display=graph_display, 
        usd_start_price=usd_start_price, btc_start_price=btc_start_price, usd_end_price=usd_end_price, btc_end_price=btc_end_price,
        usd_roi=usd_roi, usd_roi_pct=usd_roi_pct, btc_roi=btc_roi, btc_roi_pct=btc_roi_pct, dollar_display=dollar_display)
    return render_template('index.html', stonk=stonk, df_btc=df_btc, graph=graph, graph_display=graph_display)
        

@app.route("/about")
def about():
    return render_template("about.html")