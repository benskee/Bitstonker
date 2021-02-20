from app import app, db

import requests, os
from app.models import User
from flask import request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

# df_btc = pd.read_csv(f'app/csv/btc.csv')

api_key = os.getenv('SECRET_KEY')
update_alpha = requests.get(f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=BTC&to_currency=USD&apikey={api_key}')
update_df = update_alpha.json()
df_update = pd.DataFrame.from_dict(update_df['Realtime Currency Exchange Rate'],orient='index')
date = str(datetime.now())[:10]
price = df_update[0][4]
u = User(date=date, price=price)
db.session.add(u)
db.session.commit()
