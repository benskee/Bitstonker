import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


# def gbtc_head():

#     api_key = 'TYQMZOZHEW4C6ZAL'

#     gbtc_alpha = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=GBTC&interval=1min&outputsize=full&apikey=TYQMZOZHEW4C6ZAL')

#     this_df = gbtc_alpha.json()

#     df_gbtc = pd.DataFrame.from_dict(this_df['Time Series (Daily)'],orient='index')

#     df_gbtc.head

# def stock_entry():