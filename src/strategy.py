from abc import ABC
from typing import List, Dict, Optional, final
from src.order import BaseOrder, BracketOrder
from src.account import Account
from src.metrics import Metrics

class Strategy(ABC):
    def __init__(self, account: Account):
        self.account = account
        self.hp: Dict[str, any] = {}  # Hyperparameters
        self.current_price: Optional[float] = None
        self.candles: Optional[List[Dict]] = None
        self.set_default_hyperparameters()
        self.metrics = Metrics(account.collateral_manager.balance)
        
    @final
    def new_candle(self, candles: List[Dict]):
        
        self.metrics.new_candle()
        
        # passing huge lists of candles seems crazy, is it more efficient to pass a single kline and append it
        self.current_price = candles[-1]["open"]
        self.candles = candles
        
        self.before()
        
        if self.account.position.direction:
            self.update_position()
        
        self.should_place_order()
        
        self.after()
        # need to add terminate somehow.
        
    @final
    def set_default_hyperparameters(self):
        """Set the default hyperparameters provided by the subclass."""
        hyperparameters = self.hyperparameters() or []
        
        for param in hyperparameters:
            name = param['name']
            default = param['default']
            self.hp[name] = default
            
    def hyperparameters(self) -> List[Dict]:
        """Define the hyperparameters for the strategy."""

    def before(self):
        """Method called at the beginning of each new candle."""
    
    def after(self):
        """Method called at the end of each candle processing."""

    def update_position(self):
        """Update exit points and add to position if needed."""

    def should_cancel_entry(self):
        """Determine if an open order should be cancelled."""

    def go_long(self) -> BracketOrder:
        """Create a long order."""

    def go_short(self) -> BracketOrder:
        """Create a short order."""

    def should_short(self) -> bool:
        """Determine if a short position should be opened."""
        return False

    def should_long(self) -> bool:
        """Determine if a long position should be opened."""
        return False

    def should_place_order(self):
        if self.should_long():
            order = self.go_long()
            added_order = self.account.add_market_order(order)
            self.metrics.new_trade(added_order)
            
        elif self.should_short():
            order = self.go_short()
            added_order = self.account.add_market_order(order)
            self.metrics.new_trade(added_order)

    def terminate(self):
        """Called when the simulation is done."""

    ### Event handlers ###
    def on_open_position(self, order: BaseOrder):
        """Called when a new position is opened"""
    def on_close_position(self, order: BaseOrder):
        """Called when a position is closed"""
    def on_increased_position(self, order: BaseOrder):
        """Called when position size is increased"""
    def on_decreased_position(self, order: BaseOrder):
        """Called when position size is decreased"""
    def on_cancel(self):
        """Called when order is cancelled"""