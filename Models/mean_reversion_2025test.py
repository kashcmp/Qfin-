import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
from scipy.stats import linregress


def intersect2D(a, b):
  return np.array([x for x in set(tuple(x) for x in a) & set(tuple(x) for x in b)])

IVs = np.loadtxt("14day_IV.csv",skiprows = 1, delimiter=",")

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

intercepts = []
slopes = []
kappas = []
thetas = []

model_IVs_t5 = []

for i in range(len(IVs)):
    x = []
    y = []
    safe_x = []
    safe_y = []
    for j in range(len(IVs[i])):
        if np.isnan(IVs[i,j]) or np.isnan(IVs_t5[i,j]):
            x.append(np.nan)
            y.append(np.nan)
            continue
        x.append(IVs[i,j])
        y.append(IVs_t5[i,j])
        safe_x.append(IVs[i,j])
        safe_y.append(IVs_t5[i,j])
    result = linregress(safe_x, safe_y)

    a = result.intercept
    b = result.slope

    intercepts.append(a)
    slopes.append(b)

    p = np.poly1d([b,a])
    model_IVs_t5.append([p(a) if not np.isnan(a) else np.nan for a in x])

    if 0 < b < 1:
        kappa = -np.log(b) / 5
        theta = a / (1 - b)
        kappas.append(kappa)
        thetas.append(theta)
        #print("Mean reversion speed:", kappa)
        #print("Long-run mean IV:", theta)
    else:
        print("Coefficients do not imply positive OU mean reversion")

model_IVs_t5 = np.array(model_IVs_t5)[:,:-5]

epsilon = IVs_t5[:,:-5]-model_IVs_t5

epsilon_mean = np.zeros((epsilon.shape))

distance = np.ones((IVs.shape))
move = np.ones((IVs.shape))

for i in range(IVs.shape[1]):
    for j in range(IVs.shape[0]):

        try:
            epsilon_mean[j,i] = (epsilon - np.nanmean(epsilon[j,np.max([0,i-100]):i+1]))/np.nanstd(epsilon[j,np.max([0,i-100]):i+1])
        except Exception:
            pass
        std = IV_rolling_std[j,i]
        distance[j, i] = ((IVs[j, i] - thetas[j]) / std if std > 0 else 0.0)
        move[j,i] = (1-slopes[j])*(thetas[j] - IVs[j,i])




s1 = np.argwhere(IV_z > 2)
s2 = np.argwhere(distance > 2)
s3 = (np.argwhere(np.absolute(epsilon_mean) < 1))
s4 = (np.argwhere(move < -0))


indices = intersect2D(intersect2D(s1,s2),s4)



date_moneyness_2d = np.array(np.ones((IVs.shape[1],IVs.shape[0],2)), dtype = str)


calls = pd.read_csv("14day_calls.csv")

dates = pd.Series(calls.sort_values(by = ["Expiration"])["Expiration"]).unique()
moneyness = pd.Series(calls["Rel Price"].round(3)).unique()[1:-1]


for i in range(len(date_moneyness_2d)):

    date_moneyness_2d[i,:,:] = [x for x in zip([dates[i] for _ in range(len(moneyness))],moneyness)]


Calls = pd.read_csv("calls.csv")
date_moneyness_signal = []

pl = []

for i in indices:
    
    x = i[0]
    y = i[1]

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

    trade_t5 = Calls[(Calls["Strike"].astype(float) == float(trade["Strike"].values[0])) & (Calls["Expiration"] == date_moneyness_2d[y,x,0]) & ((Calls["TTE(years)"]*365).round(1) == trade["TTE(years)"].values[0]-5)]
    trade = Calls[(Calls["Strike"].astype(float) == float(trade["Strike"].values[0])) & (Calls["Expiration"] == date_moneyness_2d[y,x,0]) & ((Calls["TTE(years)"]*365).round(1) == trade["TTE(years)"].values[0])]

    #exit()
    if not(trade_t5.empty):
        #print(trade_t5)
        volume  = 50#np.min(50,trade["Volume"])
        result = trade["Bid"].values[0] * volume - trade_t5["Ask"].values[0] * volume + (trade_t5["Initial"].values[0] - trade["Initial"].values[0]) * trade["d1"].values[0] * volume
        pl.append(result)


        if result < 0:

            print(trade["IV"].values[0] - trade_t5["IV"].values[0])
            print(trade["d1"].values[0])
            print()
            print((trade_t5["Initial"].values[0] - trade["Initial"].values[0]))
            print("neg")
            print()

        else:
            
            print(trade["IV"].values[0] - trade_t5["IV"].values[0])
            print(trade["d1"].values[0])
            print()
            print((trade_t5["Initial"].values[0] - trade["Initial"].values[0]))
            print("pos")
            print()



print(sum(pl),np.mean(pl),np.std(pl))

