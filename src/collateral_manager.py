class CollateralManager:
    def __init__(self, initial_collateral):
        self.balance = initial_collateral
        self.total_collateral = initial_collateral
        self.free_collateral = initial_collateral
        
        self.maintenance_margin = 0

        self.account_health = 1.0 # 1.0 == perfect health, 0.0 == liquidated
        self.min_account_health = 1.0
    
    def has_sufficient_margin_to_open_order(self, required_margin: float) -> bool:
        return required_margin <= self.free_collateral
    
    def add_realized_pnl(self, realized_pnl: float):
        self.balance += realized_pnl

    def update(self, open_orders_maintenance_margin, position_maintenance_margin, position_unrealized_pnl,):
        
        self.maintenance_margin = position_maintenance_margin + open_orders_maintenance_margin
        self.total_collateral = self.balance + position_unrealized_pnl
        self.free_collateral = self.balance - self.maintenance_margin

        self._calculate_account_health()
    
    def _calculate_account_health(self):
        if self.total_collateral <= 0 or self.maintenance_margin >= self.total_collateral:
            self.account_health = 0
        else:
            self.account_health = 1 - (self.maintenance_margin / self.total_collateral)

        assert 0 <= self.account_health <= 1.0, f"Account health out of bounds: {self.account_health}, {self.maintenance_margin}/{self.total_collateral}"

        self.min_account_health = min(self.min_account_health, self.account_health)

    def get_lowest_account_health(self):
        return self.min_account_health
    
    def __repr__(self):
        return (f"CollateralManager(total_collateral={self.total_collateral}, "
                f"free margin={self.free_collateral}, "
                f"account_health={self.account_health}, "
                f"lowest_health={self.min_account_health})")