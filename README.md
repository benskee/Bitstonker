# Bitstonker
Analyze stocks denominated in Bitcoin. This project can be found at bitstonker.com

If you would like to test it out on your own here are the steps after you clone the repo:

Create and activate your virtual environment.
If you need help with virtual environments visit [this tutorial](https://docs.python.org/3/tutorial/venv.html)

Install the packages from requirements.txt (pip install -r requirements.txt)


### Activate Sample Database
In [/app/routes.py](/app/routes.py) find `df_btc = create_df_btc()`
([link](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L53)) 

Replace with `df_btc = create_sample_df_btc()`

This will run the app using the included sample_btc.csv in place of the btc database. 
If you would like to generate your own Bitcoin csv you can visit [This Repo](https://github.com/benskee/Bitcoin_stock_hours)



### Activate Stonks
For the stonks you can either:

a) Use an api key from alphavantage.com. If you would like to obtain a free one follow this
link. [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support#api-key)

To use your api key create a .env file in the main directory and add the line
SECRET_KEY='your_alphavantage_api_key'
(replace the part in quotes with your alphavantage api key)



b) Use the sample csv files. In [/apps/routes.py](/apps/routes.py) replace the function `get_stonk_df()`
with `get_sample_stonk_df()`

There are 3 occurances: the first is for the main page and can be found [here](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L49)
The other two are for the stonk-by-stonk page and can be found [here](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L106-L110)

For this option you will not have access to the api and will be limited to the tickers 
(GBTC, TSLA, AMZN, SPY, COKE, PEP)



The last step is to activate flask on your local host (type `flask run` in the CLI).

**Happy stonking!**