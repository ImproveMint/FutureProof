from src.order import BaseOrder, BracketOrder, OrderDirection
from src.strategy import Strategy

class Test_Strategy(Strategy):
    def hyperparameters(self):
        return [
            {'name': 'profit_margin', 'type': float, 'min': 0.0001, 'max': 0.3, 'default': 0.001},
            {'name': 'is_bull', 'type': int, 'min': 0, 'max': 1, 'default': 1}
        ]
    
    def go_long(self) -> BracketOrder:
        take_profit_price = self.current_price * (1 + self.hp["profit_margin"])
        
        order = BaseOrder(
                    direction = OrderDirection.LONG,
                    price = self.current_price,
                    size = 1,
                    )
        
        return BracketOrder(order, take_profit_price)
    
    def go_short(self) -> BracketOrder:
        take_profit_price = self.current_price * (1 - self.hp["profit_margin"])

        order = BaseOrder(
                    direction = OrderDirection.SHORT,
                    price = self.current_price,
                    size = 1,
                    )

        return BracketOrder(order, take_profit_price)

    def should_short(self):
        if self.hp["is_bull"] == 0 and self.account.position.direction == None or self.account.position.direction == OrderDirection.SHORT:
            return True
        
        return self.account.position.direction == OrderDirection.LONG
    
    def should_long(self):
        if self.hp["is_bull"] == 1 and self.account.position.direction == None or self.account.position.direction == OrderDirection.LONG:
            return True
        return self.account.position.direction == OrderDirection.SHORT