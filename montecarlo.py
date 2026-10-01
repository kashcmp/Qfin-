import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm    

t = 36*10
steps = 365*10
dt = 1/steps

rfr = 0.08
n_options = 1000
initial = 295.48
drift = 0#rfr #0
volatility = 1.0625
strike_price = 130

t_total = np.array(np.cumsum(dt*np.ones((steps,))))


fig = make_subplots(rows=3, 
                    cols=1,
                    subplot_titles=(
        f"<sup>Observed path</sup>",
        "<sup>Histogram  Normal Distribution</sup>",
        "<sup>Histogram Log-Normal Distribution</sup>"
    ))

results = []
mc_prediction = []

for i in range(n_options):  
    s = np.ones((steps,))*initial
    ds = (drift*dt+volatility*np.sqrt(dt)*np.random.normal(0,1,steps))
    intermediate = np.cumprod(ds+1)
    
    fig.add_trace(go.Scatter(
                             y = s*intermediate,
                             x = t_total,
                             showlegend = False),
                    row = 1, 
                    col = 1
    )

    results.append(np.exp(-rfr*t*dt)*(initial*intermediate[t-1]))
    mc_prediction.append(np.exp(-rfr*t*dt)*max((((initial*intermediate[t-1])) - strike_price),0))
results = np.array(results)

nbins = 100

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
fig.show()
print(np.mean(results))

