from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import matplotlib.pyplot as plt
import threading
import time
from datetime import datetime
import copy

opts = {1000:"SPY  ",
         2000:"APPL ",
         3000:"GOOGL"}
types = {10:"Bid           ",
         11:"Ask           ",
         12:"Last Option   ",
         13:"IBKR Model    ",
         80:"Bid(D)        ",
         81:"Ask(D)        ",
         82:"Last Option(D)",
         83:"IBKR Model(D) "}

class Controller(EWrapper):

    def __init__(self):
        self.spy = [[],[],[],[],[],[],[]]
        self.googl = [[],[],[],[],[],[],[]]
        self.aapl = [[],[],[],[],[],[],[]]


    def connectAck(self):
        print("Connected")

    def tickOptionComputation(self,reqId,tickType,tickAttrib,impliedVol, delta,optPrice, pvDividend,gamma,vega,theta,undPrice):
        super().tickOptionComputation(reqId,tickType,tickAttrib,impliedVol, delta,optPrice, pvDividend,gamma,vega,theta,undPrice)

        return_list = (impliedVol,delta,optPrice,gamma,vega,theta,undPrice)
        append_list = [i if i is not None else -1 for i in return_list ]

        if reqId == 1000:
            [self.spy[i].append(append_list[i]) for i in range(0,7) if append_list[i] != -1]
        if reqId == 2000:
            [self.aapl[i].append(append_list[i]) for i in range(0,7) if append_list[i] != -1]
        if reqId == 3000:
            [self.googl[i].append(append_list[i]) for i in range(0,7) if append_list[i] != -1]
        
        timestamp = datetime.now().astimezone()

        if optPrice is None:
            l1 = "Option Price None | "
        else:
            l1 = f"Option Price: {optPrice:.3f} | "

        if undPrice is None:
            l2 = "Underlying Price None | "
        else:
            l2 = f"Underlying Price: {undPrice:.3f} | "

        if impliedVol is None:
            l3 = "IV is None | "
        else:
            l3 = f"IV: {impliedVol:.3f} | "

        print(f"Time: {timestamp:%H:%M:%S.%f} | " + f"{opts[reqId]} | " + f"{types[tickType]} | " + l1 + l2 + l3)
        print()

class Socket(EClient):

    def __init__(self,wrapper):
        super().__init__(wrapper)

class TradingApp(Controller,Socket):

    def __init__(self):
        Controller.__init__(self)
        Socket.__init__(self,wrapper = self)

        self.connect("127.0.0.1", 7497, clientId=1)

        contract = Contract()
        contract.symbol = "SPY"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.right = "C"
        contract.strike = 200
        contract.lastTradeDateOrContractMonth = "20261218" 

        contract2 = copy.deepcopy(contract)
        contract2.symbol = "AAPL"
        contract2.strike = 325
        contract2.lastTradeDateOrContractMonth = "20261218" 

        contract3 = copy.deepcopy(contract)
        contract3.symbol = "GOOGL"
        contract3.strike = 330
        contract3.lastTradeDateOrContractMonth = "20261218" 

        time.sleep(1)
        self.reqMarketDataType(3)
        time.sleep(1)
        self.reqMktData(1000,contract,"",False,False,[]) 
        t = threading.Thread(target = self.run)
        t.start()

    #100 is id to cancel request,# tick type is blank, live data stream = false,false , no predetermined setttings
        
        
        #self.reqMktData(2000,contract2,"",False,False,[]) 
        #self.reqMktData(3000,contract3,"",False,False,[]) 


t = TradingApp()

plt.ion()
graph = plt.plot(range(0,len(t.spy[6])), t.spy[6])[0]
plt.pause(1)

while(True):
    # removing the older graph
    graph.remove()
    # plotting newer graph
    graph = plt.plot(range(0,len(t.spy[6])),t.spy[6],color = 'b')[0]
    plt.pause(0.25)
    print(t.spy[2])
