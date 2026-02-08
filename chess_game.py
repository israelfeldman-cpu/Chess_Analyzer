import chess
import chess.engine
import chess.svg
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import time

app = Flask(__name__)

class ChessGame:
    def __init__(self, stockfish_path):
        self.board = chess.Board()
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
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
    
    def get_best_move(self):
        if self.board.is_game_over():
            return None
        
        result = self.engine.analyse(self.board, chess.engine.Limit(depth=5, nodes=50000), multipv=1)
        
        best_moves = []
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
        if self.board.is_game_over():
            return None
        
        if difficulty == 'easy':
            result = self.engine.play(self.board, chess.engine.Limit(depth=3, nodes=10000))
        else:
            result = self.engine.play(self.board, chess.engine.Limit(depth=5, nodes=50000))
        
        return result.move
    
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
    
    def close(self):
        self.engine.quit()

def find_stockfish():
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
        if path_obj.exists() and path_obj.is_file():
            return str(path)
    return None

stockfish_path = find_stockfish()
if not stockfish_path:
    print("Error: Stockfish not found!")
    exit(1)

game = ChessGame(stockfish_path)

@app.route('/')
def index():
    return render_template('chess.html')

@app.route('/board')
def get_board():
    selected = request.args.get('selected', None)
    legal = request.args.get('legal', None)
    legal_moves = legal.split(',') if legal else None
    return game.get_board_svg(selected, legal_moves)

@app.route('/move', methods=['POST'])
def move():
    data = request.json
    result = game.make_move(data['move'])
    
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
    data = request.json
    moves = game.get_legal_moves(data['square'])
    board_svg = game.get_board_svg(data['square'], moves)
    return jsonify({'moves': moves, 'board': board_svg})

@app.route('/best_move', methods=['GET'])
def best_move():
    best_moves = game.get_best_move()
    if best_moves:
        return jsonify({
            'success': True,
            'moves': best_moves
        })
    return jsonify({'success': False, 'error': 'Game is over'})

@app.route('/reset', methods=['POST'])
def reset():
    game.reset()
    return jsonify({
        'success': True,
        'board': game.get_board_svg(),
        'history': [],
        'turn': 'White'
    })

@app.route('/undo', methods=['POST'])
def undo():
    result = game.undo_move()
    if result['success']:
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
    data = request.json
    difficulty = data.get('difficulty', 'normal') if data else 'normal'
    
    move = game.get_computer_move(difficulty)
    if move:
        san = game.board.san(move)
        game.board.push(move)
        game.move_history.append(san)
        
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

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("Starting Chess Game...")
    print(f"Stockfish loaded: {stockfish_path}")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    
    if os.environ.get('RENDER'):
        print(f"Running on Render, port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("Opening browser...")
        threading.Thread(target=open_browser, daemon=True).start()
        app.run(debug=False, port=5000)
    
    game.close()
