#!/bin/bash
# Build script for Render.com

echo "Installing Stockfish..."

# Download Stockfish
wget -q https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar

# Extract
tar -xf stockfish-ubuntu-x86-64-avx2.tar

# The extracted files create a directory structure
# Find the actual stockfish executable and move it to where we need it
find . -name "stockfish-ubuntu-x86-64-avx2" -type f -exec cp {} stockfish-binary \;

# Create stockfish directory
mkdir -p stockfish

# Move and rename executable
mv stockfish-binary stockfish/stockfish

# Make executable
chmod +x stockfish/stockfish

# Verify it exists
ls -la stockfish/

echo "Stockfish installed successfully"

# Install Python dependencies
pip install -r requirements.txt
