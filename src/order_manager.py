from src.order import BaseOrder, OrderDirection
from bintrees import FastRBTree

class OrderManager:

    def __init__(self, symbol):
        self.symbol = symbol
        self.long_orders = OrderGroup()
        self.short_orders = OrderGroup()
        self.orders = {}

    def add_order(self, order: BaseOrder):
        if order.uid in self.orders:
            raise ValueError(f"Order with UID {order.uid} already exists.")
        
        self.orders[order.uid] = order
        order_group = self.long_orders if order.direction == OrderDirection.LONG else self.short_orders
        order_group.add_order(order)
            
    def remove_order(self, order: BaseOrder):
        if order.uid not in self.orders:
            raise ValueError(f"Order {order.uid} not found.")
        
        order_group = self.long_orders if order.direction == OrderDirection.LONG else self.short_orders
        order_group.remove_order(order)
        del self.orders[order.uid]

    def get_triggered_orders(self, low_price: float, high_price: float):
        triggered_orders = []
        
        if not self.long_orders.price_tree.is_empty():
            max_long_price = self.long_orders.price_tree.max_key()
            if low_price <= max_long_price:
                triggered_orders.extend(self.long_orders.get_orders_in_price_range(low_price, max_long_price))
            
        if not self.short_orders.price_tree.is_empty():
            min_short_price = self.short_orders.price_tree.min_key()
            if high_price >= min_short_price:
                triggered_orders.extend(self.short_orders.get_orders_in_price_range(min_short_price, high_price))
        
        return triggered_orders
    
    def clear_orders(self):
        self.long_orders = OrderGroup()
        self.short_orders = OrderGroup()
        self.orders = {}
        
    def print_all_orders(self):
        print(f"Order Manager for {self.symbol}")
        print(f"Total Orders: {len(self.orders)}")
        print("\nDetailed Order List:")
        for order in self.orders.values():
            print(f"  - {order}")

    def __str__(self):
        return f"OrderManager(symbol={self.symbol}, total_orders={len(self.orders)}, long_orders={len(self.long_orders.get_orders())}, short_orders={len(self.short_orders.get_orders())})"

'''
This is a flexible way to group orders that share the same characteristic: direction, filled, canceled, long, short, etc.
Used in OrderManager to seperate long orders from short orders for efficiency
'''
class OrderGroup:
    def __init__(self):
        self.price_tree = FastRBTree()
        self.total_size = 0
        self.total_value = 0

    def add_order(self, order: BaseOrder):
        if order.price not in self.price_tree:
            self.price_tree[order.price] = []
        self.price_tree[order.price].append(order)
        
        self.total_size += order.size
        self.total_value += order.size * order.price
        
    def remove_order(self, order: BaseOrder):
        if order.price in self.price_tree:
            self.price_tree[order.price].remove(order)
            if not self.price_tree[order.price]:
                del self.price_tree[order.price]
        
        self.total_size -= order.size
        self.total_value -= order.size * order.price

    def get_orders_in_price_range(self, low_price: float, high_price: float):
        orders = []
        
        for _, orders_in_range in self.price_tree.item_slice(low_price, high_price):
            orders.extend(orders_in_range)
        return orders
    
    def get_orders(self):
        return [order for orders in self.price_tree.values() for order in orders]

    def print_all_orders(self):
        if self.price_tree.is_empty():
            print("No orders in this OrderGroup.")
            return

        total_orders = sum(len(orders) for orders in self.price_tree.values())
        print(f"Total Orders: {total_orders}")
        print(f"Total Size: {self.total_size}")
        print(f"Total Value: {self.total_value:.2f}")
        print("\nOrders:")
        for _, orders in self.price_tree.items():
            for order in orders:
                print(f"  - UID: {order.uid}, Price: {order.price}, Size: {order.size}, Direction: {order.direction.name}")