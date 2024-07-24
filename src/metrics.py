from src.order import BaseOrder, OrderDirection

class Metrics:
    def __init__(self, starting_balance):
        
        self.starting_balance = starting_balance
        
        self.total_trades = 0
        self.total_longs = 0
        self.total_shorts = 0
        
        self.total_fees = 0
        
        self.order_history = []
        
        self.current_candle_index = -1
    
    def new_candle(self):
        self.current_candle_index += 1
    
    def new_trade(self, order: BaseOrder):
        if order is None:
            return
        
        self.total_trades += 1
        
        if order.direction == OrderDirection.LONG:
            self.total_longs += 1
        
        else:
            self.total_shorts += 1
        
        self.order_history.append((order, self.current_candle_index))