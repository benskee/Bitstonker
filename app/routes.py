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
        graph = 'basic.png'
        
        return render_template('index.html', graph=graph, graph_display=graph_display)
        
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
    
        df_btc = generate_price(df_btc)

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
        btc_roi = rnd(btc_end_price - btc_start_price)
        usd_roi_pct = "{0:.2%}".format(usd_roi/usd_start_price)
        btc_roi_pct = "{0:.2%}".format(btc_roi/btc_start_price)

        context = dict(stonk=stonk, graph=graph, graph_display=graph_display, dollar_display=dollar_display,
        usd_start_price = usd_start_price, btc_start_price = btc_start_price, usd_end_price = usd_end_price,
        btc_end_price = btc_end_price, usd_roi = usd_roi, btc_roi = btc_roi, usd_roi_pct = usd_roi_pct,
        btc_roi_pct = btc_roi_pct)
        
        return render_template('index.html', **context)
app.add_url_rule('/', view_func=Index.as_view('index'))


@app.route("/about")
def about():
    return render_template("about.html")

class S2s(MethodView):

    def get(self):
        s2s_graph = "basic.png"
        s2s_graph_display = "none"
        context = dict(s2s_graph=s2s_graph, s2s_graph_display=s2s_graph_display)

        return render_template('s2s.html', **context)
        
        
    def post(self):
        req = request.form.get
        stonk1 = req('stonk1')
        stonk2 = req('stonk2')
        s2s_start_date = req('s2s_start_date')
        s2s_end_date = req('s2s_end_date')
        s2s_graph_display = "block"
        s2s_check = req('s2s_dollar_check')

        stonk1, stonk2 = check_stonks(stonk1, stonk2)

        df_stonk = get_stonk_df(stonk1)
        df_stonk2 = get_stonk_df(stonk2)
        df_stonk2.rename(columns={'stonk_close': 'stonk2_close'}, inplace=True)
        df_stonk2['stonk_close'] = df_stonk['stonk_close']
        df_stonk2 = df_stonk2.sort_index(ascending=True, axis=0)
        df_stonk2.reset_index(inplace=True)
        generate_stonk_price(df_stonk2)
        start, end = validate_start_end(df_stonk2, s2s_start_date, s2s_end_date)

        start = adjust_start(df_stonk2, start)
        end = adjust_end(df_stonk2, end)

        remove_image("stonk2")

        s2s_graph_display = 'block'
        text_1 = f'{stonk1} Daily Price in {stonk2}'
        text_2 = f'Price in Shares of {stonk2}'
        text_3 = 'Stonk by Stonk Price'
        if s2s_check != None: 
            dollar_display = "block"
            s2s_graph = generate_dollar_graph(df_stonk2, start, end, 'stonk2', text_1, text_2, text_3)
            
        else:
            dollar_display = "none"
            s2s_graph = generate_graph(df_stonk2, start, end, 'stonk2', text_1, text_2, text_3)

        stonk1_start_price = rnd(df_stonk2.stonk_close[start])
        stonk1_end_price = rnd(df_stonk2.stonk_close[end])
        stonk1_roi = rnd(stonk1_end_price - stonk1_start_price)
        stonk1_roi_pct = "{0:.2%}".format(stonk1_roi/stonk1_start_price)
        stonk2_start_price = rnd(df_stonk2.stonk2_close[start])
        stonk2_end_price = rnd(df_stonk2.stonk2_close[end])
        stonk2_roi = rnd(stonk2_end_price - stonk2_start_price)
        stonk2_roi_pct = "{0:.2%}".format(stonk2_roi/stonk2_start_price)
        s2s_start_price = rnd(df_stonk2.stonk2_price[start])
        s2s_end_price = rnd(df_stonk2.stonk2_price[end])
        s2s_roi = rnd(s2s_end_price - s2s_start_price)
        s2s_roi_pct = "{0:.2%}".format(s2s_roi/s2s_start_price)

        context = dict(stonk1=stonk1, stonk2=stonk2, s2s_graph=s2s_graph, s2s_graph_display=s2s_graph_display, 
        stonk1_start_price=stonk1_start_price, stonk1_end_price=stonk1_end_price, stonk1_roi=stonk1_roi, 
        stonk1_roi_pct=stonk1_roi_pct, stonk2_start_price=stonk2_start_price, stonk2_end_price=stonk2_end_price,
        stonk2_roi=stonk2_roi, stonk2_roi_pct=stonk2_roi_pct, s2s_start_price=s2s_start_price, 
        s2s_end_price=s2s_end_price, s2s_roi=s2s_roi, s2s_roi_pct=s2s_roi_pct, dollar_display=dollar_display)

        return render_template('s2s.html', **context)

app.add_url_rule('/s2s', view_func=S2s.as_view('s2s'))