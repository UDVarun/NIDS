"""
backend/model/predict.py
========================
Loads the trained model from disk and provides predict() and batch_predict().
Imported at startup — model stays in memory for fast inference.
"""

import os
import numpy as np
import joblib

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH   = os.path.join(_SCRIPT_DIR, 'nids_model.pkl')

try:
    _artifacts    = joblib.load(_MODEL_PATH)
    _model        = _artifacts['model']
    _scaler       = _artifacts['scaler']
    _encoders     = _artifacts['encoders']
    _feature_cols = _artifacts['feature_cols']
    MODEL_LOADED  = True
    print(f"✓ ML model loaded from {_MODEL_PATH}")
    print(f"  Features: {len(_feature_cols)} | Trees: {_model.n_estimators}")
except FileNotFoundError:
    MODEL_LOADED = False
    print(f"WARNING: Model not found at {_MODEL_PATH}")
    print("Run: python backend/model/train.py to train the model first.")
except Exception as e:
    MODEL_LOADED = False
    print(f"WARNING: Could not load model: {e}")


def predict(feature_dict: dict) -> dict:
    """
    Returns:
        prediction:    'NORMAL' or 'ATTACK'
        confidence:    float 0.0–1.0
        anomaly_score: raw Isolation Forest score
        is_attack:     bool
    """
    if not MODEL_LOADED:
        return {
            'prediction':    'UNKNOWN',
            'confidence':    0.0,
            'anomaly_score': 0.0,
            'is_attack':     False,
            'error':         'Model not loaded'
        }

    row      = [float(feature_dict.get(col, 0)) for col in _feature_cols]
    X        = np.array(row, dtype=np.float32).reshape(1, -1)
    X_scaled = _scaler.transform(X)
    raw_pred = _model.predict(X_scaled)[0]
    raw_score = float(_model.score_samples(X_scaled)[0])

    # Map raw score [-0.5, +0.5] → confidence [1.0, 0.0]
    confidence = float(max(0.0, min(1.0, (-raw_score + 0.5))))
    is_attack  = (raw_pred == -1)

    return {
        'prediction':    'ATTACK' if is_attack else 'NORMAL',
        'confidence':    round(confidence, 4),
        'anomaly_score': round(raw_score, 6),
        'is_attack':     is_attack
    }


def batch_predict(feature_dicts: list) -> list:
    """Predict on a list of feature dicts efficiently."""
    if not MODEL_LOADED or not feature_dicts:
        return []

    matrix = np.array([
        [float(fd.get(col, 0)) for col in _feature_cols]
        for fd in feature_dicts
    ], dtype=np.float32)

    X_scaled   = _scaler.transform(matrix)
    raw_preds  = _model.predict(X_scaled)
    raw_scores = _model.score_samples(X_scaled)

    results = []
    for pred, score in zip(raw_preds, raw_scores):
        is_attack  = (pred == -1)
        confidence = float(max(0.0, min(1.0, (-float(score) + 0.5))))
        results.append({
            'prediction':    'ATTACK' if is_attack else 'NORMAL',
            'confidence':    round(confidence, 4),
            'anomaly_score': round(float(score), 6),
            'is_attack':     is_attack
        })
    return results
