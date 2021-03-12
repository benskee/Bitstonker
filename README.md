<h1 align="center">Bitstonker</h1>
<p align="center"><a href="https://www.linkedin.com/in/ben-skee-software-engineer/">LinkedIn</a> | <a href="bitstonker.com">bitstonker.com</a></p>

## About The Project

This is a portfolio project that allows the user to analyze stocks denominated in Bitcoin. As a bonus I built the stonk-by-stonk feature that allows the user to compare 2 stocks. This project can be found at [bitstonker.com](bitstonker.com)


## Getting Started

1. Clone the repo
  ```sh 
  git clone https://github.com/benskee/Bitstonker.git
  ```

2. Create your virtual environment.
```sh
python3 -m venv bitstonker-env
```

3. Activate your virtual environment
  Windows
  ```sh
  bitstonker-env\Scripts\activate.bat
  ```

Unix or Mac
  ```sh 
  source bitstonker-env/bin/activate
  ```

If you need help with virtual environments visit [this tutorial](https://docs.python.org/3/tutorial/venv.html)

4. Install the packages from requirements.txt 
  ```sh
  pip install -r requirements.txt
  ```


### Activate Sample Database

In [/app/routes.py](/app/routes.py) find 
```df_btc = create_df_btc()```
([link](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L53)) 

Replace with 
  ```sh
  df_btc = create_sample_df_btc()
  ```

This will run the app using the included sample_btc.csv in place of the btc database. 
If you would like to generate your own Bitcoin csv you can visit [This Repo](https://github.com/benskee/Bitcoin_stock_hours)



### Activate Stonks
For the stonks you can either:

1. Use an api key from alphavantage.com. If you would like to obtain a free one follow this
link. [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support#api-key)

To use your api key change the `SECRET_KEY` variable in `config.py`
```SECRET_KEY = 'your alphavantage api key'```

2. Use the sample csv files. 
In [/apps/routes.py](/apps/routes.py) replace the function 
```get_stonk_df()```
with 
```get_sample_stonk_df()```

There are 3 occurances: the first is for the main page and can be found [here](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L49)
The other two are for the stonk-by-stonk page and can be found [here](https://github.com/benskee/Bitstonker/blob/55e713d70fc8fd5f1844e23f8a2eefeeed82247d/app/routes.py#L106-L110)

For this option you will not have access to the api and will be limited to the sample tickers 
(GBTC, TSLA, AMZN, SPY, COKE, PEP)

## Run the App
The last step is to activate flask on your local host 
```flask run```


**Happy stonking!**