from app import app, db

import requests, os
from app.models import User
from flask import request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

df_btc = pd.read_csv(f'app/csv/btc.csv')

for i in range(0,len(df_btc)):
    date = df_btc.date[i]
    price = df_btc.close_price[i]
    u = User(date=date, price=price)
    db.session.add(u)
    db.session.commit()
