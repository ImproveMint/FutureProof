from enum import Enum
from typing import Optional

class OrderDirection(Enum):
    SHORT = "SHORT"
    LONG = "LONG"

    def opposite(self):
        return OrderDirection.LONG if self == OrderDirection.SHORT else OrderDirection.SHORT
    
    @classmethod
    def from_string(cls, direction_str: str):
        direction_str = direction_str.upper()
        if direction_str == cls.LONG.value:
            return cls.LONG
        elif direction_str == cls.SHORT.value:
            return cls.SHORT
        else:
            raise ValueError(f"Invalid direction: {direction_str}")

class OrderStatus(Enum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    OFFLINE = "OFFLINE"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    
class BaseOrder:
    _id_counter = 0

    def __init__(self, direction: OrderDirection, size: float, price: float, order_status : OrderStatus = OrderStatus.NEW, uid: Optional[int] = None):
        self.direction = direction
        self.size = size
        self.price = price
        self.order_status = order_status
        self.uid = uid or self._generate_id()

    @classmethod
    def _generate_id(cls) -> int:
        cls._id_counter += 1
        return cls._id_counter

    def __eq__(self, other) -> bool:
        # Two ways to define equality: UID is the same. Or, orders are considered fungible so properties can be checked for equality
        return self.direction == other.direction and self.size == other.size and self.price == other.price

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(uid={self.uid}, direction={self.direction.value}, size={self.size}, price={self.price}, status={self.order_status.value})")

    def __str__(self) -> str:
        return f"Order(uid={self.uid}, direction={self.direction.value}, size={self.size}, price={self.price}, status={self.order_status.value})"
    
class BracketOrder:
    def __init__(self, entry_order: BaseOrder, take_profit_price = None, stop_loss_price = None):
        self.entry_order = entry_order
        self.entry_price = entry_order.price
        self.direction = entry_order.direction
        self.size = entry_order.size
        self.take_profit_price = take_profit_price
        self.stop_loss_price = stop_loss_price