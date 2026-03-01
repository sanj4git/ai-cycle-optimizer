"""
Economic Simulation Engine
For each candidate demould time h:
  YardCost(h) = yard_day_cost × (h / 24)
  P_fail(h) = Φ((S_req - μ_h) / σ_h)
  ExpectedCost(h) = YardCost + TreatmentCost + ReworkCost × P_fail
Includes labor, electricity, mold opportunity cost breakdowns.
"""
from scipy.stats import norm


class EconomicEngine:

    def compute(self, h, mean, std,
                required_strength,
                yard_day_cost=1500,
                rework_cost=20000,
                steam_cost_per_hour=100,
                curing_method="Ambient",
                electricity_cost_per_hour=0,
                labor_cost_per_shift=0,
                mold_opportunity_cost=0):
        """
        Compute full cost breakdown for demoulding at time h.
        Returns dict with itemized costs and risk metrics.
        """
        # Yard holding cost
        yard_cost = yard_day_cost * (h / 24)

        # Treatment / steam cost (only if steam curing)
        if curing_method == "Steam":
            treatment_cost = steam_cost_per_hour * h
        else:
            treatment_cost = 0.0

        # Electricity cost
        elec_cost = electricity_cost_per_hour * h

        # Labor cost (assume 8-hour shifts)
        labor_cost = labor_cost_per_shift * (h / 8)

        # Mold opportunity cost (cost of having the mold occupied)
        mold_cost = mold_opportunity_cost * (h / 24)

        # Failure probability
        if std > 0:
            pfail = float(norm.cdf((required_strength - mean) / std))
        else:
            pfail = 0.0 if mean >= required_strength else 1.0

        # Expected rework cost
        rework_expected = rework_cost * pfail

        # Total expected cost
        total = yard_cost + treatment_cost + elec_cost + labor_cost + mold_cost + rework_expected

        return {
            "yard_cost": round(yard_cost, 2),
            "treatment_cost": round(treatment_cost, 2),
            "electricity_cost": round(elec_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "mold_opportunity_cost": round(mold_cost, 2),
            "pfail": round(pfail, 4),
            "rework_expected": round(rework_expected, 2),
            "total_cost": round(total, 2),
        }

    def cost_curve(self, strength_engine, features, required_strength,
                   yard_day_cost=1500, rework_cost=20000, steam_cost_per_hour=100,
                   curing_method="Ambient", electricity_cost_per_hour=0,
                   labor_cost_per_shift=0, mold_opportunity_cost=0,
                   time_points=None):
        """
        Compute cost breakdown across a range of demould times.
        Returns list of dicts.
        """
        import numpy as np
        if time_points is None:
            time_points = np.linspace(6, 168, 80)

        results = []
        for h in time_points:
            mean, std = strength_engine.predict(h, features)
            cost_data = self.compute(
                h, mean, std, required_strength,
                yard_day_cost, rework_cost, steam_cost_per_hour,
                curing_method, electricity_cost_per_hour,
                labor_cost_per_shift, mold_opportunity_cost
            )
            cost_data["time"] = h
            cost_data["mean_strength"] = round(mean, 2)
            cost_data["std_strength"] = round(std, 2)
            results.append(cost_data)

        return results