import chess
import chess.engine
import chess.svg
import sys
from pathlib import Path
import webbrowser
import tempfile

class ChessAnalyzer:
    def __init__(self, stockfish_path=None):
        if stockfish_path is None:
            stockfish_path = self.find_stockfish()
        
        if stockfish_path is None:
            raise FileNotFoundError(
                "Stockfish not found. Please download it from https://stockfishchess.org/download/ "
                "and provide the path to the executable."
            )
        
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        print(f"Stockfish engine loaded: {stockfish_path}")
    
    def find_stockfish(self):
        common_paths = [
            "stockfish.exe",
            "stockfish_15_win_x64_avx2/stockfish-windows-x86-64-avx2.exe",
            "C:/Program Files/Stockfish/stockfish.exe",
            Path.home() / "Downloads" / "stockfish_15_win_x64_avx2" / "stockfish-windows-x86-64-avx2.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return str(path)
        return None
    
    def display_board_visual(self, board):
        svg_board = chess.svg.board(board, size=400)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Chess Position</title>
                <style>
                    body {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background-color: #312e2b;
                        font-family: Arial, sans-serif;
                    }}
                    .container {{
                        text-align: center;
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                    }}
                    .fen {{
                        margin-top: 15px;
                        color: #666;
                        font-size: 12px;
                        word-break: break-all;
                        max-width: 400px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    {svg_board}
                    <div class="fen">FEN: {board.fen()}</div>
                </div>
            </body>
            </html>
            """
            f.write(html_content)
            temp_path = f.name
        
        webbrowser.open('file://' + temp_path)
        print(f"Board opened in browser: {temp_path}")
    
    def analyze_position(self, fen_or_moves, depth=20, num_lines=3):
        board = chess.Board()
        
        if " " in fen_or_moves and ("/" in fen_or_moves or fen_or_moves.startswith("rnbqkbnr")):
            board.set_fen(fen_or_moves)
        else:
            moves = fen_or_moves.split()
            for move_str in moves:
                try:
                    move = board.parse_san(move_str)
                    board.push(move)
                except:
                    try:
                        move = chess.Move.from_uci(move_str)
                        board.push(move)
                    except:
                        print(f"Invalid move: {move_str}")
                        return
        
        print("\n" + "="*60)
        print("Position:")
        print(board)
        print(f"\nFEN: {board.fen()}")
        print("="*60)
        
        self.display_board_visual(board)
        
        if board.is_game_over():
            print("\nGame Over!")
            if board.is_checkmate():
                print("Checkmate!")
            elif board.is_stalemate():
                print("Stalemate!")
            elif board.is_insufficient_material():
                print("Insufficient material!")
            return
        
        print(f"\nAnalyzing (depth {depth}, top {num_lines} moves)...\n")
        
        info = self.engine.analyse(board, chess.engine.Limit(depth=depth), multipv=num_lines)
        
        for i, line_info in enumerate(info, 1):
            score = line_info["score"].relative
            pv = line_info["pv"]
            
            if score.is_mate():
                eval_str = f"Mate in {score.mate()}"
            else:
                cp = score.score() / 100
                eval_str = f"{cp:+.2f}"
            
            moves_str = " ".join([board.san(move) for move in pv[:5]])
            if len(pv) > 5:
                moves_str += " ..."
            
            print(f"{i}. {eval_str:>8}  {moves_str}")
    
    def close(self):
        self.engine.quit()

def main():
    print("Chess Position Analyzer with Stockfish")
    print("=" * 60)
    
    stockfish_path = None
    if len(sys.argv) > 1:
        stockfish_path = sys.argv[1]
    
    try:
        analyzer = ChessAnalyzer(stockfish_path)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nUsage: python chess_analyzer.py [path_to_stockfish.exe]")
        return
    
    print("\nEnter positions as:")
    print("  - FEN notation: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    print("  - Move sequence: e4 e5 Nf3 Nc6")
    print("  - Type 'quit' to exit\n")
    
    try:
        while True:
            position = input("\nEnter position (or 'quit'): ").strip()
            
            if position.lower() in ['quit', 'exit', 'q']:
                break
            
            if not position:
                continue
            
            analyzer.analyze_position(position)
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
