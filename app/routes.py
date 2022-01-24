from . import app
from app.functions import *
from flask import render_template, request, redirect, flash
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

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/error")
def error_page():
    return render_template("error_page.html")

@app.route("/last5")
def last5():
    context = previous5()
    return render_template("last5.html", **context)

class Index(MethodView):
    def get(self):
        graph_display = "none"
        graph = 'basic.png'
        return render_template('index.html', graph=graph, graph_display=graph_display)
        
    def post(self):
        req = request.form.get
        stonk = req('stonk').upper()
        start_date = req('start_date')
        end_date = req('end_date')
        check = req('dollar_check')
        df_btc = ""

        if not stonk:
            stonk = "SPY"

        df_stonk = get_stonk_df(stonk)
        if 'Error Message' in df_stonk:
            context = stonk_error(stonk)
            return render_template('index.html', **context)
        df_btc = create_df_btc()

        df_btc['stonk_close'] = df_stonk['stonk_close']
        df_btc.reset_index(inplace=True)

        if df_stonk.index[len(df_stonk)-1] > df_btc['date'][0]:
            df_btc = stonk_start(df_btc, df_stonk)
    
        df_btc = generate_price(df_btc)

        start, end = validate_start_end(df_btc, start_date, end_date)
        if start == "":
            context = date_error()
            return render_template('index.html', **context)

        remove_image("btc")

        text_1 = (f'{stonk} Daily Price in Bitcoin')
        text_2 = 'Price in Ten Thousand Sats (.0001 Bitcoin)'
        text_3 = 'Bitcoin'
        if check != None:
            dollar_display = "block"
            graph = generate_dollar_graph(df_btc, start, end, 'btc', text_1, text_2, text_3)
            
        else:
            dollar_display = "none"
            graph = generate_graph(df_btc, start, end, 'btc', text_1, text_2, text_3)
            
        start = adjust_start(df_btc, start)
        end = adjust_end(df_btc, end)
            
        context_a = dict(stonk=stonk, graph=graph, dollar_display=dollar_display)
        context = {**context_a, **populate_table(df_btc, start, end)}
        return render_template('index.html', **context)
app.add_url_rule('/', view_func=Index.as_view('index'))


class S2s(MethodView):

    def get(self):
        graph = "basic.png"
        graph_display = "none"
        context = dict(graph=graph, graph_display=graph_display)
        return render_template('s2s.html', **context)
        
    def post(self):
        req = request.form.get
        stonk1 = req('stonk1').upper()
        stonk2 = req('stonk2').upper()
        start_date = req('start_date')
        end_date = req('end_date')
        check = req('dollar_check')

        stonk1, stonk2 = check_stonks(stonk1, stonk2)
        df_stonk = get_stonk_df(stonk1)
        if 'Error Message' in df_stonk:
            context = stonk_error(stonk1)
            return render_template('s2s.html', **context)
        df_stonk2 = get_stonk_df(stonk2)
        if 'Error Message' in df_stonk2:
            context = stonk_error(stonk2)
            return render_template('s2s.html', **context)
        df_stonk2 = combine_stonks(df_stonk, df_stonk2)
        start, end = validate_start_end(df_stonk2, start_date, end_date)
        if start == "":
            context = date_error()
            return render_template('s2s.html', **context)

        start = adjust_start(df_stonk2, start)
        end = adjust_end(df_stonk2, end)

        remove_image("stonk2")
        text_1 = f'{stonk1} Daily Price in {stonk2}'
        text_2 = f'Price in Shares of {stonk2}'
        text_3 = 'Stonk by Stonk Price'
        if check != None: 
            dollar_display = "block"
            graph = generate_dollar_graph(df_stonk2, start, end, 'stonk2', text_1, text_2, text_3)
            
        else:
            dollar_display = "none"
            graph = generate_graph(df_stonk2, start, end, 'stonk2', text_1, text_2, text_3)

        context_a = dict(stonk1=stonk1, stonk2=stonk2, graph=graph, dollar_display=dollar_display)
        context = {**context_a, **s2s_populate_table(df_stonk2, start, end)}
        return render_template('s2s.html', **context)
app.add_url_rule('/s2s', view_func=S2s.as_view('s2s'))