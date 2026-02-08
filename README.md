# Interactive Chess Game

A web-based chess game with Stockfish engine integration.

## Features
- Play chess against Stockfish AI
- Visual chess board with click-to-move interface
- Auto-play mode for automatic computer responses
- Move analysis with best move suggestions
- Undo moves
- Move history tracking

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download Stockfish from https://stockfishchess.org/download/

3. Run the app:
```bash
python chess_game.py
```

## Deploy to Render.com

1. Push this code to GitHub
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Render will automatically detect the build script and deploy

## Technologies
- Python Flask
- Stockfish Chess Engine
- Chess.py library
- HTML/CSS/JavaScript
