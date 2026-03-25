#!/bin/bash
# ============================================================
# NIDS Sentinel — Project Structure Creator
# ============================================================

mkdir -p backend/model backend/db backend/utils
mkdir -p data/nsl_kdd
mkdir -p setup
mkdir -p frontend/src/components frontend/src/hooks frontend/src/styles

touch backend/{feature_extractor,sniffer,app}.py
touch backend/model/{train,predict,__init__}.py
touch backend/db/{database,__init__}.py
touch backend/db/schema.sql
touch backend/utils/{logger,__init__}.py
touch setup/{check_environment,download_dataset}.sh

echo "✓ Folder structure verified"
