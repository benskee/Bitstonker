from . import app
from flask import render_template, request, redirect
import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine

@app.before_request
def before_request():
    if request.url.startswith('http://') and request.url.startswith('http://127.0.0.1:5000/') == False:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


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

        # Import Database and create BTC dataframe
        SQL_URI = os.environ['SQLALCHEMY_DATABASE_URI']
        cnx = create_engine(SQL_URI)
        conn = cnx.connect()
        df_btc = pd.read_sql_table('user', cnx)
        conn.close()
        cnx.dispose()
        df_btc.rename(columns={'price':'close_price'}, inplace=True)
        for date in range(len(df_btc['date'])):
            df_btc['date'][date] = datetime.strptime(df_btc['date'][date], '%Y-%m-%d').date()
        df_btc.set_index('date', inplace=True)
        
        #combine charts and account for stonk market days
        df_stonk.set_index('date', inplace=True)
        df_btc['stonk_close'] = df_stonk['stonk_close']
        df_btc.reset_index(inplace=True)

        #get stonk price in bitcoin
        btc_price_list = []
        for date in df_btc.index:
            if df_btc.stonk_close[date]:        
                btc_price = float(format(df_btc.stonk_close[date]*10000/float(df_btc.close_price[date]), '.8f'))
                btc_price_list.append(btc_price)
        df_btc['btc_price'] = btc_price_list


        # ensure start and end dates are valid
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = df_btc['date'][0]

        if not end_date:
            end_date = df_btc['date'][len(df_btc)-1]
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        if start_date < df_btc['date'][0]:
            start_date = df_btc['date'][0]

        if end_date > df_btc['date'][len(df_btc)-1]:
            end_date = df_btc['date'][len(df_btc)-1]

        start = df_btc.loc[df_btc['date'] == start_date].index[0]
        end = df_btc.loc[df_btc['date'] == end_date].index[0]

        for filename in os.listdir('app/static/'):
            if filename.startswith('image_'):
                os.remove('app/static/' + filename)

        # generate graph 
        graph = f'image_{str(datetime.now())[-5:]}.png'
        if check != None: 
            dollar_display = "block"
            figure, ax1 = plt.subplots(figsize=(15, 12))
            plt.grid(True)
            ax1.plot(df_btc.date[start:end+1], df_btc.btc_price[start:end+1].fillna(method='ffill'), label='Bitcoin', color='orange')
            plt.title(f'{stonk} Daily stonk Price in Bitcoin', fontsize=18)
            plt.ylabel(f'Price in Ten Thousand Sats (.0001 Bitcoin)', fontsize=16)
            ax2 = plt.twinx()
            ax2.set_ylabel(f'Price in Dollars', fontsize=16)
            ax2.plot(df_btc.date[start:end+1], df_btc.stonk_close[start:end+1].fillna(method='ffill'), label='Dollars', color='green')
            ax2.tick_params(axis='y')
            lines_1, labels_1 = ax1.get_legend_handles_labels()
            lines_2, labels_2 = ax2.get_legend_handles_labels()
            lines = lines_1 + lines_2
            labels = labels_1 + labels_2
            ax1.legend(lines, labels, loc=2)
            plt.savefig(f'app/static/{graph}');
        else:
            plt.subplots(figsize=(15, 12))
            plt.grid(True)
            plt.plot(df_btc.date[start:end+1], df_btc.btc_price[start:end+1].fillna(method='ffill'), color='orange')
            plt.title(f'{stonk} Daily stonk Price in Bitcoin', fontsize=18)
            plt.ylabel('Price in Ten Thousand Sats (.0001 Bitcoin)', fontsize=16)
            plt.legend(['Bitcoin'], loc=2)
            plt.savefig(f'app/static/{graph}');

        
        # account for start or end on day market is closed
        adj_start = 0

        for day in range(1, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[start + adj_start]) == True:
                adj_start += 1
            else:
                break

        adj_end = 0

        for day in range(1, len(df_btc)-1):
            if np.isnan(df_btc.stonk_close[end - adj_end]) == True:
                adj_end += 1
            else:
                break
            

        # populate table
        usd_start_price = round(df_btc.stonk_close[start + adj_start], 2)
        btc_start_price = round(df_btc.btc_price[start + adj_start], 2)
        usd_end_price = round(df_btc.stonk_close[end - adj_end], 2)
        btc_end_price = round(df_btc.btc_price[end - adj_end], 2)
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

@app.route('/s2s', methods=["GET", "POST"])
def s2s():
    if request.method == "GET":
        stonk1 = ""
        stonk2 = ""
        # df_btc = ""
        s2s_graph = ""
        s2s_graph_display = "none"
        
        

    if request.method == "POST":
        stonk1 = request.form.get('stonk1').upper()
        stonk2 = request.form.get('stonk2').upper()
        s2s_start_date = request.form.get('s2s_start_date')
        s2s_end_date = request.form.get('s2s_end_date')
        s2s_graph_display = "block"
        s2s_check = request.form.get('s2s_dollar_check')
        s2s_dollar_display = "none"
        # df_btc = ""

        if not stonk1 and not stonk2:
            stonk1 = "COKE"
            stonk2 = "PEP"

        elif not stonk1:
            stonk1="SPY"

        elif not stonk2:
            stonk2="GBTC"

        #get stonk dataframe
        api_key = os.environ['SECRET_KEY']
        stonk_alpha = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stonk1}&outputsize=full&apikey={api_key}')
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

        stonk2_alpha = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stonk2}&outputsize=full&apikey={api_key}')
        this2_df = stonk2_alpha.json()
        df_stonk2 = pd.DataFrame.from_dict(this2_df['Time Series (Daily)'],orient='index')
        df_stonk2.reset_index(inplace=True)
        df_stonk2.rename(columns={'index':'date', '5. adjusted close': 'stonk2_close'}, inplace=True)
        df_stonk2.drop(columns=['1. open', '2. high', '3. low', '4. close', '6. volume', '7. dividend amount','8. split coefficient'], axis=1, inplace=True)
        for num in ['stonk2_close']:
            df_stonk2[num] = df_stonk2[num].astype(float, copy=True)
        for date in range(len(df_stonk2['date'])):
            df_stonk2['date'][date] = datetime.strptime(df_stonk2['date'][date], '%Y-%m-%d').date()

        #combine charts and account for stock market days
        df_stonk2.set_index('date', inplace=True)
        df_stonk.set_index('date', inplace=True)
        df_stonk2['stonk_close'] = df_stonk['stonk_close']
        df_stonk2 = df_stonk2.reset_index()

        #get stock price in bitcoin
        stonk2_price_list = []
        for date in df_stonk2.index:
            if df_stonk2.stonk_close[date]:        
                stonk2_price = float(format(df_stonk2.stonk_close[date]/df_stonk2.stonk2_close[date], '.8f'))
                stonk2_price_list.append(stonk2_price)
        df_stonk2['stonk2_price'] = stonk2_price_list

        if s2s_start_date:
            s2s_start_date = datetime.strptime(s2s_start_date, '%Y-%m-%d').date()
        else:
            s2s_start_date = df_stonk2['date'][len(df_stonk2)-1]

        if not s2s_end_date:
            s2s_end_date = df_stonk2['date'][0]
        else:
            s2s_end_date = datetime.strptime(s2s_end_date, '%Y-%m-%d').date()

        if s2s_start_date > s2s_end_date:
            s2s_start_date, s2s_end_date = s2s_end_date, s2s_start_date

        if s2s_start_date < df_stonk2['date'][len(df_stonk2)-1]:
            s2s_start_date = df_stonk2['date'][len(df_stonk2)-1]

        if s2s_end_date > df_stonk2['date'][0]:
            s2s_end_date = df_stonk2['date'][0]

        adj_start = 0

        for day in range(1, len(df_stonk2)-1):
            if len(df_stonk2.loc[df_stonk2['date'] == s2s_start_date + timedelta(days=adj_start)]) < 1:
                adj_start += 1 
            else:
                break

        start = df_stonk2.loc[df_stonk2['date'] == s2s_start_date + timedelta(days=adj_start)].index[0]


        adj_end = 0

        for day in range(1, len(df_stonk2)-1):
            if len(df_stonk2.loc[df_stonk2['date'] == s2s_end_date + timedelta(days=adj_end)]) < 1:
                adj_end += 1 
            else:
                break

        end = df_stonk2.loc[df_stonk2['date'] == s2s_end_date + timedelta(days=adj_end)].index[0]
        
        for filename in os.listdir('app/static/'):
            if filename.startswith('s2s_'):
                os.remove('app/static/' + filename)

        # generate graph 
        s2s_graph = f's2s_{str(datetime.now())[-5:]}.png'
        if s2s_check != None: 
            s2s_dollar_display = "block"
            figure, ax1 = plt.subplots(figsize=(15, 12))
            plt.grid(True)
            ax1.plot(df_stonk2.date[end:start+1], df_stonk2.stonk2_price[end:start+1].fillna(method='ffill'), label='Stonk by Stonk', color='orange')
            plt.title(f'{stonk1} Daily Price in {stonk2}', fontsize=18)
            plt.ylabel(f'Price in shares of {stonk2}', fontsize=16)
            ax2 = plt.twinx()
            ax2.set_ylabel(f'Price in Dollars', fontsize=16)
            ax2.plot(df_stonk2.date[end:start+1], df_stonk2.stonk_close[end:start+1].fillna(method='ffill'), label='Dollars', color='green')
            ax2.tick_params(axis='y')
            lines_1, labels_1 = ax1.get_legend_handles_labels()
            lines_2, labels_2 = ax2.get_legend_handles_labels()
            lines = lines_1 + lines_2
            labels = labels_1 + labels_2
            ax1.legend(lines, labels, loc=2)
            plt.savefig(f'app/static/{s2s_graph}');
        else:
            plt.subplots(figsize=(15, 12))
            plt.grid(True)
            plt.plot(df_stonk2.date[end:start], df_stonk2.stonk2_price[end:start].fillna(method='ffill'), color='orange')
            plt.title(f'{stonk1} Daily Price in {stonk2}', fontsize=18)
            plt.ylabel(f'Price in Shares of {stonk2}', fontsize=16)
            plt.legend(['Stonk by Stonk Price'], loc=2)
            plt.savefig(f'app/static/{s2s_graph}');

        # populate table
        stonk1_start_price = round(df_stonk2.stonk_close[start - adj_start], 2)
        stonk1_end_price = round(df_stonk2.stonk_close[end + adj_end], 2)
        stonk1_roi = round(stonk1_end_price - stonk1_start_price, 2)
        stonk1_roi_pct = "{0:.2%}".format(stonk1_roi/stonk1_start_price)

        stonk2_start_price = round(df_stonk2.stonk2_close[start - adj_start], 2)
        stonk2_end_price = round(df_stonk2.stonk2_close[end + adj_end], 2)
        stonk2_roi = round(stonk2_end_price - stonk2_start_price, 2)
        stonk2_roi_pct = "{0:.2%}".format(stonk2_roi/stonk2_start_price)

        s2s_start_price = round(df_stonk2.stonk2_price[start - adj_start], 2)
        s2s_end_price = round(df_stonk2.stonk2_price[end + adj_end], 2)
        s2s_roi = round(s2s_end_price - s2s_start_price, 2)
        s2s_roi_pct = "{0:.2%}".format(s2s_roi/s2s_start_price)


        return render_template('s2s.html', stonk1=stonk1, stonk2=stonk2, s2s_graph=s2s_graph, 
        s2s_graph_display=s2s_graph_display, s2s_dollar_display=s2s_dollar_display, 
        stonk1_start_price=stonk1_start_price, stonk1_end_price=stonk1_end_price, stonk1_roi=stonk1_roi, stonk1_roi_pct=stonk1_roi_pct, 
        stonk2_start_price=stonk2_start_price, stonk2_end_price=stonk2_end_price, stonk2_roi=stonk2_roi, stonk2_roi_pct=stonk2_roi_pct, 
        s2s_start_price=s2s_start_price, s2s_end_price=s2s_end_price, s2s_roi=s2s_roi, s2s_roi_pct=s2s_roi_pct)

    return render_template('s2s.html', stonk1=stonk1, stonk2=stonk2, s2s_graph=s2s_graph, s2s_graph_display=s2s_graph_display)