#!/bin/bash
# Build script for Render deployment
# Installs PyTorch CPU first to avoid CUDA dependencies (~2GB saved!)

set -e

echo "=== Upgrading pip ==="
pip install --upgrade pip setuptools wheel

echo "=== Installing PyTorch CPU-only (lightweight, ~200MB vs ~2GB with CUDA) ==="
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu

echo "=== Installing remaining dependencies (torch already satisfied) ==="
pip install -r requirements.txt

echo "=== Verifying PyTorch installation ==="
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo "=== Build complete ==="

