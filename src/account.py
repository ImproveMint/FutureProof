from src.order_manager import OrderManager
from src.order import *
from src.collateral_manager import CollateralManager
from src.position import Position

'''
For now account only handles one symbol
'''
class Account:
    def __init__(self, symbol, starting_balance: float, initial_margin_ratio, maintenance_margin_ratio):
        self.symbol = symbol
        self.initial_margin_ratio = initial_margin_ratio
        self.maintenance_margin_ratio = maintenance_margin_ratio
        
        self.collateral_manager = CollateralManager(starting_balance)
        self.order_manager = OrderManager(symbol)
        self.position = Position(symbol)

    def add_limit_order(self, order: BaseOrder, mark_price: float):
        if order.direction == OrderDirection.LONG and order.price >= mark_price or order.direction == OrderDirection.SHORT and order.price <= mark_price:
            assert False, "Limit order would execute immediately. Review your take_profit price"
            
        self.order_manager.add_order(order)
    
    def add_market_order(self, bracket_order: BracketOrder):

        if self.collateral_manager.has_sufficient_margin_to_open_order(bracket_order.entry_price * bracket_order.size * self.initial_margin_ratio):
            if bracket_order.take_profit_price:
                tp_order = BaseOrder(OrderDirection.opposite(bracket_order.direction), size=bracket_order.size, price=bracket_order.take_profit_price)
                self.add_limit_order(tp_order, bracket_order.entry_price)
            
            if bracket_order.stop_loss_price:
                # Added a stoploss requires new logic to execute stop-market orders.
                # Which means BaseOrders will need a ordertype I think ( maybe we can circumvent with order group)
                # My only issue is I'm trying to keep BaseOrder lean for future optimizations.
                # stop_loss_order = BaseOrder(OrderDirection.opposite(bracket_order.direction), size=bracket_order.size, price=bracket_order.stop_loss_price)
                # self.add_order(stop_loss_order)
                pass
            
            realized_pnl = self.position.add_filled_order(bracket_order.entry_order)
            self.collateral_manager.add_realized_pnl(realized_pnl)

            return bracket_order.entry_order
        
        else:
            # Insufficient margin - Can log or count the number of times we have insufficient margin
            return None
    
    def check_for_filled_orders(self, low_price: float, high_price: float):
        # Given a candle/kline this function fills all the orders that would have been executed between the low and high of that candle
        
        filled_orders = self.order_manager.get_triggered_orders(low_price, high_price)

        for order in filled_orders:
            realized_pnl = self.position.add_filled_order(order) # Filled orders affect position
            self.collateral_manager.add_realized_pnl(realized_pnl) # Filled orders may have realized pnl
            self.order_manager.remove_order(order) # Filled orders should be removed from order manager

    def _calculate_order_maintenance_margin(self, main_mark_price):
        long_orders_total_size = self.order_manager.long_orders.total_size
        short_orders_total_size = self.order_manager.short_orders.total_size
        
        net_long_size = long_orders_total_size + (self.position.size if self.position.direction == OrderDirection.LONG else 0)
        net_short_size = short_orders_total_size + (self.position.size if self.position.direction == OrderDirection.SHORT else 0)
        
        net_size = 0

        if net_long_size >= net_short_size:
            net_size = net_long_size
        else:
            net_size = net_short_size
            
        return net_size * main_mark_price * self.maintenance_margin_ratio
    
    def update_pnl(self, mark_price):
        position_unrealized_pnl = self.position.calculate_unrealized_pnl(mark_price)
        position_maintenance_margin = self.position.calculate_maintenance_margin(mark_price, self.maintenance_margin_ratio)
        open_orders_maintenance_margin = self._calculate_order_maintenance_margin(mark_price)
        
        self.collateral_manager.update(open_orders_maintenance_margin, position_maintenance_margin, position_unrealized_pnl)
    
    def exit_market(self, mark_price):
        # liquidates position and cancels all open orders
        self.order_manager.clear_orders()
        pnl = self.position.close_position(mark_price)
        self.collateral_manager.add_realized_pnl(pnl)
    
    def __str__(self):
        return (f"Account(symbol={self.symbol}, "
                f"Total Collateral={self.collateral_manager.total_collateral})")