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

rfr = pd.read_csv("rfr.csv")
rfr = rfr.drop(columns = ["realtime_start","realtime_end"])

for i in range(len(rfr["value"])):
    if rfr["value"].loc[i] == ".":
        rfr.loc[i, "value"] = rfr.loc[i-1, "value"]

rfr["date"] = pd.to_datetime(rfr["date"])
rfr = rfr.set_index("date")
calls["Created"] = pd.to_datetime(calls["Created"])

underlying = pd.read_csv("underlying.csv")

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

Calls = calls.copy()
tte = 14
ranges = 6.5
calls = calls[calls["TTE(years)"] <= (tte+ranges)/365]
calls = calls[(tte - ranges)/365 <= calls["TTE(years)"]]

calls = calls.reset_index(drop=True)
calls["Rel Price"] = calls["Strike"]/calls["Initial"]
calls["Rel Price"] = calls["Rel Price"].round(4)

calls= calls[calls["Rel Price"]<=1.055]
calls = calls[calls["Rel Price"] >= 0.945]
calls["Rel Price"] = calls["Rel Price"].round(3)
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

    counter += 1
'''
'''

clist = [c23,c24,c25,c26]
#plist = [p23,p24,p25,p26]

#puts = pd.concat(plist)
calls = pd.concat(clist)

calls["K"] = np.log(pd.to_numeric(calls["Initial"])/pd.to_numeric(calls["Forward Price"]))
#puts["K"] = np.log(puts["Strike"]/puts["Forward Price"])


underlying = pd.read_csv("underlying.csv")
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
            P_RVs[i] = np.std(r) * np.sqrt(252)
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


calls.to_csv("checker.csv",index = False)
Calls.to_csv("wider.csv",index=False)
exit()
'''
def dayoftheweek(x):
    finder = pd.Timestamp(x)
    reference = pd.Timestamp("2026-11-10") # Tuesday

    ref_day = 2
    diff = (reference-finder).days
    modulo = diff % 7
    l = [7,1,2,3,4,5,6]

    return (l[ref_day - modulo])





calls = pd.read_csv("../CSVs/checker.csv")
Calls = pd.read_csv("../CSVs/wider.csv")
print(len(calls))
#calls = pd.read_csv("checker.csv")


dates = pd.Series(calls.sort_values(by = ["Expiration"])["Expiration"]).unique()
print(len(dates))
moneyness = pd.Series(calls["Rel Price"].round(3)).unique()[1:-1]


tte_14day = np.zeros((moneyness.size,dates.size))

over_index = 0
for i in moneyness:
    sub_calls = calls[calls["Rel Price"] == i]
    index = 0

    for j in dates:
        sub_sub_calls = sub_calls[sub_calls["Expiration"] == j]

        z = sub_sub_calls[["Created","Expiration","Strike"]]
        df = sub_sub_calls[~z.duplicated(keep="first")]
        
        x = sub_sub_calls["TTE(years)"]
        y = sub_sub_calls["IV"]
        try:

            if len(x) > 1:
                z = np.polyfit(x,y,1)
                z = np.poly1d(z)

                
                if z(14) <= 0:
                    tte_14day[over_index,index] = np.nan
                else:
                    tte_14day[over_index,index] = z(14)
            elif len(x) == 1 and x.values[0] == 14:
                tte_14day[over_index,index] = y

            else:

                tte_14day[over_index,index] = np.nan

        except Exception as e:
            tte_14day[over_index,index] = np.nan

        index += 1

    over_index += 1


def intersect2D(a, b):
  return np.array([x for x in set(tuple(x) for x in a) & set(tuple(x) for x in b)])

IVs = tte_14day

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


IVs_t5 = np.roll(IVs,-5)

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
            #print("Coefficients do not imply positive OU mean reversion")

model_IVs_t5 = np.array(model_IVs_t5)

epsilon = IVs_t5-model_IVs_t5

epsilon_mean = np.zeros((epsilon.shape))

distance = np.ones((IVs.shape))
move = np.ones((IVs.shape))
half_life = np.ones((IVs.shape))

for i in range(IVs.shape[1]):

    for j in range(IVs.shape[0]):


        std = np.nanstd(epsilon[j,np.max([0,i-100]):i+1])
        if np.isclose(std,0):
            epsilon_mean[j,i] = np.nan
        else:
            epsilon_mean[j,i] = (epsilon[j,i] - np.nanmean(epsilon[j,np.max([0,i-100]):i+1]))/(std)


        std = IV_rolling_std[j,i]
        distance[j, i] = ((IVs[j, i] - thetas[j,i]) / std if std > 0 else 0.0)
        move[j,i] = np.nan if np.isnan(thetas[j,i]) else (1-IVs[j, i])*(thetas[j,i] - IVs[j,i])
        half_life[j,i] = np.log(2)/kappas[j,i]

epsilon_mean = np.roll(epsilon_mean,5)
epsilon = np.roll(epsilon,-5)

date_moneyness_2d = np.array(np.ones((IVs.shape[1],IVs.shape[0],2)), dtype = str)
dates = pd.Series(calls.sort_values(by = ["Expiration"])["Expiration"]).unique()
moneyness = pd.Series(calls["Rel Price"].round(3)).unique()[1:-1]
for i in range(len(date_moneyness_2d)):

    date_moneyness_2d[i,:,:] = [x for x in zip([dates[i] for _ in range(len(moneyness))],moneyness)]


portfolio = []
days  = []
y = "2026-11-01"
count = 0

no_weekends = 0
while pd.Timestamp(y)-timedelta(days = count) > pd.Timestamp("2024-10-07"):
    
    if not(dayoftheweek(pd.Timestamp(y)-timedelta(days = count)) in [6,7]):
        portfolio.append(np.float64(0))
        days.append(pd.Timestamp(pd.Timestamp(y)-timedelta(days = count)))

    count += 1
days.reverse()
pfolio = pd.DataFrame({"value":portfolio,"day":days})
pfolio = pfolio.set_index('day')

print()
print()

def losses(z,weights = True):

    folio = pfolio.copy()
    s1 = np.argwhere((z[0] < IV_z) & (IV_z < z[1]))
    s2 = np.argwhere((z[2] < distance) & (distance < z[3]))
    s3 = np.argwhere((z[4] < epsilon) & (epsilon < z[5]))
    s4 = (np.argwhere(move < 0))
    s5 = np.argwhere((z[6] < half_life) & (half_life < z[7]))

    indices = intersect2D(intersect2D(intersect2D(intersect2D(s1,s2),s4),s3),s5)
    
    date_moneyness_signal = []
    p = []
    l = []
    counter = 0
    bullets = ["",".","..","...","....",".....","......","........",".........","..........."]
    for i in indices:
        print("\r Working"+bullets[counter%10],end = "")
        counter += 1
        x = i[0]
        y = i[1]
        if pd.Timestamp(dates[y]) < pd.Timestamp("2024-10-07") or pd.Timestamp(dates[y]) > pd.Timestamp("2026-10-25"):
            continue
        date_moneyness_signal.append(date_moneyness_2d[y,x,:])
        df = calls[(calls["Expiration"] == date_moneyness_2d[y,x,0]) & (calls["Rel Price"].round(3) == float(date_moneyness_2d[y,x,1]))]

        test = 14
        u_counter = 1
        while df[df["TTE(years)"] == test+u_counter].empty and test+u_counter < 21:
            u_counter += 1
        o_counter = 1
        while df[df["TTE(years)"] == test-o_counter].empty and test-o_counter > 7:
            o_counter += 1

        winner = "up" if u_counter < o_counter else "down"
        if winner == "up":
            trade = df[df["TTE(years)"] == test+u_counter]
        else:
            trade = df[df["TTE(years)"] == test-o_counter]


        trade_t5 = calls[(calls["Strike"].astype(float) == float(trade["Strike"].values[0])) & (calls["Expiration"] == date_moneyness_2d[y,x,0]) & ((calls["TTE(years)"]).round(0) == trade["TTE(years)"].values[0]-5)]
        if not(trade_t5.empty):
            days = 0

            volume  = np.min([5,trade["bVolume"].values[0]])
            result = trade["Bid"].values[0] * volume - trade_t5["Ask"].values[0] * volume + (trade_t5["Initial"].values[0] - trade["Initial"].values[0]) * trade["d1"].values[0] * volume * 100
            delta = trade["d1"].values[0]
            add = 0

            while days < 4:
                
                evolution = Calls[(Calls["Expiration"] == date_moneyness_2d[y,x,0]) & (Calls["Strike"].round(3) == trade["Strike"].values[0].round(3))& (pd.to_datetime(Calls["Created"]) == pd.to_datetime(trade["Created"]).values[0] + timedelta(days = days+add)) & ((Calls["TTE(years)"]*365).round(0) == trade["TTE(years)"].values[0]-(days+add))]
                evolution["TTE(years)"] *= 365

                if evolution.empty:
                    add+=1
                    if add > 9:
                        break

                    continue
   
                index = pd.to_datetime(evolution["Created"].values[0]) - timedelta(days = 0)

                folio.loc[index] += -evolution["Ask"].values[0]*volume
                folio.loc[index] += evolution["Initial"].values[0]*delta*volume
                folio.loc[index] += trade["Bid"].values[0]*volume
                folio.loc[index] += -trade["Initial"].values[0]*delta*volume
                days+=1
                last_index = index

            for a in folio.index:
                if a > last_index:
                    folio.loc[a] += result

            if result > 0:
                p.append(result)
                #print(kappas[x,y],"win")
            if result < 0:
                l.append(result)
                #print(kappas[x,y],"loss")
        #print(i)
        #print(result)


            
    if weights == True:
        w1,w2 = (1,3)
    else:
        w1,w2 = (1,1)
        print()
        print(f"Loss value {np.sum(l):.2f}, number of losing trades {len(l)}")
        print(f"Profit value {np.sum(p):.2f}, number of winning trades {len(p)}")
        print(f"Ratio of losing trades {len(l)/(len(l)+len(p))}")
        print(f"Number of trades {len(l)+len(p)}")
    return ((w1 * np.sum(p) + w2 * np.sum(l)),folio)

train = calls[pd.to_datetime(calls["Expiration"]).dt.normalize() < pd.Timestamp("2024-10-07")].copy()


z1 = [ 1.47515754,  2.90179831,  0.4661562,   4.2971716,  -0.20669647,  1.29084686] # try1
z2 = [ 1.27807456,  4.16766731,  1.60401758,  4.7227877,  -0.34539528,  1.40682094] #full try2
z3 =[ 2.03358897,  2.72279683,  0.78085089,  3.22958016, -0.5909661,   3.13362539] # weighted try3
z4 = [1.01652649, 3.78785348, 0.52344026, 2.51197941, 0.00917258, 1.24904451] #try 4 weighted and minimal

z5 = [ 1.84663146,  2.51114088,  0.64511321,  2.15299062, -1.43427245,  0.89304972] #try 5 trained early weighted and minimal
z6 = [1.81890754,  2.50463034,  0.24497942,  2.68233176, -2.48977968,  1.89139202] # testing of params increasing in number weight follow below
z7 = [ 1.82493208,  2.46584362,  0.66901834,  2.88377333, -1.90288626,  2.35315839]
z8 = [ 1.83308374,  2.35854441,  0.83153633,  4.97620755, -1.02756051,  1.43137493]
z9 = [ 1.83602839,  3.69698885,  0.09768046,  2.13688028, -0.06249926,  0.78258908]
z10 = [1.82890239,  2.08294328,  0.29800668,  2.1520985,  -2.23436803,  0.99544411]


z11 = [ 1.84471616,  2.26367286,  1.25858919,  3.83635251, -0.04167325,  3.36858114,0.75433959,  3.37081815] # final params value
z12 = [ 1.63294105,  2.41734377,  0.72374093,  3.38157722, -1.51984944, 3.60349046,
  0.75433959,  3.37081815]
for i in [z11,z12]:
    m_return,pfolio = losses(i,weights=False)
    #[print(i) for i in pfolio["value"]]
    print(m_return)

    array = np.array(pfolio)


    min = 0
    max = 0
    drawdown = []
    for i in range(len(array)):

        if array[i] < min:
            min = array[i]
        if array[i] > max:
            drawdown.append(max - min)
            max = array[i]
            min = max
            



    v = pfolio["value"].diff().dropna()

    nv = np.array(v)
    nv = np.sqrt(np.sum(nv[nv < 0]**2) / len(v))

    sortini = np.sqrt(252) * v.mean()/nv

    sharpe = v.mean()/v.std()

    ratio = np.sqrt(252) * sharpe
    print()
    print("Sharpe ratio:" ,ratio)
    print("Max drawdown:",np.max(drawdown))
    print("Sortini ratio",sortini)
    print()

exit()







#--------------------------------------------------------------
#Differential evolution training



def objective(z):
    z1_low, z1_high, z2_low, z2_high, z3_low, z3_high,z4_low,z4_high = z
    pnl = []
    neg = []
    if not (z1_low < z1_high and
            z2_low < z2_high and
            z3_low < z3_high and 
            z4_low < z4_high):
        return 1e6

    mask = (
        (z[0] < IV_z) & (IV_z < z[1]) &
        (z[2] < distance) & (distance < z[3]) &
        (z[4] < epsilon) & (epsilon < z[5]) &
        (z[6] < half_life) & (half_life < z[7]) & 
        (move < 0)
    )

    indices = np.argwhere(mask)
    for x, y in indices:
        signal_date = dates[y]
        if pd.Timestamp(dates[y]) > pd.Timestamp("2024-10-07"):
            continue
        signal_moneyness = moneyness[x]

        df = train[(train["Expiration"] == signal_date) & (train["Rel Price"].round(3) == float(signal_moneyness))]
        test = 14
        u_counter = 1
        while df[df["TTE(years)"] == test+u_counter].empty and test+u_counter < 21:
            u_counter += 1
        o_counter = 1
        while df[df["TTE(years)"] == test-o_counter].empty and test-o_counter > 7:
            o_counter += 1

        winner = "up" if u_counter < o_counter else "down"
        if winner == "up":
            trade = df[df["TTE(years)"] == test+u_counter]
        else:
            trade = df[df["TTE(years)"] == test-o_counter]


        trade_t5 = train[(train["Strike"].astype(float) == float(trade["Strike"].values[0])) & (train["Expiration"] == date_moneyness_2d[y,x,0]) & ((train["TTE(years)"]) == trade["TTE(years)"].values[0]-5)]
        if not(trade_t5.empty):
            
            volume  = np.min([100,trade["bVolume"].values[0]])
            result = trade["Bid"].values[0] * volume - trade_t5["Ask"].values[0] * volume + (trade_t5["Initial"].values[0] - trade["Initial"].values[0]) * trade["d1"].values[0] * volume

            if result < 0:
                pnl.append(result*2)
                neg.append(result)
            pnl.append(result)


    if len(pnl) < 30:
        return 1e6

    return -np.sum(pnl) + 40 * len(neg)

bounds = [
    (1, 4), (1, 5),       # IV_z lower and upper
    (0, 3), (1, 5),       # distance lower and upper
    (-3, 2), (-1, 4),      # historical epsilon Z-score bounds
    (0,1),(0,5)
]
def show_progress(xk,b):
    print("Current x:", xk,b)
res = differential_evolution(
    objective,
    bounds,
    popsize=15,
    maxiter=300,
    seed=42,
    polish=False,
    callback = show_progress
)

print("Optimal thresholds:", res.x)
print("Training average P&L:", -res.fun)
print(losses(res.x,weights = False))

    
