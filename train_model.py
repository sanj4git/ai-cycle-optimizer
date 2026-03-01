"""
ML Model Training Script
Train XGBoost bootstrap ensemble for concrete strength prediction
Based on ml_model_spec.md.resolved
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from pathlib import Path

# Configuration
DATA_PATH = 'data/precast_dataset.csv'
MODEL_OUTPUT_PATH = 'models/strength_model.joblib'
N_MODELS = 10  # Number of bootstrap models
RANDOM_STATE = 42

def create_long_format_dataset(df):
    """
    Reshape wide format dataset to long format.
    Each row becomes (element, age, strength) observation.
    """
    print("Reshaping data to long format...")
    
    # Strength columns mapping
    strength_cols = {
        'strength_hr24': 24,
        'strength_hr48': 48,
        'strength_hr72': 72,
        'strength_hr96': 96,
        'strength_hr168': 168,
    }
    
    # Feature columns to keep
    feature_cols = [
        'element_type', 'length_mm', 'width_mm', 'thickness_mm',
        'mix_w_c', 'cement_type', 'admixture', 'admixture_dose_pct',
        'curing_method', 'automation_level', 'ambient_temp_c',
        'ambient_rh_pct', 'region', 'monsoon_flag'
    ]
    
    rows = []
    for _, row in df.iterrows():
        for col, age in strength_cols.items():
            r = {f: row[f] for f in feature_cols}
            r['age_hours'] = age
            r['strength_mpa'] = row[col]
            rows.append(r)
    
    df_long = pd.DataFrame(rows)
    print(f"Dataset reshaped: {len(df)} elements × 5 time points = {len(df_long)} observations")
    
    return df_long

def encode_categorical_features(df_long):
    """
    Encode categorical features using LabelEncoder.
    Returns encoded dataframe and label encoders dict.
    """
    print("Encoding categorical features...")
    
    label_encoders = {}
    categorical_cols = ['element_type', 'cement_type', 'admixture', 'curing_method', 'region']
    
    df_encoded = df_long.copy()
    
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_long[col])
        label_encoders[col] = le
        print(f"   - {col}: {len(le.classes_)} categories")
    
    return df_encoded, label_encoders

def train_bootstrap_ensemble(X_train, y_train):
    """
    Train bootstrap ensemble of XGBoost models.
    Returns list of trained models.
    """
    print(f"\nTraining bootstrap ensemble ({N_MODELS} models)...")
    
    models = []
    for i in range(N_MODELS):
        print(f"   Training model {i+1}/{N_MODELS}...", end=" ")
        
        # Bootstrap sample
        idx = np.random.choice(len(X_train), size=len(X_train), replace=True)
        X_bootstrap = X_train.iloc[idx]
        y_bootstrap = y_train.iloc[idx]
        
        # Train XGBoost model
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=i,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
        )
        
        model.fit(X_bootstrap, y_bootstrap, verbose=False)
        models.append(model)
        print("✓")
    
    print(f"Ensemble training complete!")
    return models

def evaluate_model(models, X_test, y_test):
    """
    Evaluate the bootstrap ensemble on test set.
    Returns evaluation metrics.
    """
    print("\nEvaluating model performance...")
    
    # Get predictions from all models
    all_preds = np.array([m.predict(X_test) for m in models])
    
    # Mean prediction (ensemble average)
    mean_preds = all_preds.mean(axis=0)
    
    # Standard deviation (uncertainty estimate)
    std_preds = all_preds.std(axis=0)
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, mean_preds)
    rmse = np.sqrt(mean_squared_error(y_test, mean_preds))
    r2 = r2_score(y_test, mean_preds)
    
    # Calibration: % of test points within ±1σ
    within_1sigma = np.mean(np.abs(y_test.values - mean_preds) <= std_preds) * 100
    within_2sigma = np.mean(np.abs(y_test.values - mean_preds) <= 2*std_preds) * 100
    
    # Print results
    print("\n" + "="*60)
    print("MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"Mean Absolute Error (MAE):     {mae:.3f} MPa")
    print(f"Root Mean Squared Error (RMSE): {rmse:.3f} MPa")
    print(f"R² Score:                       {r2:.4f}")
    print(f"\nUncertainty Calibration:")
    print(f"  Within ±1σ:                   {within_1sigma:.1f}%")
    print(f"  Within ±2σ:                   {within_2sigma:.1f}%")
    print("="*60)
    
    # Target check
    print("\nTarget Metrics Check:")
    print(f"   MAE < 3 MPa:        {'PASS' if mae < 3 else 'FAIL'} ({mae:.3f})")
    print(f"   RMSE < 4 MPa:       {'PASS' if rmse < 4 else 'FAIL'} ({rmse:.3f})")
    print(f"   Calibration > 60%:  {'PASS' if within_1sigma > 60 else 'FAIL'} ({within_1sigma:.1f}%)")
    
    metrics = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'calibration_1sigma': within_1sigma,
        'calibration_2sigma': within_2sigma,
    }
    
    return metrics

def save_model(models, label_encoders, output_path):
    """
    Save trained models and encoders to disk.
    """
    print(f"\nSaving model to {output_path}...")
    
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as joblib
    model_data = {
        'models': models,
        'label_encoders': label_encoders,
        'n_models': len(models),
    }
    
    joblib.dump(model_data, output_path)
    
    # Get file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"Model saved successfully! ({file_size:.2f} MB)")

def main():
    """
    Main training pipeline.
    """
    print("="*60)
    print("AI-CYCLE OPTIMIZER - MODEL TRAINING")
    print("="*60)
    
    # 1. Load raw data
    print(f"\nLoading data from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} elements with {df.shape[1]} features")
    print(f"   Columns: {', '.join(df.columns[:5])}...")
    
    # 2. Reshape to long format
    df_long = create_long_format_dataset(df)
    
    # 3. Encode categorical features
    df_encoded, label_encoders = encode_categorical_features(df_long)
    
    # 4. Split features and target
    print("\nSplitting data...")
    X = df_encoded.drop(columns=['strength_mpa'])
    y = df_encoded['strength_mpa']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set:     {len(X_test)} samples")
    
    # 5. Train bootstrap ensemble
    models = train_bootstrap_ensemble(X_train, y_train)
    
    # 6. Evaluate model
    metrics = evaluate_model(models, X_test, y_test)
    
    # 7. Save model
    save_model(models, label_encoders, MODEL_OUTPUT_PATH)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"\nYou can now run the application with:")
    print(f"   streamlit run app.py")
    print()

if __name__ == "__main__":
    main()
