from . import app
from app.functions import *
from flask import render_template, request, redirect
from flask.views import MethodView
import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

@app.before_request
def before_request():
    if request.url.startswith('http://') and request.url.startswith('http://127.0.0.1:5000/') == False:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


class Index(MethodView):
    def get(self):
        graph_display = "none"
        
        return render_template('index.html', graph_display=graph_display)
        
    def post(self):
        stonk = request.form.get('stonk').upper()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        check = request.form.get('dollar_check')
        df_btc = ""

        if not stonk:
            stonk = "SPY"

        df_stonk = get_stonk_df(stonk)

        df_btc = create_df_btc()

        df_btc['stonk_close'] = df_stonk['stonk_close']
        df_btc.reset_index(inplace=True)

        if df_stonk.index[len(df_stonk)-1] > df_btc['date'][0]:
            df_btc = stonk_start(df_btc, df_stonk)
    
        df_btc = generate_price(df_btc, 'btc')

        start, end = validate_start_end(df_btc, start_date, end_date)

        remove_image("btc")

        graph_display = "block"
        text_1 = (f'{stonk} Daily Price in Bitcoin')
        text_2 = (f'Price in Ten Thousand Sats (.0001 Bitcoin)')
        text_3 = 'Bitcoin'
        if check != None:
            dollar_display = "block"
            graph = generate_dollar_graph(df_btc, start, end, 'btc', text_1, text_2, text_3)
            
        else:
            dollar_display = "none"
            graph = generate_graph(df_btc, start, end, 'btc', text_1, text_2, text_3)
            

        start = adjust_start(df_btc, start)
        end = adjust_end(df_btc, end)
            
        usd_start_price = rnd(df_btc.stonk_close[start])
        btc_start_price = rnd(df_btc.btc_price[start])
        usd_end_price = rnd(df_btc.stonk_close[end])
        btc_end_price = rnd(df_btc.btc_price[end])
        usd_roi = rnd(usd_end_price - usd_start_price)
        usd_roi_pct = "{0:.2%}".format(usd_roi/usd_start_price)
        btc_roi = rnd(btc_end_price - btc_start_price)
        btc_roi_pct = "{0:.2%}".format(btc_roi/btc_start_price)
        
        return render_template('index.html', stonk=stonk, graph=graph, graph_display=graph_display, 
        usd_start_price=usd_start_price, btc_start_price=btc_start_price, usd_end_price=usd_end_price, btc_end_price=btc_end_price,
        usd_roi=usd_roi, usd_roi_pct=usd_roi_pct, btc_roi=btc_roi, btc_roi_pct=btc_roi_pct, dollar_display=dollar_display)
app.add_url_rule('/', view_func=Index.as_view('index'))


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
        dollar_display = "none"
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
        
        remove_image("s2s")

        # generate graph 
        s2s_graph = f's2s_{str(datetime.now())[-5:]}.png'
        if s2s_check != None: 
            dollar_display = "block"
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
        s2s_graph_display=s2s_graph_display, dollar_display=dollar_display, 
        stonk1_start_price=stonk1_start_price, stonk1_end_price=stonk1_end_price, stonk1_roi=stonk1_roi, stonk1_roi_pct=stonk1_roi_pct, 
        stonk2_start_price=stonk2_start_price, stonk2_end_price=stonk2_end_price, stonk2_roi=stonk2_roi, stonk2_roi_pct=stonk2_roi_pct, 
        s2s_start_price=s2s_start_price, s2s_end_price=s2s_end_price, s2s_roi=s2s_roi, s2s_roi_pct=s2s_roi_pct)

    return render_template('s2s.html', stonk1=stonk1, stonk2=stonk2, s2s_graph=s2s_graph, s2s_graph_display=s2s_graph_display)