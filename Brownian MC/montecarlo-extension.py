import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm    

T = 1.0
steps = int(T * 252)
dt = float(1/steps)

rfr = 0.05
n_sim = int(1e5)
initial = 100
drift = rfr 
volatility = .205
strike_price = 100

choice = "p"
b_choice = "  "
barrier = 0
while True:
    try:
        choice = input("Choose Asian,Lookback or Barrier Options [A,L,B] : ").upper()
        if choice == "B":
            b_choice = input("Choose Barrier Option type [U/D,I/O] (two letters no seperator): ").upper()
            barrier = float(input("Enter Barrier : "))

            if b_choice[0] == "D" and (barrier >= initial):
                pass
            if b_choice[0] == "U" and (barrier <= initial):
                pass
            else:
                break
        if choice in "ALB":
            break
    except Exception as e:
        pass


t_1 = np.linspace(0,T,steps+1)
t_sub = []
[t_sub.append(t_1) for i in range(n_sim)]
t_2 = np.stack(t_sub, axis=0)

Z = np.array([[np.random.normal(0,1) if y > 0 else 0 for y in range(steps+1)] for x in range(n_sim) ])
Z = np.cumsum(Z * np.sqrt(dt) ,axis = 1)

S = np.full((n_sim,steps+1), initial)
S = S * np.exp((drift - (volatility ** 2)/2) * t_2 + volatility * Z)

payoffs = 0
if choice == "A":
    payoffs = np.mean(S,axis = 1) - strike_price
    discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)
if choice == "L":
    payoffs = np.max(S,axis = 1) - strike_price
    discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)
if choice == "B":
    if b_choice == "UI":
        payoffs = np.where(np.max(S,axis=1)<=barrier,0,S[:,-1]) - strike_price
        discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)
    if b_choice == "UO":
        payoffs = np.where(np.max(S,axis=1)>=barrier,0,S[:,-1]) - strike_price
        discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)
    if b_choice == "DI":
        payoffs = np.where(np.min(S,axis=1)>=barrier,0,S[:,-1]) - strike_price
        discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)
    if b_choice == "DO":
        payoffs = np.where(np.min(S,axis=1)<=barrier,0,S[:,-1]) - strike_price
        discounted = np.where(payoffs < 0, 0, payoffs) * np.exp(-rfr*T)

stderror = np.std(discounted,ddof= 1) / np.sqrt(n_sim)
price = np.mean(discounted)
lower = price - 1.96 * stderror
upper =  price + 1.96 * stderror

print()
print(f"Monte Carlo Prediction for {choice} Call Option Price: {price:.3f} in 95% confidence interval [{lower:.4f},{upper:.4f}]")
print()

if choice == "B":
    if b_choice[0] == "U":
        O = np.array(np.mean(np.where(np.where(np.max(S,axis=1)>=barrier,0,S[:,-1]- strike_price) < 0,0,np.where(np.max(S,axis=1)>=barrier,0,S[:,-1]- strike_price))))*np.exp(-rfr*T)
        I = np.array(np.mean(np.where(np.where(np.max(S,axis=1)<=barrier,0,S[:,-1]- strike_price) < 0,0,np.where(np.max(S,axis=1)<=barrier,0,S[:,-1]- strike_price))))*np.exp(-rfr*T)
        print(f"Up and Out price = {O:.3f} + Up and In price = {I:.3f} is const. {O+I:.3f}" )
    if b_choice[0] == "D":
        I = np.array(np.mean(np.where(np.where(np.min(S,axis=1)>=barrier,0,S[:,-1]- strike_price) < 0,0,np.where(np.min(S,axis=1)>=barrier,0,S[:,-1]- strike_price))))*np.exp(-rfr*T)
        O = np.array(np.mean(np.where(np.where(np.min(S,axis=1)<=barrier,0,S[:,-1]- strike_price) < 0,0,np.where(np.min(S,axis=1)<=barrier,0,S[:,-1]- strike_price))))*np.exp(-rfr*T)
        print(f"Down and Out price = {O:.3f} + Down and In price = {I:.3f} is const. {O+I:.3f}" )    
print()

d1 = (np.log(initial/strike_price) + (rfr + 0.5 * volatility**2) * T)/(volatility * np.sqrt(T))
d2 = d1 - volatility * np.sqrt(T)

c = initial * norm.cdf(d1) - strike_price * np.exp(-rfr*T) * norm.cdf(d2)
print(f"Black-Scholes Prediction for equivalent European Option Price: {c}")



fig = make_subplots(rows=1, 
                    cols=3,
                    subplot_titles=(
        "<sup>Asian Option Final vs  Asian Option Average</sup>",
        f"<sup>Barrier Entry {b_choice[0]} and {b_choice[1]}</sup>",
        "<sup>Barrier Price vs Option Price</sup>"
    ))

if choice == "A":
    fig.add_trace(go.Scatter(
                    x =np.mean(S,axis = 1),
                    y = S[:,-1],
                    mode = "markers",
                    marker=dict(
                        size=3,
                        color=np.mean(S,axis = 1),
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(
                            title="Average<br>Price"
                        )
                ),
                customdata=discounted,
                hovertemplate=
                    "Final Price: $%{y:.2f}<br>" +
                    "Average Price: $%{x:.2f}<br>" +
                    "Asian Payoff: $%{customdata:.2f}" +
                    "<extra></extra>"
            ),
            row = 1,
            col = 1
    )
    fig.update_xaxes(title_text ="Asian Mean",row = 1,col = 1)
    fig.update_yaxes(title_text ="Final Price",row = 1,col = 1)

if choice == "B":
    for i in range(5):
        fig.add_trace(go.Scatter(
                        x = t_1,
                        y = S[-1-i,:],
                        mode = "lines",
                        showlegend = False,
                        customdata=[barrier for i in range(len(t_1))],
                        hovertemplate=
                            "Sample Path: $%{y:.2f}<br>" +
                            "Barrier: $%{customdata:.2f}" +
                            "<extra></extra>"
                        ),
                row = 1,
                col = 2
        )
    fig.add_hline(
    y=barrier,
    line_dash="dash",
    annotation_text="Barrier",
    row = 1,
    col = 2
    )
    fig.update_xaxes(title_text ="Price",row = 1,col = 1)
    fig.update_yaxes(title_text ="Time in years",row = 1,col = 1)

    if b_choice == "UO":
            fig.add_trace(go.Scatter(
                            x = np.linspace(0,steps,100) + initial,
                            y = np.array([np.mean(np.where(np.where(np.max(S,axis=1)>=i+initial,0,S[:,-1]- strike_price) < 0,0,np.where(np.max(S,axis=1)>=i+initial,0,S[:,-1]- strike_price))) for i in np.linspace(0,steps,100)] )*np.exp(-rfr*T),
                            mode = "lines",
                            showlegend = False,
                            hovertemplate=
                                "Barrier Price: $%{x:.2f}<br>" +
                                "Option Price: $%{y:.2f}" +
                                "<extra></extra>"
                            ),
                    row = 1,
                    col = 3
            )
    if b_choice == "UI":
        fig.add_trace(go.Scatter(
                        x = np.linspace(0,steps,100) + initial,
                        y = np.array([np.mean(np.where(np.where(np.max(S,axis=1)<=i+initial,0,S[:,-1]- strike_price) < 0,0,np.where(np.max(S,axis=1)<=i+initial,0,S[:,-1]- strike_price))) for i in np.linspace(0,steps,100)] )*np.exp(-rfr*T),
                        mode = "lines",
                        showlegend = False,
                        hovertemplate=
                            "Barrier Price: $%{x:.2f}<br>" +
                            "Option Price: $%{y:.2f}" +
                            "<extra></extra>"
                        ),
                row = 1,
                col = 3
        )

    if b_choice == "DO":
        fig.add_trace(go.Scatter(
                        x = np.linspace(-1 * min(steps,initial),0,100) + initial,
                        y = np.array([np.mean(np.where(np.where(np.min(S,axis=1)<=i+initial,0,S[:,-1]- strike_price) < 0,0,np.where(np.min(S,axis=1)<=i+initial,0,S[:,-1]- strike_price))) for i in np.linspace(-1 * min(steps,initial),0,100)] )*np.exp(-rfr*T),
                        mode = "lines",
                        showlegend = False,
                        hovertemplate=
                            "Barrier Price: $%{x:.2f}<br>" +
                            "Option Price: $%{y:.2f}" +
                            "<extra></extra>"
                        ),
                row = 1,
                col = 3
        )
    if b_choice == "DI":
        fig.add_trace(go.Scatter(
                        x = np.linspace(-min(steps,initial),0,100) + initial,
                        y = np.array([np.mean(np.where(np.where(np.min(S,axis=1)>=i+initial,0,S[:,-1]- strike_price) < 0,0,np.where(np.min(S,axis=1)>=i+initial,0,S[:,-1]- strike_price))) for i in np.linspace(-1 * min(steps,initial),0,100)] )*np.exp(-rfr*T),
                        mode = "lines",
                        showlegend = False,
                        hovertemplate=
                            "Barrier Price: $%{x:.2f}<br>" +
                            "Option Price: $%{y:.2f}" +
                            "<extra></extra>"
                        ),
                row = 1,
                col = 3
        )
    fig.update_xaxes(title_text ="Barrier Price",row = 1,col = 3)
    fig.update_yaxes(title_text ="Option Pricing",row = 1,col = 3)
fig.show()

