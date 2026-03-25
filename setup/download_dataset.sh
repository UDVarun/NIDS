#!/bin/bash
# Downloads the NSL-KDD dataset files from GitHub mirror.

DATASET_DIR="data/nsl_kdd"
TRAIN_URL="https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt"
TEST_URL="https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt"

mkdir -p "$DATASET_DIR"

echo "Downloading NSL-KDD training set..."
curl -L "$TRAIN_URL" -o "$DATASET_DIR/KDDTrain+.txt"
echo "✓ Training set downloaded: $(wc -l < $DATASET_DIR/KDDTrain+.txt) records"

echo "Downloading NSL-KDD test set..."
curl -L "$TEST_URL" -o "$DATASET_DIR/KDDTest+.txt"
echo "✓ Test set downloaded: $(wc -l < $DATASET_DIR/KDDTest+.txt) records"

echo "Dataset ready in $DATASET_DIR/"
