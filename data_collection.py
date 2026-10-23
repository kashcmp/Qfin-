import yfinance as yf
from thetadata import ThetaClient
from datetime import date, timedelta
from pathlib import Path 
import pandas as pd
from scipy.special import erfinv, erf
import numpy as np
from pyspark.sql import SparkSession
import time
import requests


# program to receive parquet files from theta client and save them
'''
client = ThetaClient(email="danny.kashanin@gmail.com", password="siccyk-Wajxop-3pedxu",api_key="td1_prod_4dbb3a30d3394e63affc48fb98c68370")

start_date=date(2025, 10, 7)
end_date=date(2026, 10, 7)
steps = 5

using = start_date

out = Path("data/spy_option_history")
out.mkdir(parents=True, exist_ok=True)

while using <= end_date:

    batch_end = min(timedelta(days = steps-1) + using,end_date)

    df = client.option_history_eod(
        start_date=using,
        end_date=batch_end,
        symbol='SPY',
        expiration="*",
        max_dte = 30
    )
    if df is not None and len(df):
            df.write_parquet(out / f"{using}_{batch_end}.parquet")  # Polars
    using = batch_end + timedelta(days=1)

'''



# program to read in all parquet files and create two new dataframe of calls and puts with only necessary data
'''
# Initialize a Spark session
spark = SparkSession.builder.appName("SparkExample").getOrCreate()


start_date=date(2025, 10, 7)
end_date=date(2026, 10, 7)
steps = 5
using = start_date

col_names =  ['Mid', 'Strike', 'TTE(years)', 'Rfr','Initial',"Created"]
dataset_c = pd.DataFrame(columns = col_names)
dataset_p  = pd.DataFrame(columns = col_names)

count = 0
while using <= end_date:

    batch_end = min(timedelta(days = steps-1) + using,end_date)
    df = pd.read_parquet("data/spy_option_history/" +f"{using}_{batch_end}" + ".parquet")

    df["created"] = pd.to_datetime(df["created"]).dt.date
    df["expiration"] = pd.to_datetime(df["expiration"]).dt.date

    calls = df[df["right"] == "CALL"]
    puts =  df[df["right"] == "PUT"]

    c_mids = np.array((calls["bid"] + calls["ask"])/2)
    c_strikes = np.array(calls["strike"])
    p_mids = np.array((puts["bid"] + puts["ask"])/2)
    p_strikes = np.array(puts["strike"])

    c_tte = (calls["expiration"] - calls["created"])
    p_tte = puts["expiration"] - puts["created"]
    c_tte  = [i.days/365 for i in np.array(c_tte)]
    p_tte  = [i.days/365 for i in np.array(p_tte)]


    new_row = pd.DataFrame({'Mid':c_mids, 'Strike':c_strikes, 'TTE(years)':c_tte, 'Rfr':np.zeros((c_mids.shape)),'Initial':np.zeros((c_mids.shape)),"Created":calls["created"]})
    dataset_c = pd.concat([dataset_c,new_row], ignore_index=True)
    new_row = pd.DataFrame({'Mid':p_mids, 'Strike':p_strikes, 'TTE(years)':p_tte, 'Rfr':np.zeros((p_mids.shape)),'Initial':np.zeros((p_mids.shape)),"Created":puts["created"]})
    dataset_p = pd.concat([dataset_p,new_row], ignore_index=True)

    using = batch_end + timedelta(days=1)


dataset_c.to_csv("calls.csv")
dataset_p.to_csv("puts.csv")
'''



#program to query FRED for 1month bond tields over same period as before
'''
api_key = "153fdee52837f80203df12a4b81352ae"

base = "https://api.stlouisfed.org/fred"
end = "/series/observations"

series_id = 'DGS1MO'
startdate = '2025-10-06'
endate = "2026-10-07"
ts_freq = 'q'
ts_units = 'pc1'

params = {
    'series_id' : series_id,
    'api_key' : api_key,
    'file_type' : 'json',
    'observation_start' : startdate,
    'observation_end' : endate
}

response = requests.get(base+end,params = params)

if response.status_code == 200:
    response_data = response.json()
    data = pd.DataFrame(response_data["observations"])
    data["date"] = pd.to_datetime(data["date"])
    data['value'] = data['value']

    data.to_csv("rfr.csv")
else:
    print("Data Retrieval Failed Status Code : ",response.status_code)
'''

#yfinfnace for underlying asset close

startdate = '2025-10-05'
endate = "2026-10-09"

df = yf.download("SPY",start = startdate,end = endate,interval = "1d")
df.to_csv("underlying.csv")
