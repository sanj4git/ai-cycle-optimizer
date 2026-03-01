"""
Strength Prediction Engine
- Physics-informed maturity model: S(t) = (Smax + Bcure) × (1 - e^(-kt)) + ε
- Supports ML model plug-in via model_loader
- Cement type, admixture, and humidity modifiers
"""
import numpy as np

# Cement type multipliers on Smax
CEMENT_FACTORS = {
    "OPC": 1.0,
    "PSC": 0.85,
    "PPC": 0.90,
}

# Admixture effects on rate constant k
ADMIXTURE_K_MODIFIERS = {
    "None": 0.0,
    "Plasticizer": 0.002,
    "Accelerator": 0.008,
    "Retarder": -0.006,
}

# Curing method factors
CURING_FACTORS = {
    "Ambient": 1.0,
    "Moist": 1.10,
    "Steam": 1.25,
}


class StrengthEngine:

    def __init__(self, model=None):
        self.model = model  # MLModel instance (from model_loader.py)

    def physics_model(self, h, wc_ratio, ambient_temp, curing_method="Ambient",
                      cement_type="OPC", admixture="None", admixture_dose_pct=0.0,
                      ambient_rh_pct=60.0):
        """
        Physics-informed strength prediction.
        Returns (mean_strength_MPa, std_MPa)
        """
        # Base rate constant (temperature-dependent)
        k = 0.035 + (ambient_temp - 25) * 0.001

        # Admixture effect on k
        k += ADMIXTURE_K_MODIFIERS.get(admixture, 0.0) * (admixture_dose_pct / 1.0)

        # Ensure k stays positive
        k = max(k, 0.005)

        # Max strength based on w/c ratio and cement type
        Smax = (65 - wc_ratio * 55) * CEMENT_FACTORS.get(cement_type, 1.0)

        # Curing bonus
        curing_factor = CURING_FACTORS.get(curing_method, 1.0)

        # Humidity effect (low humidity reduces hydration efficiency)
        humidity_factor = 0.85 + 0.15 * min(ambient_rh_pct / 80.0, 1.0)

        # Strength model: S(t) = (Smax) × curing × humidity × (1 - e^(-kt))
        mean = Smax * curing_factor * humidity_factor * (1 - np.exp(-k * h))

        # Uncertainty grows with prediction distance, reduces with higher Smax
        std = 1.5 + (0.6 - wc_ratio) * 3 + 0.01 * h

        return float(mean), float(std)

    def predict(self, h, features):
        """
        Predict strength at time h given features dict.

        features dict keys:
            Required: wc_ratio, ambient_temp
            Optional: curing_method, cement_type, admixture, admixture_dose_pct,
                      ambient_rh_pct, element_type, length_mm, width_mm, thickness_mm,
                      automation_level, region, monsoon_flag

        If ML model is loaded, uses ML model. Otherwise falls back to physics.
        Returns: (mean, std)
        """
        if self.model:
            try:
                return self.model.predict(features, h)
            except Exception:
                pass  # Fall back to physics model

        return self.physics_model(
            h,
            features.get("wc_ratio", features.get("mix_w_c", 0.4)),
            features.get("ambient_temp", features.get("ambient_temp_c", 30)),
            curing_method=features.get("curing_method", "Ambient"),
            cement_type=features.get("cement_type", "OPC"),
            admixture=features.get("admixture", "None"),
            admixture_dose_pct=features.get("admixture_dose_pct", 0.0),
            ambient_rh_pct=features.get("ambient_rh_pct", features.get("ambient_rh_pct", 60.0)),
        )

    def predict_curve(self, features, time_points=None):
        """Predict strength curve over multiple time points.
        Returns dict with keys: times, means, uppers, lowers
        """
        if time_points is None:
            time_points = np.linspace(0, 168, 100)

        means, stds = [], []
        for t in time_points:
            m, s = self.predict(t, features)
            means.append(m)
            stds.append(s)

        means = np.array(means)
        stds = np.array(stds)

        return {
            "times": time_points,
            "means": means,
            "uppers": means + stds,
            "lowers": np.maximum(means - stds, 0),
            "stds": stds,
        }