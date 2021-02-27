from app import app, db
import requests, os
from app.models import User
from flask import request
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

api_key = os.getenv('SECRET_KEY')
update_alpha = requests.get(f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=BTC&to_currency=USD&apikey={api_key}')
update_df = update_alpha.json()
df_update = pd.DataFrame.from_dict(update_df['Realtime Currency Exchange Rate'],orient='index')
date = str(datetime.now().date())
price = df_update[0][4]
day_0 = datetime.strptime("2021-02-24", '%Y-%m-%d').date()
id = 1888 + (datetime.now().date() - day_0).days
u = User(id=id, date=date, price=price)
db.session.add(u)
db.session.commit()
