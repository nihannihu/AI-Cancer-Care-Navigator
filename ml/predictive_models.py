from __future__ import annotations

from typing import Dict, Any
import numpy as np
import pandas as pd
# import xgboost as xgb # Uncomment if using xgboost
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Mock training data generation for the demo
# In real life, we load SEER data
def train_mock_models():
    # Synthetic dataset for survival
    # Features: Age, Stage (1-4), ComorbidityIndex (0-5)
    X = np.random.rand(1000, 3)
    X[:, 0] = X[:, 0] * 80 + 20 # Age 20-100
    X[:, 1] = np.random.randint(1, 5, 1000) # Stage 1-4
    X[:, 2] = np.random.randint(0, 6, 1000) # Comorbidity
    
    # Target: 5-year survival (1=Yes, 0=No)
    # Simple logic: Higher stage + higher age = lower survival
    y_prob = 1.0 - (X[:, 1] * 0.15 + (X[:, 0]/100) * 0.2 + X[:, 2] * 0.05)
    y = (y_prob > 0.5).astype(int)
    
    clf_survival = RandomForestClassifier(n_estimators=10)
    clf_survival.fit(X, y)
    
    # Synthetic dataset for side effects (Nausea)
    # Features: Age, ChemoType (0-2), Dosage (0-1)
    X_se = np.random.rand(1000, 3)
    # Target: Nausea (1=High, 0=Low)
    y_se = np.random.randint(0, 2, 1000)
    
    clf_side_effects = RandomForestClassifier(n_estimators=10)
    clf_side_effects.fit(X_se, y_se)
    
    return clf_survival, clf_side_effects

# Train once on import
survival_model, side_effect_model = train_mock_models()

def predict_survival(age: int, stage: int, comorbidities: int) -> Dict[str, Any]:
    try:
        # Input format: [Age, Stage, Comorbidity]
        input_data = np.array([[age, stage, comorbidities]])
        prob = survival_model.predict_proba(input_data)[0][1]
        
        return {
            "5_year_survival_probability": round(prob * 100, 2),
            "risk_score": round(prob * 100, 2),
            "risk_category": "High Risk" if prob < 0.5 else "Low Risk",
            "predicted_diagnosis": "High Survival Chance" if prob > 0.5 else "Low Survival Chance",
            "probabilities": {
                "no_disease": round(prob, 2),
                "disease_present": round(1 - prob, 2)
            }
        }
    except Exception as e:
        return {"error": str(e)}

def predict_side_effects(age: int, chemo_type: int, dosage: float) -> Dict[str, Any]:
    try:
        input_data = np.array([[age, chemo_type, dosage]])
        prob = side_effect_model.predict_proba(input_data)[0][1]
        
        return {
            "nausea_probability": round(prob * 100, 2),
            "hair_loss_severity": "Moderate" if prob > 0.5 else "Low", # Mock logic
            "preventive_measures": [
                "Anti-nausea medication (Ondansetron)",
                "Cold cap therapy for hair loss",
                "Hydration therapy"
            ]
        }
    except Exception as e:
        return {"error": str(e)}
