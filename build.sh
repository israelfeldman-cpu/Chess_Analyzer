#!/bin/bash
# Build script for Render.com

echo "Installing Stockfish..."

# Download Stockfish
wget https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar

# Extract
tar -xf stockfish-ubuntu-x86-64-avx2.tar

# Create stockfish directory
mkdir -p stockfish

# Move executable
mv stockfish/stockfish-ubuntu-x86-64-avx2 stockfish/stockfish

# Make executable
chmod +x stockfish/stockfish

echo "Stockfish installed successfully"

# Install Python dependencies
pip install -r requirements.txt
