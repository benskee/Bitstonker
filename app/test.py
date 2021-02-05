from flask import request
import requests, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

df_btc = pd.read_csv(f'app/test/btc.csv')

update_alpha = requests.get(f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=BTC&to_currency=USD&apikey={api_key}')
update_df = update_alpha.json()
df_update = pd.DataFrame.from_dict(update_df['Realtime Currency Exchange Rate'],orient='index')
df_btc.loc[len(df_btc)] = [str(datetime.now())[:10], float(df_update[0][4])]
df_btc.to_csv(rf'app/test/btc.csv')