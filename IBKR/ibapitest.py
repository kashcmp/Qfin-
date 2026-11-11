from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
from datetime import datetime
import copy

opts = {1001:"SPY  ",
         2001:"APPL ",
         3001:"GOOGL"}
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
        pass

    def connectAck(self):
        print("Connected")

    def tickOptionComputation(self,reqId,tickType,tickAttrib,impliedVol, delta,optPrice, pvDividend,gamma,vega,theta,undPrice):
        super().tickOptionComputation(reqId,tickType,tickAttrib,impliedVol, delta,optPrice, pvDividend,gamma,vega,theta,undPrice)
        
        if tickType == 83:
            pass

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
        contract.strike = 764
        contract.lastTradeDateOrContractMonth = "20261218" 

        contract2 = copy.deepcopy(contract)
        contract2.symbol = "AAPL"
        contract2.strike = 325
        contract2.lastTradeDateOrContractMonth = "20261218" 

        contract3 = copy.deepcopy(contract)
        contract3.symbol = "GOOGL"
        contract3.strike = 330
        contract3.lastTradeDateOrContractMonth = "20261218" 
        
        t = threading.Thread(target = self.run)
        t.start()

        time.sleep(1)
        self.reqMarketDataType(3)
        time.sleep(1)
        self.reqMktData(1001,contract,"",False,False,[])     #100 is id to cancel request,# tick type is blank, live data stream = false,false , no predetermined setttings
        
        
        self.reqMktData(2001,contract2,"",False,False,[]) 
        self.reqMktData(3001,contract3,"",False,False,[]) 

        time.sleep(10)
        self.cancelMktData(1001)
        self.cancelMktData(2001)
        self.cancelMktData(3001)
        self.disconnect()
        t.join()

TradingApp()

