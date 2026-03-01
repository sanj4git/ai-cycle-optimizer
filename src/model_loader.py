"""
ML Model Loader
Plug-in point for the trained XGBoost bootstrap ensemble.
Falls back gracefully if model file is not found.
"""
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "strength_model.joblib")


def load_model():
    """
    Try to load the ML model. Returns None if not available.
    The StrengthEngine will fall back to physics model.
    """
    if not os.path.exists(MODEL_PATH):
        return None

    try:
        import joblib
        import numpy as np
        import pandas as pd

        data = joblib.load(MODEL_PATH)
        return MLModel(data['models'], data['label_encoders'])
    except Exception as e:
        print(f"[model_loader] Could not load ML model: {e}")
        return None


class MLModel:
    """
    Wrapper around the XGBoost bootstrap ensemble.
    Called by StrengthEngine.predict(h, features).
    """
    def __init__(self, models, label_encoders):
        self.models = models
        self.label_encoders = label_encoders

    def predict(self, features: dict, age_hours: float):
        """
        Args:
            features: dict with element properties
            age_hours: float — time point to predict at
        Returns:
            (mean, std): predicted strength mean and std in MPa
        """
        import numpy as np
        import pandas as pd

        row = {
            'element_type': features.get('element_type', 'Slab'),
            'length_mm': features.get('length_mm', 3000),
            'width_mm': features.get('width_mm', 1200),
            'thickness_mm': features.get('thickness_mm', 200),
            'mix_w_c': features.get('wc_ratio', features.get('mix_w_c', 0.4)),
            'cement_type': features.get('cement_type', 'OPC'),
            'admixture': features.get('admixture', 'None'),
            'admixture_dose_pct': features.get('admixture_dose_pct', 0.0),
            'curing_method': features.get('curing_method', 'Ambient'),
            'automation_level': features.get('automation_level', 0),
            'ambient_temp_c': features.get('ambient_temp', features.get('ambient_temp_c', 30)),
            'ambient_rh_pct': features.get('ambient_rh_pct', 60),
            'region': features.get('region', 'North'),
            'monsoon_flag': features.get('monsoon_flag', 0),
            'age_hours': age_hours,
        }

        # Encode categoricals
        for col, le in self.label_encoders.items():
            if col in row:
                try:
                    row[col] = le.transform([row[col]])[0]
                except ValueError:
                    row[col] = 0  # Unknown category fallback

        X = pd.DataFrame([row])
        preds = np.array([m.predict(X)[0] for m in self.models])

        return float(preds.mean()), float(preds.std())
