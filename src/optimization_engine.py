"""
Multi-Objective Optimization Engine
Objectives:
  - Minimize expected cost
  - Minimize probability of failure
  - Minimize cycle time
Output:
  - Optimal demould time h*
  - Pareto front (Cost vs Risk vs Time)
"""
import numpy as np


class OptimizationEngine:

    def __init__(self, strength_engine, economic_engine):
        self.strength_engine = strength_engine
        self.economic_engine = economic_engine

    def optimize(self, features,
                 required_strength,
                 yard_day_cost=1500,
                 rework_cost=20000,
                 steam_cost_per_hour=100,
                 curing_method="Ambient",
                 electricity_cost_per_hour=0,
                 labor_cost_per_shift=0,
                 mold_opportunity_cost=0,
                 candidate_times=None):
        """
        Evaluate all candidate demould times and find the optimal one.
        Returns (results_list, best_result)
        """
        if candidate_times is None:
            candidate_times = [12, 18, 24, 36, 48, 60, 72, 96, 120]

        results = []
        for h in candidate_times:
            mean, std = self.strength_engine.predict(h, features)

            cost_data = self.economic_engine.compute(
                h, mean, std, required_strength,
                yard_day_cost, rework_cost, steam_cost_per_hour,
                curing_method, electricity_cost_per_hour,
                labor_cost_per_shift, mold_opportunity_cost
            )

            results.append({
                "time_h": h,
                "mean_strength": round(mean, 2),
                "std_strength": round(std, 2),
                "risk_pct": round(cost_data["pfail"] * 100, 2),
                "yard_cost": cost_data["yard_cost"],
                "treatment_cost": cost_data["treatment_cost"],
                "rework_expected": cost_data["rework_expected"],
                "total_cost": cost_data["total_cost"],
                "meets_strength": mean >= required_strength,
            })

        # Best = lowest total cost among those that meet strength
        viable = [r for r in results if r["meets_strength"]]
        if viable:
            best = min(viable, key=lambda x: x["total_cost"])
        else:
            # If none meet strength, pick lowest risk
            best = min(results, key=lambda x: x["risk_pct"])

        best["recommended"] = True
        return results, best

    def pareto_front(self, results):
        """
        Extract Pareto-optimal solutions (non-dominated on cost, risk, time).
        Returns list of Pareto-optimal result dicts.
        """
        pareto = []
        for r in results:
            dominated = False
            for q in results:
                if (q["total_cost"] <= r["total_cost"] and
                    q["risk_pct"] <= r["risk_pct"] and
                    q["time_h"] <= r["time_h"] and
                    (q["total_cost"] < r["total_cost"] or
                     q["risk_pct"] < r["risk_pct"] or
                     q["time_h"] < r["time_h"])):
                    dominated = True
                    break
            if not dominated:
                pareto.append(r)
        return pareto

    def sensitivity_analysis(self, features, required_strength,
                             yard_day_cost, rework_cost, steam_cost_per_hour,
                             curing_method="Ambient"):
        """
        Tornado chart data: how much does +10% change in each parameter
        affect the optimal cost?
        """
        # Base case
        _, base_best = self.optimize(
            features, required_strength, yard_day_cost,
            rework_cost, steam_cost_per_hour, curing_method
        )
        base_cost = base_best["total_cost"]

        sensitivities = []
        params = {
            "Temperature (+5°C)": {"ambient_temp": features.get("ambient_temp", 30) + 5},
            "Temperature (-5°C)": {"ambient_temp": features.get("ambient_temp", 30) - 5},
            "W/C Ratio (+0.05)": {"wc_ratio": features.get("wc_ratio", 0.4) + 0.05},
            "W/C Ratio (-0.05)": {"wc_ratio": features.get("wc_ratio", 0.4) - 0.05},
            "Yard Cost (+20%)": {},
            "Rework Cost (+20%)": {},
        }

        for label, feat_override in params.items():
            test_features = dict(features)
            test_features.update(feat_override)

            test_yard = yard_day_cost * 1.2 if "Yard Cost" in label else yard_day_cost
            test_rework = rework_cost * 1.2 if "Rework Cost" in label else rework_cost

            _, test_best = self.optimize(
                test_features, required_strength, test_yard,
                test_rework, steam_cost_per_hour, curing_method
            )
            delta = test_best["total_cost"] - base_cost
            sensitivities.append({
                "parameter": label,
                "delta_cost": round(delta, 2),
                "pct_change": round(delta / base_cost * 100, 2) if base_cost > 0 else 0,
            })

        return sensitivities