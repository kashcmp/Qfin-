import pandas as pd
import numpy as np
import yfinance as yf
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from datetime import timedelta

calls = pd.read_csv("calls.csv")
puts = pd.read_csv("puts.csv")

rfr = pd.read_csv("rfr.csv")
rfr = rfr.drop(columns = ["realtime_start","realtime_end"])

for i in range(len(rfr["value"])):
    if rfr["value"].loc[i] == ".":
        rfr.loc[i, "value"] = rfr.loc[i-1, "value"]

rfr = rfr.set_index("date")

underlying = pd.read_csv("underlying.csv")
underlying = underlying.set_index("Price")


calls["Rfr"] = rfr["value"].reindex(calls["Created"]).reset_index(drop=True)
calls["Rfr"] = pd.to_numeric(calls["Rfr"]) / 100 
puts["Rfr"] = rfr["value"].reindex(puts["Created"]).reset_index(drop=True)
puts["Rfr"] = pd.to_numeric(puts["Rfr"]) / 100 

calls["Initial"] = underlying["Close"].reindex(calls["Created"]).reset_index(drop=True)
calls["Initial"] = pd.to_numeric(calls["Initial"])
puts["Initial"] = underlying["Close"].reindex(puts["Created"]).reset_index(drop=True)
puts["Initial"] = pd.to_numeric(puts["Initial"])


points_t0 = underlying["Close"].to_numpy()[2:]
points_t0 = np.asarray(points_t0,dtype = np.float64)
points_t1 = np.roll(points_t0,1)

underlying = pd.read_csv("underlying.csv")

col = np.insert(np.log(points_t0/points_t1), 0, np.nan, axis=0)
col = np.insert(col, 0, np.nan, axis=0)

underlying["Returns"] = col
underlying = underlying.set_index("Price")

calls["Returns"] = underlying["Returns"].reindex(calls["Created"]).reset_index(drop=True)
puts["Returns"] = underlying["Returns"].reindex(puts["Created"]).reset_index(drop=True)

spy = yf.Ticker("SPY")
dividends = spy.dividends
annualized_dividend = (np.mean(dividends["2025"])+np.mean(dividends["2026"]))/200

calls["Forward Price"] = calls["Initial"] * np.exp((calls["Rfr"] - annualized_dividend)*calls["TTE(years)"])
puts["Forward Price"] = puts["Initial"] * np.exp((puts["Rfr"] - annualized_dividend)*puts["TTE(years)"])

calls["K"] = np.log(calls["Strike"]/calls["Forward Price"])
puts["K"] = np.log(puts["Strike"]/puts["Forward Price"])



def bs_call(S, K, T, r, q, sigma):
    d1 = (np.log(S/K) + (r-q+sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    return S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)


def implied_volc(C, S, K, T, r):
    if T <= 0 or S <= 0 or K <= 0:
        return np.nan

    def objective(sigma):
        return bs_call(S, K, T, r, annualized_dividend, sigma) - C

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return np.nan


def bs_put(S, K, T, r, q, sigma):
    d1 = (np.log(S/K) + (r-q+sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    return -S*np.exp(-q*T)*norm.cdf(-d1) + K*np.exp(-r*T)*norm.cdf(-d2)


def implied_volp(C, S, K, T, r):
    if T <= 0 or S <= 0 or K <= 0:
        return np.nan

    def objective(sigma):
        return bs_put(S, K, T, r, annualized_dividend, sigma) - C

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return np.nan

calls["IV"] = [
    implied_volc(C, S, K, T, r)
    for C, S, K, T, r in zip(
        calls["Mid"],
        calls["Initial"],
        calls["Strike"],
        calls["TTE(years)"],
        calls["Rfr"]
    )
]

puts["IV"] = [
    implied_volp(C, S, K, T, r)
    for C, S, K, T, r in zip(
        puts["Mid"],
        puts["Initial"],
        puts["Strike"],
        puts["TTE(years)"],
        puts["Rfr"]
    )
]

calls = pd.read_csv("calls.csv")
puts = pd.read_csv("puts.csv")


spy = yf.Ticker("SPY")
dividends = spy.dividends
q= (np.mean(dividends["2025"])+np.mean(dividends["2026"]))/200

df = calls.copy()
S = df["Initial"]
K = df["Strike"]
r = df["Rfr"]
sigma = df["IV"]
T = df["TTE(years)"]

d1 = (
    np.log(S / K)
    + (r - q + 0.5 * sigma**2) * T
) / (sigma * np.sqrt(T))



calls["d1"] = np.exp(-q*T) * norm.cdf(d1)


df = puts.copy()
S = df["Initial"]
K = df["Strike"]
r = df["Rfr"]
sigma = df["IV"]
T = df["TTE(years)"]

d1 = (
    np.log(S / K)
    + (r - q + 0.5 * sigma**2) * T
) / (sigma * np.sqrt(T))


puts["d1"] = np.exp(-q*T) * (norm.cdf(d1)-1)
calls.to_csv("calls.csv",index=False)

puts.to_csv("puts.csv",index=False)


calls = pd.read_csv("calls.csv")
puts = pd.read_csv("puts.csv")

underlying = pd.read_csv("underlying.csv")
underlying = underlying.set_index("Price")

close = underlying["Close"][2:].astype(float)
close.index = pd.to_datetime(close.index)

calls_created = pd.to_datetime(calls["Created"]).dt.normalize()
calls_positions = close.index.get_indexer(calls_created, method="bfill")
puts_created = pd.to_datetime(calls["Created"]).dt.normalize()
puts_positions = close.index.get_indexer(puts_created, method="bfill")

log_returns = np.log(close / close.shift(1))
tte_days = (calls["TTE(years)"].to_numpy() * 365).astype(int)

print(tte_days)
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

for i, (pos, n) in enumerate(zip(puts_positions, tte_days)):
    if n <= 0:
        P_RVs[i] = 0
    elif pos >= 0:
        # n trading-day returns starting at the first trading day on/after Created
        r = log_returns.iloc[pos + 1 : pos + n + 1].dropna().to_numpy()
        if r.size:
            P_RVs[i] = np.std(r) * np.sqrt(252)



calls["RV"] = C_RVs
puts["RV"] = P_RVs

calls.to_csv("calls.csv",index = False)

puts.to_csv("puts.csv",index = False)

calls = pd.read_csv("calls.csv")

tte = 14
ranges = 6.5
calls = calls[calls["TTE(years)"] <= (tte+ranges)/365]
calls = calls[(tte - ranges)/365 <= calls["TTE(years)"]]
calls["TTE(years)"] = calls["TTE(years)"]*365
calls["TTE(years)"] = calls["TTE(years)"].round(0)

calls = calls.reset_index(drop=True)
calls["Rel Price"] = calls["Strike"]/calls["Initial"]
calls["Rel Price"] = calls["Rel Price"].round(4)

calls= calls[calls["Rel Price"]<=1.055]
calls = calls[calls["Rel Price"] >= 0.945]
calls["Rel Price"] = calls["Rel Price"].round(3)
calls = calls.sort_values(by = ["Rel Price","Created","TTE(years)"])

#calls.to_csv(f"{tte}day_calls.csv",index = False)

dates = pd.Series(calls.sort_values(by = ["Expiration"])["Expiration"]).unique()

moneyness = pd.Series(calls["Rel Price"].round(3)).unique()[1:-1]


tte_14day = np.zeros((moneyness.size,dates.size))
print(tte_14day.shape)
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
                    print("hello1")
                    tte_14day[over_index,index] = np.nan
                else:
                    tte_14day[over_index,index] = z(14)
            elif len(x) == 1 and x == 14:
                tte_14day[over_index,index] = y

            else:
                tte_14day[over_index,index] = np.nan

        except Exception as e:
            tte_14day[over_index,index] = np.nan

        index += 1

    over_index += 1

print(tte_14day)

np.savetxt("14day_IV.csv", X=tte_14day, header="x, y", delimiter=",")
    