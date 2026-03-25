"""
backend/model/train.py
======================
Trains the Isolation Forest anomaly detection model on the NSL-KDD dataset.
Run once before starting the API: python backend/model/train.py
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT     = os.path.dirname(SCRIPT_DIR)
DATA_DIR         = os.path.join(PROJECT_ROOT, 'data', 'nsl_kdd')
MODEL_OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'nids_model.pkl')

COLUMNS = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes',
    'dst_bytes', 'land', 'wrong_fragment', 'urgent', 'hot',
    'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
    'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
    'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate',
    'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
    'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count',
    'dst_host_srv_count', 'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate',
    'dst_host_serror_rate', 'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
    'dst_host_srv_rerror_rate', 'label', 'difficulty_level'
]

CATEGORICAL_COLS = ['protocol_type', 'service', 'flag']

LABEL_MAP = {
    'normal': 'NORMAL',
    'neptune': 'DOS', 'back': 'DOS', 'land': 'DOS', 'pod': 'DOS',
    'smurf': 'DOS', 'teardrop': 'DOS', 'mailbomb': 'DOS',
    'apache2': 'DOS', 'processtable': 'DOS', 'udpstorm': 'DOS',
    'ipsweep': 'PROBE', 'nmap': 'PROBE', 'portsweep': 'PROBE',
    'satan': 'PROBE', 'mscan': 'PROBE', 'saint': 'PROBE',
    'ftp_write': 'R2L', 'guess_passwd': 'R2L', 'imap': 'R2L',
    'multihop': 'R2L', 'phf': 'R2L', 'spy': 'R2L',
    'warezclient': 'R2L', 'warezmaster': 'R2L', 'sendmail': 'R2L',
    'named': 'R2L', 'snmpattack': 'R2L', 'httptunnel': 'R2L',
    'xlock': 'R2L', 'xsnoop': 'R2L', 'worm': 'R2L',
    'buffer_overflow': 'U2R', 'loadmodule': 'U2R', 'perl': 'U2R',
    'rootkit': 'U2R', 'sqlattack': 'U2R', 'xterm': 'U2R', 'ps': 'U2R'
}


def load_dataset():
    train_path = os.path.join(DATA_DIR, 'KDDTrain+.txt')
    test_path  = os.path.join(DATA_DIR, 'KDDTest+.txt')

    if not os.path.exists(train_path):
        print(f"ERROR: Training file not found at {train_path}")
        print("Run: bash setup/download_dataset.sh")
        sys.exit(1)

    print("Loading training data...")
    df_train = pd.read_csv(train_path, header=None, names=COLUMNS)
    df_test  = pd.read_csv(test_path,  header=None, names=COLUMNS)

    df_train = df_train.drop('difficulty_level', axis=1)
    df_test  = df_test.drop('difficulty_level', axis=1)

    print(f"Train: {len(df_train):,} records | Test: {len(df_test):,} records")
    return df_train, df_test


def encode_categoricals(df_train, df_test):
    encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df_train[col] = le.fit_transform(df_train[col])

        known_classes = set(le.classes_)
        df_test[col] = df_test[col].map(
            lambda x: x if x in known_classes else le.classes_[0]
        )
        df_test[col] = le.transform(df_test[col])
        encoders[col] = le
        print(f"  Encoded '{col}': {len(le.classes_)} unique values")

    return df_train, df_test, encoders


def prepare_labels(df_train, df_test):
    for df in [df_train, df_test]:
        df['attack_category'] = df['label'].map(
            lambda x: LABEL_MAP.get(str(x).strip(), 'UNKNOWN')
        )
        df['is_attack'] = (df['attack_category'] != 'NORMAL').astype(int)

    n_train    = len(df_train)
    n_attacks  = df_train['is_attack'].sum()
    attack_ratio = n_attacks / n_train
    print(f"\nClass distribution in training set:")
    print(f"  Normal:  {n_train - n_attacks:,} ({100*(1-attack_ratio):.1f}%)")
    print(f"  Attack:  {n_attacks:,} ({100*attack_ratio:.1f}%)")
    print(f"  → contamination parameter: {attack_ratio:.2f}")

    return df_train, df_test


def train_model(X_train_scaled):
    print("\nTraining Isolation Forest...")
    print("  n_estimators=200, contamination=0.05, n_jobs=-1")
    print("  This may take 30-90 seconds...")

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled)

    # Calculate score range for normalization
    scores = model.decision_function(X_train_scaled)
    score_min = float(np.min(scores))
    score_max = float(np.max(scores))

    print("  ✓ Training complete")
    return model, score_min, score_max


def evaluate_model(model, X_test_scaled, y_test):
    print("\nEvaluating model on test set...")
    raw_preds = model.predict(X_test_scaled)
    y_pred    = (raw_preds == -1).astype(int)

    print("\n" + "="*50)
    print("CLASSIFICATION REPORT")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"Confusion Matrix:")
    print(f"  True Negatives  (correctly flagged normal): {tn:,}")
    print(f"  False Positives (normal flagged as attack): {fp:,}")
    print(f"  False Negatives (attack missed):            {fn:,}")
    print(f"  True Positives  (attack correctly caught):  {tp:,}")
    print(f"\n  False Positive Rate: {fp/(fp+tn)*100:.1f}%")
    print(f"  Detection Rate:      {tp/(tp+fn)*100:.1f}%")


def save_artifacts(model, scaler, encoders, feature_cols, score_min, score_max):
    artifact = {
        'model':        model,
        'scaler':       scaler,
        'encoders':     encoders,
        'feature_cols': feature_cols,
        'label_map':    LABEL_MAP,
        'columns':      COLUMNS,
        'score_min':    score_min,
        'score_max':    score_max
    }
    print(f"\n✓ Attempting to save model to: {os.path.abspath(MODEL_OUTPUT_PATH)}")
    joblib.dump(artifact, MODEL_OUTPUT_PATH)
    size_mb = os.path.getsize(MODEL_OUTPUT_PATH) / (1024 * 1024)
    print(f"\n✓ Model saved successfully to: {os.path.abspath(MODEL_OUTPUT_PATH)} ({size_mb:.1f} MB)")


def main():
    print("=" * 60)
    print("NIDS Sentinel — ML Training Pipeline")
    print("=" * 60)

    df_train, df_test = load_dataset()

    print("\nEncoding categorical columns...")
    df_train, df_test, encoders = encode_categoricals(df_train, df_test)

    df_train, df_test = prepare_labels(df_train, df_test)

    drop_cols    = ['label', 'attack_category', 'is_attack']
    feature_cols = [c for c in df_train.columns if c not in drop_cols]

    X_train = df_train[feature_cols].values
    y_test  = df_test['is_attack'].values
    X_test  = df_test[feature_cols].values

    print("\nScaling features with StandardScaler...")
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print(f"  Feature matrix shape: {X_train_scaled.shape}")

    model, s_min, s_max = train_model(X_train_scaled)
    evaluate_model(model, X_test_scaled, y_test)
    save_artifacts(model, scaler, encoders, feature_cols, s_min, s_max)

    print("\n✓ Training pipeline complete. Ready to start the API.")


if __name__ == '__main__':
    main()
