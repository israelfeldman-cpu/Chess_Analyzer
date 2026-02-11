import chess
import chess.engine
import chess.svg
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
import webbrowser
import threading
import time
import os
from version import __version__

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chess-game-secret-key-change-in-production')

class ChessGame:
    def __init__(self, stockfish_path):
        self.board = chess.Board()
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        
        # Optimize Stockfish for speed
        self.engine.configure({"Threads": 2, "Hash": 128, "Skill Level": 15})
        
        self.move_history = []
    
    def get_board_svg(self, selected_square=None, legal_moves=None):
        if selected_square or legal_moves:
            squares_to_highlight = chess.SquareSet()
            
            if selected_square:
                try:
                    sq = chess.parse_square(selected_square)
                    squares_to_highlight.add(sq)
                except:
                    pass
            
            if legal_moves:
                for move_square in legal_moves:
                    try:
                        sq = chess.parse_square(move_square)
                        squares_to_highlight.add(sq)
                    except:
                        pass
            
            fill_colors = {}
            if selected_square:
                try:
                    sq = chess.parse_square(selected_square)
                    fill_colors[sq] = '#ffeb3b'
                except:
                    pass
            
            if legal_moves:
                for move_square in legal_moves:
                    try:
                        sq = chess.parse_square(move_square)
                        fill_colors[sq] = '#81c784'
                    except:
                        pass
            
            return chess.svg.board(
                self.board, 
                size=600,
                squares=squares_to_highlight,
                fill=fill_colors
            )
        
        return chess.svg.board(self.board, size=600)
    
    def make_move(self, move_uci):
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                san = self.board.san(move)
                self.board.push(move)
                self.move_history.append(san)
                return {"success": True, "move": san}
            else:
                return {"success": False, "error": "Illegal move"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_best_move(self, time_limit=60.0):
        if self.board.is_game_over():
            return None
        
        # Cap at 30 seconds to fit within Render's ~70s HTTP timeout
        # (leaving buffer for network overhead)
        time_limit = min(time_limit, 30.0)
        
        # Use only time limit for predictable results
        result = self.engine.analyse(
            self.board, 
            chess.engine.Limit(time=time_limit),
            multipv=1
        )
        
        best_moves = []
        # When multipv=1, result is a single info dict, not a list
        if not isinstance(result, list):
            result = [result]
            
        for info in result:
            score = info["score"].relative
            pv = info["pv"]
            
            if score.is_mate():
                eval_str = f"Mate in {score.mate()}"
            else:
                cp = score.score() / 100
                eval_str = f"{cp:+.2f}"
            
            move_san = self.board.san(pv[0])
            best_moves.append({
                "move": move_san,
                "uci": pv[0].uci(),
                "eval": eval_str,
                "line": " ".join([self.board.san(m) for m in pv[:5]])
            })
        
        return best_moves
    
    def get_computer_move(self, difficulty='normal'):
        """Get computer move - returns immediately with random move as fallback"""
        if self.board.is_game_over():
            return None
        
        # Immediate fallback: return a random legal move
        # Stockfish is not working reliably on Render deployment
        import random
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None
    
    def get_legal_moves(self, from_square):
        try:
            square = chess.parse_square(from_square)
            legal_moves = []
            for move in self.board.legal_moves:
                if move.from_square == square:
                    legal_moves.append(chess.square_name(move.to_square))
            return legal_moves
        except:
            return []
    
    def reset(self):
        self.board.reset()
        self.move_history = []
    
    def undo_move(self):
        try:
            if len(self.board.move_stack) > 0:
                self.board.pop()
                if len(self.move_history) > 0:
                    self.move_history.pop()
                return {"success": True}
            else:
                return {"success": False, "error": "No moves to undo"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_game_status(self):
        if self.board.is_checkmate():
            return "Checkmate!"
        elif self.board.is_stalemate():
            return "Stalemate!"
        elif self.board.is_insufficient_material():
            return "Draw - Insufficient material"
        elif self.board.is_fifty_moves():
            return "Draw - Fifty move rule"
        elif self.board.is_repetition():
            return "Draw - Threefold repetition"
        elif self.board.is_check():
            return "Check!"
        return ""
    
    def get_state(self):
        """Get current game state for session storage"""
        state = {
            'fen': self.board.fen(),
            'history': self.move_history,
            'moves_uci': [move.uci() for move in self.board.move_stack]
        }
        print(f"Saving state - FEN: {state['fen']}, moves: {len(state['moves_uci'])}")
        return state
    
    def set_state(self, state):
        """Restore game state from session"""
        if state:
            print(f"Loading state - FEN: {state.get('fen', 'none')}, moves: {len(state.get('moves_uci', []))}")
            try:
                # Validate the FEN first if present
                if 'fen' in state:
                    try:
                        # Test if FEN is valid
                        test_board = chess.Board(state['fen'])
                    except ValueError as ve:
                        print(f"Warning: Corrupted FEN detected: {state['fen']}, error: {ve}")
                        print("Resetting to initial position...")
                        self.board.reset()
                        self.move_history = []
                        return
                
                # Restore from move list if available (preserves full move stack)
                if 'moves_uci' in state and state['moves_uci']:
                    self.board.reset()
                    for move_uci in state['moves_uci']:
                        try:
                            move = chess.Move.from_uci(move_uci)
                            if move in self.board.legal_moves:
                                self.board.push(move)
                            else:
                                print(f"Warning: Illegal move in state: {move_uci}")
                                break
                        except ValueError as e:
                            print(f"Warning: Invalid UCI move: {move_uci}, error: {e}")
                            break
                elif 'fen' in state:
                    # Fallback to FEN (loses move stack)
                    self.board.set_fen(state['fen'])
                
                self.move_history = state.get('history', [])
            except Exception as e:
                print(f"Error restoring state: {e}, resetting to initial position")
                self.board.reset()
                self.move_history = []
    
    def close(self):
        self.engine.quit()

def find_stockfish():
    import os
    print("=" * 60)
    print("Searching for Stockfish...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    if os.path.exists('stockfish'):
        print(f"Stockfish dir contents: {os.listdir('stockfish')}")
    
    common_paths = [
        "stockfish/stockfish-windows-x86-64-avx2.exe",
        "stockfish.exe",
        "stockfish/stockfish",
        "stockfish/stockfish-ubuntu-x86-64-avx2",
        "C:/Program Files/Stockfish/stockfish.exe",
        Path.home() / "Downloads" / "stockfish_15_win_x64_avx2" / "stockfish-windows-x86-64-avx2.exe",
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
    ]
    
    for path in common_paths:
        path_obj = Path(path)
        print(f"  Checking: {path} ... ", end="")
        if path_obj.exists() and path_obj.is_file():
            print(f"✓ FOUND")
            return str(path)
        print("✗ not found")
    
    print("=" * 60)
    return None

stockfish_path = find_stockfish()
if not stockfish_path:
    print("Error: Stockfish not found!")
    print("Looking in these locations:")
    print("  - stockfish/stockfish")
    print("  - stockfish/stockfish-ubuntu-x86-64-avx2")
    print("  - /usr/games/stockfish")
    raise FileNotFoundError("Stockfish executable not found. Please check build.sh succeeded.")

game = ChessGame(stockfish_path)

@app.route('/')
def index():
    # Load game state from session if it exists
    if 'game_state' in session:
        game.set_state(session['game_state'])
    return render_template('chess.html', version=__version__)

@app.route('/version')
def version():
    return jsonify({'version': __version__})

@app.route('/game_state')
def game_state():
    # Load game state from session
    if 'game_state' in session:
        game.set_state(session['game_state'])
    
    return jsonify({
        'board': game.get_board_svg(),
        'history': game.move_history,
        'turn': 'White' if game.board.turn else 'Black',
        'status': game.get_game_status(),
        'game_over': game.board.is_game_over()
    })

@app.route('/board')
def get_board():
    # Load game state from session
    if 'game_state' in session:
        game.set_state(session['game_state'])
    
    selected = request.args.get('selected', None)
    legal = request.args.get('legal', None)
    legal_moves = legal.split(',') if legal else None
    return game.get_board_svg(selected, legal_moves)

@app.route('/move', methods=['POST'])
def move():
    # Load game state from session
    if 'game_state' in session:
        game.set_state(session['game_state'])
    
    data = request.json
    result = game.make_move(data['move'])
    
    # Save game state to session
    session['game_state'] = game.get_state()
    
    return jsonify({
        **result,
        'board': game.get_board_svg(),
        'status': game.get_game_status(),
        'history': game.move_history,
        'turn': 'White' if game.board.turn else 'Black',
        'game_over': game.board.is_game_over()
    })

@app.route('/legal_moves', methods=['POST'])
def legal_moves():
    # Load game state from session
    if 'game_state' in session:
        game.set_state(session['game_state'])
    
    data = request.json
    moves = game.get_legal_moves(data['square'])
    board_svg = game.get_board_svg(data['square'], moves)
    return jsonify({'moves': moves, 'board': board_svg})

@app.route('/best_move', methods=['GET'])
def best_move():
    try:
        # Load game state from session
        if 'game_state' in session:
            game.set_state(session['game_state'])
        
        # Get time_limit from query parameter, default to 60 seconds
        time_limit = float(request.args.get('time_limit', 60.0))
        
        print(f"Best move analysis requested: time_limit={time_limit}s")
        best_moves = game.get_best_move(time_limit)
        
        if best_moves:
            print(f"Best move found: {best_moves[0] if best_moves else 'none'}")
            return jsonify({
                'success': True,
                'moves': best_moves
            })
        return jsonify({'success': False, 'error': 'Game is over'})
    except Exception as e:
        print(f"Best move analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/reset', methods=['POST'])
def reset():
    game.reset()
    # Clear session
    session.pop('game_state', None)
    # Save new empty game state
    session['game_state'] = game.get_state()
    
    return jsonify({
        'success': True,
        'board': game.get_board_svg(),
        'history': [],
        'turn': 'White'
    })

@app.route('/undo', methods=['POST'])
def undo():
    # Load game state from session
    if 'game_state' in session:
        game.set_state(session['game_state'])
    
    result = game.undo_move()
    if result['success']:
        # Save updated state
        session['game_state'] = game.get_state()
        
        return jsonify({
            'success': True,
            'board': game.get_board_svg(),
            'history': game.move_history,
            'turn': 'White' if game.board.turn else 'Black',
            'status': game.get_game_status(),
            'game_over': game.board.is_game_over()
        })
    return jsonify(result)

@app.route('/computer_move', methods=['POST'])
def computer_move():
    try:
        # Load game state from session
        if 'game_state' in session:
            game.set_state(session['game_state'])
        
        data = request.json
        difficulty = data.get('difficulty', 'normal') if data else 'normal'
        
        print(f"Computer move requested: difficulty={difficulty}")
        move = game.get_computer_move(difficulty)
        
        if move:
            san = game.board.san(move)
            game.board.push(move)
            game.move_history.append(san)
            
            # Save updated state
            session['game_state'] = game.get_state()
            
            print(f"Computer played: {san}")
            return jsonify({
                'success': True,
                'move': san,
                'board': game.get_board_svg(),
                'status': game.get_game_status(),
                'history': game.move_history,
                'turn': 'White' if game.board.turn else 'Black',
                'game_over': game.board.is_game_over()
            })
        return jsonify({'success': False, 'error': 'Game is over'})
    except Exception as e:
        print(f"Computer move error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("Starting Chess Game...")
    print(f"Stockfish loaded: {stockfish_path}")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print("Opening browser...")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=5000)
