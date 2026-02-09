import chess
import chess.svg

def create_board_html(position):
    board = chess.Board()
    
    if " " in position and ("/" in position or position.startswith("rnbqkbnr")):
        board.set_fen(position)
    else:
        moves = position.split()
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
    
    svg_board = chess.svg.board(board, size=500)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chess Position</title>
    <style>
        body {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        .container {{
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .fen {{
            margin-top: 20px;
            color: #666;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            max-width: 500px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Chess Position</h1>
        {svg_board}
        <div class="fen">FEN: {board.fen()}</div>
    </div>
</body>
</html>"""
    
    with open("chess_board.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Chess board saved to: chess_board.html")
    print(f"Full path: {os.path.abspath('chess_board.html')}")
    print("\nOpen this file in your web browser to see the board!")

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) > 1:
        position = " ".join(sys.argv[1:])
    else:
        print("Enter position (FEN or moves):")
        position = input().strip()
    
    create_board_html(position)
