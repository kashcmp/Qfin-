import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm    

T = 1.0
steps = int(T * 252)
dt = 1/steps

rfr = 0.0525
n_sim = int(1e5)
initial = 778.52
drift = rfr 
volatility = 0.272
strike_price = 540

'''
3d paths with n-sim varied aswell
t_1 = np.arange(0,T+dt,dt)

t_sub = []
[t_sub.append(t_1) for i in range(n_sim)]

t_2 = np.stack(t_sub, axis=1)

t_total =  np.tril(np.ones((steps+1,n_sim,n_sim)) *  t_2[:,:,None])

#x = np.linspace(np.ones((n_sim,steps)),np.ones((n_sim,steps)) * T, steps, axis = 2)

Z = np.array([[[np.random.normal(0,1) for _ in range(n_sim)] for _ in range(n_sim) ] for _ in range(steps+1)])
Z = np.tril(np.cumsum(Z * np.sqrt(dt) ,axis = 0))

S = np.tril(np.full((steps+1,n_sim,n_sim), initial))

S = S * np.exp((drift - (volatility ** 2)/2) * t_total + volatility * Z)

O = S[-1,:,:] - strike_price
O = np.where(O <= 0, np.nan, O)

F = np.nanmean(O,axis = 1)
F *= np.exp(-rfr*T)


results = S[-1,-1,:]
'''
Z1 = np.random.normal(0,1,n_sim)
S = initial * np.exp((drift - (volatility**2)/2) * T + volatility * Z1) - strike_price
S = np.where(S < 0,0,S)

results = initial * np.exp((drift - (volatility**2)/2) * T + volatility * Z1)
coverg_results = S * np.exp(-rfr* T)
mu = np.mean(S)

prediciton = mu * np.exp(-rfr*T)

print(f"Monte Carlo Prediction for European Call Option Price: {prediciton}")
    

fig = make_subplots(rows=3, 
                    cols=1,
                    subplot_titles=(
        f"<sup>Convergence of Black Scholes vs Monte Carlo</sup>",
        "<sup>Histogram  Normal Distribution</sup>",
        "<sup>Histogram Log-Normal Distribution</sup>"
    ))

d1 = (np.log(initial/strike_price) + (rfr + 0.5 * volatility**2) * T)/(volatility * np.sqrt(T))
d2 = d1 - volatility * np.sqrt(T)

c = initial * norm.cdf(d1) - strike_price * np.exp(-rfr*T) * norm.cdf(d2)
print(f"Black-Scholes Prediction for European Call Option Price: {c}")

#-----------------------------------------------------------------------------
# Graphing
nbins = 100
fig.add_trace(go.Scatter(
                            x = [n for n in range(n_sim)],
                             y = [np.mean(np.maximum(initial * np.exp((drift - (volatility**2)/2) * T + volatility * np.random.normal(0,1,n)) - strike_price ,0)) * np.exp(-rfr* T) - c for n in range(1,n_sim)]
                        ),              
              row = 1,
              col = 1
)

fig.add_trace(go.Histogram(
                             x = np.log(results),
                             nbinsx = nbins,
                             histnorm="probability density",),              
              row = 2,
              col = 1
)

mu = np.mean(np.log(results))
sigma = np.std(np.log(results))

x = np.linspace(np.min(np.log(results)), np.max(np.log(results)), 1000)
pdf = norm.pdf(x, mu, sigma)
y = pdf

fig.add_trace(go.Scatter(
                x = x,
                y = y
                ),
                row = 2,
                col = 1
)


fig.add_trace(go.Histogram(
                             x = (results),
                             nbinsx = nbins,
                             histnorm="probability density",),
                             
                             
              row = 3,
              col = 1
)

mu = np.mean(np.log(results))
sigma = np.std(np.log(results))

x = np.linspace(np.min(results), np.max(results), 1000)
y = (1 / (x * sigma * np.sqrt(2*np.pi))) * \
    np.exp(-((np.log(x) - mu)**2) / (2*sigma**2))

fig.add_trace(go.Scatter(
                x = x,
                y = y
                ),
                row = 3,
                col = 1
)

fig.update_xaxes(type="log", row=1, col=1)
fig.show()

