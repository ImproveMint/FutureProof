from src.order import BaseOrder, OrderDirection

class Position:
    def __init__(self, symbol, direction: OrderDirection = None, entry_price: float = 0, size: float = 0):
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.base_asset_size = size

    def add_filled_order(self, order: BaseOrder) -> float:
        # Adds order to existing position and returns the realized pnl
        
        new_position_size = self._calculate_new_position_size(order)
        
        # Case with no previous position - Filled order becomes position.
        if self.direction is None:
            self.direction = order.direction
            self.entry_price = order.price
            self.size = new_position_size
            return 0
        
        # Case where order increased position
        elif self.direction == order.direction:
            # Newly added order is in the same direction
            self.entry_price = ((self.entry_price * self.base_asset_size) + (order.price * order.size)) / new_position_size
            self.size = new_position_size
            return 0
        
        # Cases where order decreased position
        elif self.direction != order.direction:
            # Order closed position
            if new_position_size == 0:
                self.direction = None
                self.entry_price = 0
            # Order closed and created a position in the opposite direction
            else:
                self.direction = order.direction
                self.entry_price = order.price
            
            self.size = new_position_size
            return self._calculate_added_order_pnl(order)
    
    def calculate_unrealized_pnl(self, mark_price: float) -> float:
        if self.direction == OrderDirection.LONG:
            return self.base_asset_size * (mark_price - self.entry_price)
        elif self.direction == OrderDirection.SHORT:
            return self.base_asset_size * (self.entry_price - mark_price)
        else:
            return 0
    
    def calculate_maintenance_margin(self, mark_price: float, maintenance_margin_ratio: float) -> float:
        return self.base_asset_size * mark_price * maintenance_margin_ratio
    
    def calculate_initial_margin(self, mark_price: float, initial_margin_ratio: float) -> float:
        return self.base_asset_size * mark_price * initial_margin_ratio
    
    def close_position(self, mark_price: float) -> float:
        realized_pnl =  self.calculate_unrealized_pnl(mark_price)

        self.direction = None
        self.entry_price = 0
        self.base_asset_size = 0

        return realized_pnl
    
    def _calculate_new_position_size(self, added_order: BaseOrder) -> float:
        if (self.direction != added_order.direction):
            return abs(self.base_asset_size - added_order.size)
        
        return self.base_asset_size + added_order.size
    
    def _calculate_added_order_pnl(self, added_order: BaseOrder) -> float:
        # calculate the realized PNL if order were filled at its entry price
        if (self.direction is None or self.direction == added_order.direction):
            return 0

        # The position size that's filled must be the smaller of the two
        size_filled = min(added_order.size, self.base_asset_size)

        if self.direction == OrderDirection.LONG:
            return (added_order.price - self.entry_price) * size_filled
        elif self.direction == OrderDirection.SHORT:
            return (self.entry_price - added_order.price) * size_filled
        
    def __repr__(self):
        direction_value = self.direction.value if self.direction is not None else "None"
        return f"Position(symbol={self.symbol}, direction={direction_value}, size={self.base_asset_size}, entry_price={self.entry_price})"
