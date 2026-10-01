import numpy as np
import matplotlib.pyplot as plt
import threading
import math
import copy
steps = 1000000
t = 100
time = np.linspace(0,t,steps)
dt = t/steps
results = []
lock = threading.Lock()

class Exponential_scale: 
    
    def plotter(self,drift,intial):
        
        s = np.exp((drift)*time)
        with lock:
            results.append(s)

    def __init__(self,drift,intitial):
        a = drift
        b = intitial
        t = threading.Thread(target = self.plotter, args = (a,b),daemon=True)
        t.start()
        self.thread = t

class Geometric_Brownian_Motion:

    def plotter(self,drift,volatility,initial):
        
        s = np.ones((steps,))*initial
        ds = (drift*dt+volatility*np.sqrt(dt)*np.random.normal(0,1,steps))
        
        with lock:
            results.append(initial*np.cumprod(ds+1))
            results.append(initial*np.exp(np.cumsum(ds)))
    def __init__(self,drift,volatility,intitial):
        a = drift
        b = intitial
        c = volatility
        t = threading.Thread(target = self.plotter, args = (a,c,b),daemon=True)
        t.start()
        self.thread = t

class Arithmetic_Brownian_motion:

    def plotter(self,drift,volatility,initial):
        
        s = np.ones((steps,))*initial
        ds = (drift*dt+volatility*np.sqrt(dt)*np.random.normal(0,1,steps))
        
        with lock:
            results.append(s+np.cumsum(ds))
    def __init__(self,drift,volatility,intitial):
        a = drift
        b = intitial
        c = volatility
        t = threading.Thread(target = self.plotter, args = (a,c,b),daemon=True)
        t.start()
        self.thread = t

class Standard_Brownian_motion:

    def plotter(self,initial,nothin):
        
        s = np.ones((steps,))*initial
        ds = (np.random.normal(0,dt,steps))
        
        with lock:
            results.append(s+np.cumsum(ds))
    def __init__(self,initial):
        b = initial
        t = threading.Thread(target = self.plotter, args = (b,0),daemon=True)
        t.start()
        self.thread = t

'''
threads = []

r = Standard_Brownian_motion(0)

for j in np.linspace(-0.5, 0.5, 40):
    i = 0.01
    j = 0.2
    #r1 = Arithmetic_Brownian_motion(i,j, 100)
    r = Standard_Brownian_motion(0)
    threads.append(r.thread) 


for t in threads:
    t.join()
for i in range(0,len(results)):
    plt.subplot(1,2,1)
    #plt.yscale("log")
    plt.plot(time,results[i])
    #plt.subplot(1,2,2)
    #plt.plot(time,results[i+1])


#plt.yscale("log")
plt.show()

'''
for i in range(4):
    drift  = 0.05
    volatility = 0.2
    initial = 200

    s = np.exp((drift)*time) + initial
    results.append(s)

    s = np.ones((steps,))*initial
    ds = (drift*dt+volatility*np.sqrt(dt)*np.random.normal(0,1,steps))
    results.append(initial*np.cumprod(ds+1))
    results.append(initial*np.exp(np.cumsum(ds)))


    s = np.ones((steps,))*initial
    ds = (drift*dt+volatility*np.sqrt(dt)*np.random.normal(0,1,steps))
    results.append(s+np.cumsum(ds))


    s = np.ones((steps,))*0
    ds = np.sqrt(dt)*(np.random.normal(0,1,steps))
    results.append(s+np.cumsum(ds))

fig,ax = plt.subplots(2,2)
fig.suptitle("Brownian Motion")
for i in range(0,len(results),5):

    ax[0,0].plot(time,results[i])
    ax[0, 0].set_title('Exponential drift')
    ax[0,1].plot(time,results[i+1])
    ax[0,1].plot(time,results[i+2])
    ax[0, 1].set_title('Geometric Brownian Motion')
    ax[1,0].plot(time,results[i+3])
    ax[1, 0].set_title('Arithmetic Brownian Motion')
    ax[1,1].plot(time,results[i+4])
    ax[1,1].set_title('Standard Brownian Motion')

for axs in ax.flat:
    axs.set(xlabel='time', ylabel='value')
ax[0,1].set_yscale("log")
plt.show()