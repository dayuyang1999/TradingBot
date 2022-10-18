
from typing import Dict
from abc import abstractmethod
from array import array


class Strategy:
    '''
    Base class of strategy
    '''
    
    def __init__(self, name: str):
        self.name = name



    
    @abstractmethod
    def create_signal(self) -> Dict:
        '''
        create signal: 3 list of signal
            - long
            - short
            - empty
        
        if 1 = do this action **after observing the data in this timestamp**
        defalut = 0
        '''
        raise NotImplementedError
        

    def backtest(self) -> None:
        '''
        Non rolling back test
        
        print:
            - success rate
            - total return
        '''
        raise NotImplementedError
        
        
    



        
        
        
        
        
    