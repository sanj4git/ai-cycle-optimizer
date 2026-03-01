"""
Yard throughput and capacity modeling.
Links demould cycle time directly to yard size and production capacity.
"""

class YardModel:

    def __init__(self, mold_count: int = 20, daily_demand: int = 30):
        self.mold_count = mold_count
        self.daily_demand = daily_demand

    def throughput(self, cycle_time_hours: float) -> float:
        """Maximum daily throughput: MoldCount × (24 / CycleTime)"""
        if cycle_time_hours <= 0:
            return 0.0
        return self.mold_count * (24.0 / cycle_time_hours)

    def utilization(self, cycle_time_hours: float) -> float:
        """Yard utilization = demand / throughput capacity (capped at 100%)"""
        tp = self.throughput(cycle_time_hours)
        if tp <= 0:
            return 1.0
        return min(self.daily_demand / tp, 1.0)

    def congestion_factor(self, cycle_time_hours: float) -> float:
        """
        Congestion penalty: when utilization > 80%, costs increase.
        Returns a multiplier >= 1.0
        """
        util = self.utilization(cycle_time_hours)
        if util <= 0.8:
            return 1.0
        return 1.0 + (util - 0.8) * 2.5  # up to 1.5× at 100%

    def weekly_cost(self, cycle_time_hours: float, yard_day_cost: float) -> float:
        """Weekly yard holding cost"""
        util = self.utilization(cycle_time_hours)
        return yard_day_cost * 7 * util

    def capacity_gap(self, cycle_time_hours: float) -> float:
        """
        How many elements short of demand per day.
        Positive = surplus capacity, negative = shortfall.
        """
        return self.throughput(cycle_time_hours) - self.daily_demand

    def summary(self, cycle_time_hours: float, yard_day_cost: float = 1500) -> dict:
        """Full yard performance summary"""
        tp = self.throughput(cycle_time_hours)
        util = self.utilization(cycle_time_hours)
        gap = self.capacity_gap(cycle_time_hours)
        weekly = self.weekly_cost(cycle_time_hours, yard_day_cost)
        congestion = self.congestion_factor(cycle_time_hours)

        return {
            "throughput": round(tp, 2),
            "utilization_pct": round(util * 100, 1),
            "capacity_gap": round(gap, 1),
            "weekly_cost": round(weekly, 0),
            "congestion_factor": round(congestion, 2),
            "status": "✅ On Track" if gap >= 0 else "⚠️ Under Capacity"
        }
