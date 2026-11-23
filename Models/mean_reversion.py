import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
from scipy.stats import linregress
from pathlib import Path 
import pandas as pd
from datetime import date, timedelta
from pyspark.sql import SparkSession
import time
import requests
from scipy.stats import norm
from scipy.optimize import brentq
import yfinance as yf
from scipy.optimize import differential_evolution
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
'''
spark = SparkSession.builder.appName("SparkExample").getOrCreate()

start_date=date(2023, 10, 7)
end_date=date(2026, 11, 4)

steps = 5
using = start_date

col_names =  ['Bid', 'Ask', 'Mid', 'Strike', 'TTE(years)',"Created","Expiration"]
dataset_c = pd.DataFrame(columns = col_names)
dataset_p  = pd.DataFrame(columns = col_names)

count = 0
while using <= end_date:

    batch_end = min(timedelta(days = steps-1) + using,end_date)
    df = pd.read_parquet("data/spy_option_history/" +f"{using}_{batch_end}" + ".parquet")

    df["created"] = pd.to_datetime(df["created"]).dt.date
    df["expiration"] = pd.to_datetime(df["expiration"]).dt.date
    df["last_trade"] = pd.to_datetime(df["last_trade"]).dt.date

    calls = df[df["right"] == "CALL"]
    #puts =  df[df["right"] == "PUT"]

    c_mids = np.array((calls["bid"] + calls["ask"])/2)
    c_bids = np.array(calls["bid"])
    c_asks = np.array(calls["ask"])
    c_strikes = np.array(calls["strike"])
    #p_mids = np.array((puts["bid"] + puts["ask"])/2)
    #p_bids = np.array(puts["bid"])
    #p_asks = np.array(puts["ask"])
    #p_strikes = np.array(puts["strike"])

    c_tte = (calls["expiration"] - calls["last_trade"])
    #p_tte = puts["expiration"] - puts["last_trade"]
    c_tte  = [i.days/365 for i in np.array(c_tte)]
    #p_tte  = [i.days/365 for i in np.array(p_tte)]

    c_volb = calls["bid_size"]
    c_vola = calls["ask_size"]
    #p_volb = puts["bid_size"]
    #p_vola = puts["ask_size"]
    expc = calls["expiration"]
    #expp = puts["expiration"]

    new_row = pd.DataFrame({'Bid':c_bids, 'Ask':c_asks, 'Mid':c_mids, 'Strike':c_strikes, 'TTE(years)':c_tte,"Created":calls["created"],"Expiration" : expc, "bVolume":c_volb,"aVolume":c_vola})
    dataset_c = pd.concat([dataset_c,new_row], ignore_index=True)
    #new_row = pd.DataFrame({'Bid':p_bids, 'Ask':p_asks, 'Mid':p_mids, 'Strike':p_strikes, 'TTE(years)':p_tte, 'Rfr':np.zeros((p_mids.shape)),'Initial':np.zeros((p_mids.shape)),"Created":puts["created"],"Expiration" : expp,"bVolume" :c_volb,"aVolume":c_vola })
    #dataset_p = pd.concat([dataset_p,new_row], ignore_index=True)

    using = batch_end + timedelta(days=1)

calls = dataset_c

#puts = dataset_p

rfr = pd.read_csv("../CSVs/rfr.csv")
rfr = rfr.drop(columns = ["realtime_start","realtime_end"])

for i in range(len(rfr["value"])):
    if rfr["value"].loc[i] == ".":
        rfr.loc[i, "value"] = rfr.loc[i-1, "value"]

rfr["date"] = pd.to_datetime(rfr["date"])
rfr = rfr.set_index("date")
calls["Created"] = pd.to_datetime(calls["Created"])

underlying = pd.read_csv("../CSVs/underlying.csv")

calls["Rfr"] = calls["Created"].map(rfr["value"])

calls["Rfr"] = pd.to_numeric(calls["Rfr"]) / 100 

#puts["Rfr"] = rfr["value"].reindex(puts["Created"]).reset_index(drop=True)
#puts["Rfr"] = pd.to_numeric(puts["Rfr"]) / 100 

underlying["Price"] = pd.concat([underlying["Price"].iloc[:2],pd.to_datetime(underlying["Price"].iloc[2:])])
underlying = underlying.set_index("Price")

calls["Initial"] = calls["Created"].map(underlying["Close"])
calls["Initial"] = pd.to_numeric(calls["Initial"])
#puts["Initial"] = underlying["Close"].reindex(puts["Created"]).reset_index(drop=True)
#puts["Initial"] = pd.to_numeric(puts["Initial"])


points_t0 = underlying["Close"].to_numpy()[2:]
points_t0 = np.asarray(points_t0,dtype = np.float64)
points_t1 = np.roll(points_t0,1)

col = np.insert(np.log(points_t0/points_t1), 0, np.nan, axis=0)
col = np.insert(col, 0, np.nan, axis=0)

underlying["Returns"] = col

calls["Returns"] = calls["Created"].map(underlying["Returns"])
#puts["Returns"] = underlying["Returns"].reindex(puts["Created"]).reset_index(drop=True)

spy = yf.Ticker("SPY")
dividends = spy.dividends

annualized_dividend23= (np.mean(dividends["2023"]))/100
annualized_dividend24= (np.mean(dividends["2024"]))/100
annualized_dividend25= (np.mean(dividends["2025"]))/100
annualized_dividend26= (np.mean(dividends["2026"]))/100

divs = [annualized_dividend23, annualized_dividend24, annualized_dividend25, annualized_dividend26]

one_year = timedelta(days=364)
y23 = date(2023, 1, 1)
y24 = date(2024, 1, 1)
y25 = date(2025, 1, 1)
y26 = date(2026, 1, 1)

calls["Rel Price"] = calls["Strike"]/calls["Initial"]
calls["Rel Price"] = calls["Rel Price"].round(4)

tte = 14
ranges = 6.5
calls = calls[calls["TTE(years)"] <= (tte+ranges)/365]


calls = calls.reset_index(drop=True)



calls = calls.sort_values(by = ["Rel Price","Created","TTE(years)"])

c23 = calls[pd.to_datetime(calls["Created"]).dt.date<= y23 + one_year]
c24 = calls[pd.to_datetime(calls["Created"]).dt.date<= y24 + one_year]
c24 = c24[y24 <= pd.to_datetime(c24["Created"]).dt.date]
c25 = calls[pd.to_datetime(calls["Created"]).dt.date<= y25 + one_year]
c25 = c25[y25 <= pd.to_datetime(c25["Created"]).dt.date]
c26 = calls[pd.to_datetime(calls["Created"]).dt.date<= y26 + one_year]
c26 = c26[y26 <= pd.to_datetime(c26["Created"]).dt.date]

#p23 = puts[pd.to_datetime(puts["Created"]).dt.date<= y23 + one_year]
#p24 = puts[pd.to_datetime(puts["Created"]).dt.date<= y24 + one_year]
#p25 = puts[pd.to_datetime(puts["Created"]).dt.date<= y25 + one_year]
#p26 = puts[pd.to_datetime(puts["Created"]).dt.date<= y26 + one_year]
#p24 = p24[y24 <= pd.to_datetime(p24["Created"]).dt.date]
#p25 = p25[y25 <= pd.to_datetime(p25["Created"]).dt.date]
#p26 = p25[y26 <= pd.to_datetime(p26["Created"]).dt.date]

c23["Forward Price"] = c23["Initial"] * np.exp((pd.to_numeric(c23["Rfr"]) - annualized_dividend23)*pd.to_numeric(c23["TTE(years)"]))
c24["Forward Price"] = c24["Initial"] * np.exp((pd.to_numeric(c24["Rfr"]) - annualized_dividend24)*pd.to_numeric(c24["TTE(years)"]))
c25["Forward Price"] = c25["Initial"] * np.exp((pd.to_numeric(c25["Rfr"]) - annualized_dividend25)*pd.to_numeric(c25["TTE(years)"]))
c26["Forward Price"] = c26["Initial"] * np.exp((pd.to_numeric(c26["Rfr"]) - annualized_dividend26)*pd.to_numeric(c26["TTE(years)"]))

#p23["Forward Price"] = p23["Initial"] * np.exp((p23["Rfr"] - annualized_dividend23)*p23["TTE(years)"])
#p24["Forward Price"] = p24["Initial"] * np.exp((p24["Rfr"] - annualized_dividend24)*p24["TTE(years)"])
#p25["Forward Price"] = p25["Initial"] * np.exp((p25["Rfr"] - annualized_dividend25)*p25["TTE(years)"])
#p26["Forward Price"] = p26["Initial"] * np.exp((p26["Rfr"] - annualized_dividend26)*p26["TTE(years)"])





def bs_call(S, K, T, r, q, sigma):
    d1 = (np.log(S/K) + (r-q+sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    return S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)


def implied_volc(C, S, K, T, q, r):
    if T <= 0 or S <= 0 or K <= 0:
        return np.nan

    def objective(sigma):
        return bs_call(S, K, T, r, q, sigma) - C

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return np.nan

def bs_put(S, K, T, r, q, sigma):
    d1 = (np.log(S/K) + (r-q+sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    return -S*np.exp(-q*T)*norm.cdf(-d1) + K*np.exp(-r*T)*norm.cdf(-d2)


def implied_volp(C, S, K, T, q, r):
    if T <= 0 or S <= 0 or K <= 0:
        return np.nan

    def objective(sigma):
        return bs_put(S, K, T, r, q, sigma) - C

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return np.nan

    
clist = [c23,c24,c25,c26]
#plist = [p23,p24,p25,p26]

counter = 0
for df in clist: 
    if df.empty:
        continue

    df["IV"] = [
        implied_volc(C, S, K, T, divs[counter],r)
        for C, S, K, T, r in zip(
            df["Mid"],
            df["Initial"],
            df["Strike"],
            df["TTE(years)"],
            df["Rfr"]
        )
    ]

    dataf = df.copy()

    S = pd.to_numeric(dataf["Initial"])
    K = pd.to_numeric(dataf["Strike"])
    r = pd.to_numeric(dataf["Rfr"])
    sigma = pd.to_numeric(dataf["IV"])
    T = pd.to_numeric(dataf["TTE(years)"])


    d1 = (
        np.log(S / K)
        + (r - float(divs[counter]) + 0.5 * sigma**2) * T
    ) / (sigma * np.sqrt(T))

    df["d1"] = np.exp(float(-divs[counter])*T) * norm.cdf(d1)
    df["vega"] = S * np.exp(-divs[counter]*T) *np.sqrt(T)*norm.pdf(d1)/100
    df["Gamma"] = np.exp(float(-divs[counter])*T) * norm.pdf(d1) / (S*sigma*np.sqrt(T))

    counter += 1

'''
'''
counter = 0
for df in plist:
        
    df["IV"] = [
        implied_volp(C, S, K, T, divs[counter],r)
        for C, S, K, T, r in zip(
            df["Mid"],
            df["Initial"],
            df["Strike"],
            df["TTE(years)"],
            df["Rfr"]
        )
    ]

    dataf = df.copy()
    S = dataf["Initial"]
    K = dataf["Strike"]
    r = dataf["Rfr"]
    sigma = dataf["IV"]
    T = dataf["TTE(years)"]

    d1 = (
        np.log(S / K)
        + (r - divs[i] + 0.5 * sigma**2) * T
    ) / (sigma * np.sqrt(T))

    df["d1"] = np.exp(-divs[counter]*T) * (norm.cdf(d1)-1)
    df["vega"] = S * np.sqrt(T)*norm.pdf(d1)/100

    counter += 1
'''
'''

clist = [c23,c24,c25,c26]
#plist = [p23,p24,p25,p26]

#puts = pd.concat(plist)
calls = pd.concat(clist)


Calls = calls.copy()
calls = calls[(tte - ranges)/365 <= calls["TTE(years)"]]
calls= calls[calls["Rel Price"]<=1.055]
calls = calls[calls["Rel Price"] >= 0.945]
calls["Rel Price"] = calls["Rel Price"].round(3)
calls["K"] = np.log(pd.to_numeric(calls["Initial"])/pd.to_numeric(calls["Forward Price"]))
#puts["K"] = np.log(puts["Strike"]/puts["Forward Price"])


underlying = pd.read_csv("../CSVs/underlying.csv")
underlying = underlying.set_index("Price")

close = underlying["Close"][2:].astype(float)
close.index = pd.to_datetime(close.index)

calls_created = pd.to_datetime(calls["Created"]).dt.normalize()
calls_positions = close.index.get_indexer(calls_created, method="bfill")
#puts_created = pd.to_datetime(puts["Created"]).dt.normalize()
#puts_positions = close.index.get_indexer(puts_created, method="bfill")

log_returns = np.log(close / close.shift(1))
tte_days = (calls["TTE(years)"].to_numpy() * 365).astype(int)

C_RVs = np.full(len(calls), np.nan)
P_RVs = np.full(len(calls), np.nan)


for i, (pos, n) in enumerate(zip(calls_positions, tte_days)):
    if n <= 0:
        C_RVs[i] = 0
    elif pos >= 0:
        # n trading-day returns starting at the first trading day on/after Created
        r = log_returns.iloc[pos + 1 : pos + n + 1].dropna().to_numpy()
        if r.size:
            C_RVs[i] = np.std(r) * np.sqrt(252)
'''
'''
for i, (pos, n) in enumerate(zip(puts_positions, tte_days)):
    if n <= 0:
        P_RVs[i] = 0
    elif pos >= 0:
        # n trading-day returns starting at the first trading day on/after Created
        r = log_returns.iloc[pos + 1 : pos + n + 1].dropna().to_numpy()
        if r.size:
            P_RVs[i] = np.std(r) * np.sqrt(252)
'''
'''
calls["RV"] = C_RVs
#puts["RV"] = P_RVs


#Calls = calls.copy()
#Puts = puts.copy()

calls["TTE(years)"] = calls["TTE(years)"]*365
calls["TTE(years)"] = calls["TTE(years)"].round(0)


calls.to_csv("../CSVs/checker.csv",index = False)
Calls.to_csv("../CSVs/wider.csv",index=False)

'''




calls = pd.read_csv("../CSVs/checker.csv")
Calls = pd.read_csv("../CSVs/wider.csv")
Calls["TTE(years)"] = (Calls["TTE(years)"]*365).round(0)
#calls = pd.read_csv("checker.csv")


dates = pd.Series(calls.sort_values(by = ["Expiration"])["Expiration"]).unique()
moneyness = pd.Series(calls["Rel Price"].round(3)).unique()[1:-1]


tte_14day = np.full((moneyness.size,dates.size), np.nan)
stock_momementum = np.full((dates.size), np.nan)
return_momementum = np.full((dates.size), np.nan)
stock_z = np.full((dates.size), np.nan)
return_z = np.full((dates.size), np.nan)

for x,y in enumerate(dates):

    sub_calls = calls[calls["Expiration"] == y]
    stock_momementum[x] = sub_calls["Initial"].values[0]
    return_momementum[x] = sub_calls["Returns"].values[0]

for x,y in enumerate(stock_momementum):
    stock_window = stock_momementum[max(0, x - 100):x + 1]
    return_window = return_momementum[max(0, x - 100):x + 1]
    stock_z[x] = (y - np.mean(stock_window))/np.std(stock_window)
    return_z[x] = (return_momementum[x] - np.mean(return_window))/np.std(return_window)

over_index = 0
for i in moneyness:
    tolerance = 0.003

    sub_calls = calls[(calls["Rel Price"] >= i - tolerance) &(calls["Rel Price"] <= i + tolerance)]
    #sub_calls = calls[calls["Rel Price"] == i]
    index = 0

    for j in dates:
        sub_sub_calls = sub_calls[sub_calls["Expiration"] == j]

        z = sub_sub_calls[["Created","Expiration","Strike"]]
        df = sub_sub_calls[~z.duplicated(keep="first")]


        sub_sub_calls = sub_sub_calls[sub_sub_calls["TTE(years)"] > 13]
        x = sub_sub_calls["TTE(years)"]
        y = sub_sub_calls["IV"]

        fourteen = sub_sub_calls[sub_sub_calls["TTE(years)"] == 14]
            

        if not(fourteen.empty):
            tte_14day[over_index,index] = fourteen["IV"].values[0]
        elif len(x) > 1:
            z = np.polyfit(x,y,1)
            z = np.poly1d(z)

            if z(14) <= 0:
                tte_14day[over_index,index] = np.nan
            else:
                tte_14day[over_index,index] = z(14)
        elif len(x) == 1:
            tte_14day[over_index,index] = y.values[0]

        else:
            tte_14day[over_index,index] = np.nan

        index += 1

    over_index += 1


IVs = tte_14day
np.savetxt("conf.csv",IVs,delimiter =",")
IV_rolling_avg = np.ones((IVs.shape))
IV_rolling_std = np.ones((IVs.shape))
IV_z = np.ones((IVs.shape))

for i in range(IVs.shape[0]):
    for j in range(IVs.shape[1]):
        window = IVs[i, max(0, j - 100):j + 1]

        IV_rolling_avg[i,j] = np.nanmean(window)
        IV_rolling_std[i,j] = np.nanstd(window)

        std = IV_rolling_std[i,j]
        IV_z[i, j] = ((IVs[i, j] - IV_rolling_avg[i, j]) / std if std > 0 else 0.0)


IVs_t5 = np.roll(IVs,-5,axis = 1)
IVs_t5[:, -5:] = np.nan

intercepts = np.ones((IVs.shape))
slopes = np.ones((IVs.shape))
kappas = np.ones((IVs.shape))
thetas = np.ones((IVs.shape))
model_IVs_t5 = np.ones((IVs.shape))

for i in range(IVs.shape[0]):
    for j in range(IVs.shape[1]):
        if j < 5:
            intercepts[i,j] = np.nan
            slopes[i,j] = np.nan
            kappas[i,j] = np.nan
            thetas[i,j] = (np.nan)
            model_IVs_t5[i,j] = np.nan
            continue
        window = IVs[i, max(0, j - 105):j - 5]
        window_t5s = IVs_t5[i, max(0, j - 105):j - 5]
        
        non_window = window[np.argwhere(~np.isnan(window_t5s) & ~np.isnan(window))]
        non_window_t5s = window_t5s[np.argwhere(~np.isnan(window_t5s) & ~np.isnan(window))]

        result = linregress(non_window,non_window_t5s)

        a = result.intercept[0]
        b = result.slope[0]
        intercepts[i,j] = (a)
        
        slopes[i,j] = (b)
        p = np.poly1d([b,a])
        model_IVs_t5[i,j] = p(IVs[i,j])

        if 0 < b < 1:
            kappa = -np.log(b) / 5
            theta = a / (1 - b)
            kappas[i,j] = (kappa)
            thetas[i,j] = (theta)
            #print("Mean reversion speed:", kappa)
            #print("Long-run mean IV:", theta)
        else:
            thetas[i,j] = (np.nan)
            kappas[i,j] = np.nan
            #print("Coefficients do not imply positive OU mean reversion")

model_IVs_t5 = np.array(model_IVs_t5)

epsilon = IVs_t5-model_IVs_t5

epsilon_mean = np.zeros((epsilon.shape))

distance = np.full(IVs.shape, np.nan)
move = np.full(IVs.shape, np.nan)
half_life = np.full(IVs.shape, np.nan)

for i in range(IVs.shape[1]):

    for j in range(IVs.shape[0]):
        start = max(0, i - 100)
        window = epsilon[j, start:i+1]
        valid = window[~np.isnan(window)]

        if len(valid) < 2 or np.isnan(epsilon[j, i]):
            epsilon_mean[j, i] = np.nan
            std = IV_rolling_std[j,i]
            distance[j, i] = ((IVs[j, i] - thetas[j,i]) / std if std > 0 else 0.0)
            move[j,i] = np.nan if np.isnan(thetas[j,i]) else (1-slopes[j, i])*(thetas[j,i] - IVs[j,i])
            half_life[j,i] = np.log(2)/kappas[j,i]
            continue

        std = valid.std()
        if np.isclose(std, 0):
            epsilon_mean[j, i] = np.nan
        else:
            epsilon_mean[j, i] = (epsilon[j, i] - valid.mean()) / std


        std = IV_rolling_std[j,i]
        distance[j, i] = ((IVs[j, i] - thetas[j,i]) / std if std > 0 else 0.0)
        move[j,i] = np.nan if np.isnan(thetas[j,i]) else (1-slopes[j, i])*(thetas[j,i] - IVs[j,i])
        half_life[j,i] = np.log(2)/kappas[j,i]

epsilon_mean = np.roll(epsilon_mean,5)
epsilon = np.roll(epsilon,5,axis = 1)
epsilon[:, :5] = np.nan

date_moneyness_2d = np.array(np.ones((IVs.shape[1],IVs.shape[0],2)), dtype = str)

for i in range(len(date_moneyness_2d)):

    date_moneyness_2d[i,:,:] = [x for x in zip([dates[i] for _ in range(len(moneyness))],moneyness)]


col_names =  [ 'IVz', 'D', 'eps',"half"]
params = pd.DataFrame(columns = col_names)

counts = {
    "zvalid": 0,
    "hvalid": 0,
    "dvalid": 0,
    "mvalid": 0,
    "cvalid": 0,
    "5valid": 0,
    "vega_positive": 0,
    "half_positive": 0,
    "iv_positive": 0,
    "distance_positive": 0,
    "mu_pass": 0,
    "large_z_pass": 0,
    "both_pass": 0,
    "exit_found": 0
}


calls["Created"] = pd.to_datetime(calls["Created"])
days = pd.Series(calls.sort_values(by = ["Created"])["Created"]).unique()
portfolio = pd.DataFrame({"value":[0.0 for _ in days],"day":days})
portfolio = portfolio.set_index('day')

calls = calls.copy()
calls["Created"] = pd.to_datetime(calls["Created"])
calls["Expiration"] = pd.to_datetime(calls["Expiration"])
calls["rel_r"] = calls["Rel Price"].round(5)

Calls = Calls.copy()
Calls["Created"] = pd.to_datetime(Calls["Created"])
Calls["Expiration"] = pd.to_datetime(Calls["Expiration"])
Calls["strike_f"] = Calls["Strike"].astype(float)
Calls["strike_r"] = Calls["strike_f"].round(3)
Calls["tte_r"] = Calls["TTE(years)"].round(0)

idx_entry = calls.groupby(["Created", "rel_r"]).indices
idx_entry1 = calls.groupby(["Expiration", "rel_r"]).indices
idx_t5    = Calls.groupby(["strike_f", "Expiration", "tte_r"]).indices
idx_path  = Calls.groupby(["Expiration", "strike_r", "Created", "TTE(years)"]).indices

def lookup(frame, index, key):
    pos = index.get(key)
    return frame.iloc[pos] if pos is not None else frame.iloc[0:0]

trades = 0
for x in range(len(moneyness)):
    counter = 0
    bullets = ["",".","..","...","....",".....","......","........",".........","..........."]

    for y in range(len(dates)):
        if y < 14 or y < len(dates)/3: #used for training
            continue
        print("\r Working"+bullets[counter%10],end = "")
        counter += 1
        m = moneyness[x]
        t = dates[y]

        #Function
        ivz = IV_z[x,y]
        eps = epsilon[x,y]
        d = distance[x,y]
        change = move[x,y]
        half = half_life[x,y]
        iv = IVs[x,y]

        result = 0
        result2 = 0
        dS = 0
        Change = 0
        exp = 0
        
        if np.isnan(ivz):    counts["zvalid"] += 1
        if np.isnan(half):   counts["hvalid"] += 1
        if np.isnan(d):      counts["dvalid"] += 1
        if np.isnan(m):      counts["mvalid"] += 1
        if np.isnan(change): counts["cvalid"] += 1


        #Result

        df1 = lookup(calls, idx_entry1, (pd.Timestamp(t), float(round(m,3))))
        df = lookup(calls, idx_entry, (pd.Timestamp(t) - timedelta(days=14), float(round(m,3))))
        if df.empty:
            continue
        trade = pd.Series([])

        ttes = (df["TTE(years)"]).to_list()
        test = 14
        u_counter = 0
        while test+u_counter not in ttes and test+u_counter < 21:
            u_counter += 1
        o_counter = 0
        while test-o_counter not in ttes and test-o_counter > 7:
            o_counter += 1
        winner = "up" if u_counter < o_counter else "down"
        if winner == "up":
            trade = df[df["TTE(years)"] == test+u_counter]
        else:
            trade = df[df["TTE(years)"] == test-o_counter]

        
        if trade.empty:
            print("empty")
            continue

        vega = trade["vega"].values[0]
        vega_signal = (vega-0.2)/0.5 if (vega-0.2)/0.5 > 0 else 0
        half_signal = (-half+6)/5 if (-half+6)/5 < 1.1 else 0
        distance_signal = (d/3) if d/3 > 0 else 2 * d/3
        iv_signal = (ivz/3) if ivz/3 > 0 else 2 * ivz/3

        if return_momementum[int(y-trade["TTE(years)"].values[0])] < -1.5:        momentum = 0.9
        if -1 > return_momementum[int(y-trade["TTE(years)"].values[0])] > -1.5:   momentum = 0.75
        if -0.4>return_momementum[int(y-trade["TTE(years)"].values[0])] > -1:     momentum = 0.3  
        if return_momementum[int(y-trade["TTE(years)"].values[0])] > -.4:         momentum = 0.1
        
        if iv_signal > 1.5:
            iv_signal = -np.abs(iv_signal-3)
        if distance_signal > 1.5:
            distance_signal = -np.abs(distance_signal-3)
        
        rho = 0.85
        corr  = distance_signal * rho + np.sqrt(1-rho**2) * half_signal
        mu = np.mean(np.array([iv_signal*2/3,corr*2/3,momentum*4/3]))
        large_z = (iv_signal + distance_signal) > 1.2


        if mu < 0.6:    counts["mu_pass"] += 1
        if large_z:     counts["large_z_pass"] += 1
        if vega_signal <= 0:    counts["vega_positive"] += 1
        if half_signal <= 0:    counts["half_positive"] += 1
        if distance_signal<= 0: counts["distance_positive"] += 1
        if iv_signal <= 0:      counts["iv_positive"] += 1

        
        trade_t5 = pd.Series([])
        hedge_pnl = []

        ivs = IVs[x,y-3:y+1]
        max_iv = np.max(ivs)

        turning_coeff = 0.9
        turning = iv < turning_coeff* max_iv
        if mu > 0.2 and turning:#return_momementum[int(y-trade["TTE(years)"].values[0])] < 0:
            #print(trade)
            trades+=1
            result = np.nan
            if not(trade.empty):
                exp_date = pd.Timestamp(trade["Expiration"].values[0])    
                strike = float(trade["Strike"].values[0])
                tte0 = trade["TTE(years)"].values[0]

                shift = 5
                trade_t5 = lookup(Calls, idx_t5, (strike, exp_date, tte0 - shift))
                while trade_t5.empty and shift < 9:          
                    shift += 1
                    trade_t5 = lookup(Calls, idx_t5, (strike, exp_date, tte0 - shift))
                
            if not(trade_t5.empty):
                #print(trade,trade_t5)
                volume  = 100*np.min([10,trade["bVolume"].values[0]])
                result = trade["Bid"].values[0] * volume - trade_t5["Ask"].values[0] * volume 
                result2 = (trade_t5["Initial"].values[0] - trade["Initial"].values[0]) * trade["d1"].values[0] * volume 
                total = result+result2
                dS = (trade_t5["Initial"].values[0] - trade["Initial"].values[0])


                delta = trade["d1"].values[0]
                days = 0
                add = 0
                signal_date = trade["Expiration"].values[0]
                prev = trade
                hedge_pnl = []
                while  days + add <= shift:
                    evolution = lookup(Calls, idx_path,
                                (signal_date, trade["Strike"].values[0],
                                 trade["Created"].values[0] + timedelta(days=(days+add)), 
                                 trade["TTE(years)"].values[0] - (days+add)))
                    #evolution = Calls[(Calls["Expiration"] == signal_date) & (Calls["Strike"].round(3) == trade["Strike"].values[0].round(3))& (pd.to_datetime(Calls["Created"]) == pd.to_datetime(trade["Created"]).values[0] + timedelta(days = days+add)) & ((Calls["TTE(years)"]) == trade["TTE(years)"].values[0]-(days+add))]
                    if evolution.empty:
                        add+=1
                        if add > 9:
                            break
                        continue

                    option_value = trade["Bid"].values[0] * volume - evolution["Ask"].values[0] * volume 
                    prev_shares = prev["d1"].values[0]*volume
                    deltaS = evolution["Initial"].values[0] - prev["Initial"].values[0]
                    stock_value = prev_shares * deltaS

                    hedge_pnl.append(stock_value)
                    prev = evolution
                    days+=1  
                    
                    index = pd.Timestamp(pd.to_datetime(evolution["Created"].values[0]))

                    portfolio.loc[index] += option_value
                    portfolio.loc[index] += sum(hedge_pnl)

                    last_index = index

                for a in portfolio.index:
                    if a > last_index:
                        portfolio.loc[a] += result+sum(hedge_pnl)

                exp = ((-trade_t5["IV"].values[0]+trade["IV"].values[0])*trade["vega"].values[0]*volume*100)
                Change = -trade_t5["IV"].values[0]+trade["IV"].values[0]

            if trade_t5.empty:
                trade_t5 = lookup(Calls, idx_t5,
                                              (float(trade["Strike"].values[0]),
                                               pd.Timestamp(date_moneyness_2d[y, x, 0]),
                                               trade["TTE(years)"].values[0] - shift))
                print(trade_t5)
                print(shift)
                counts["exit_found"]+=1
            

        
        pnl = result
        pnl2 = sum(hedge_pnl)
        output = IVs_t5[x,y] 
        #"S0" : trade["Ask"].values[0],"S5": trade_t5["Bid"].values[0],
        new_row = pd.DataFrame({"Date": [trade["Created"].values[0]], 
                                'eps':[eps],"half":[half],
                                "vega":[trade["vega"].values[0]],
                                "RV":trade["RV"].values[0],
                                "dS":dS,
                                "Gamma" : trade["Gamma"].values[0],
                                'IV':[trade["IV"].values[0]],
                                'IVz':[ivz],
                                'D':[d],
                                "reutrnm1":return_momementum[int(y-trade["TTE(years)"].values[0])],
                                "returnm":return_momementum[int(y-trade["TTE(years)"].values[0])],
                                "returnz":return_z[int(y-trade["TTE(years)"].values[0])],
                                "Output":[-1*(Change-trade["IV"].values[0])],
                                "change" : change,
                                "Change":Change,
                                "exp" :exp,
                                "mu":mu,
                                "PnL":round((pnl+pnl2),0)})
        
        params = pd.concat([params,new_row], ignore_index=True)
print()
params = params[params["PnL"] != 0.0]
pd.set_option('display.max_columns', None) 
pd.set_option('display.max_rows', None)
print("Unique Trades(day):",params['Date'].nunique())
print(params['Date'].value_counts())
print()
print("Number of trades:", len(params),trades)
print("Average P&L:", params["PnL"].dropna().mean())
print("Win rate:", (params["PnL"].dropna() > 0).mean())
print("Gross profit:", params.loc[params["PnL"] > 0, "PnL"].sum())
print("Gross loss:", params.loc[params["PnL"] < 0, "PnL"].sum())
print(params["PnL"].sum())
params.to_csv("what.csv")
print("Total observations:", IVs.size)
v = portfolio["value"].diff().dropna()

nv = np.array(v)
nv = np.sqrt(np.sum(nv[nv < 0]**2) / len(v))

sortini = np.sqrt(252) * v.mean()/nv

sharpe = v.mean()/v.std()

ratio = np.sqrt(252) * sharpe

def max_dd(ser):
    max2here = ser.expanding().max()
    dd2here = ser - max2here
    return dd2here.min()

print("Max Drawdown:",max_dd(portfolio["value"]))

print()
print("Sharpe ratio:" ,ratio)

print("Sortini ratio",sortini)
print()


#print(portfolio)




# Triaing period to find mu -> Mu found based on least loss and maximum profit usually mu above a loss streak
m_range = params["mu"].max() - params["mu"].min()
nbins = 20
#bins = [params["mu"].min() +m_range* i/nbins for i in range(0,nbins+1)]
bins = [0 +0.7* i/nbins for i in range(0,nbins+1)]
#print(bins)
labels = [i for i in range(nbins)]

df = pd.DataFrame(params[["PnL","mu"]],columns=['PnL',"mu"])

df['bins'] = pd.cut(df["mu"], bins)
grouping = df.groupby("bins", observed=True).agg(
    n=("PnL", "size"),          
    traded=("PnL", "count"),    
    total=("PnL", "sum"),
    mean=("PnL", "mean"),
    win_rate=("PnL", lambda s: (s.dropna() > 0).mean()),
)
s = df.groupby(pd.cut(df['mu'], bins=bins)).size()
print(grouping)

#plt.plot(grouping["PnL"].to_numpy())
#plt.show()