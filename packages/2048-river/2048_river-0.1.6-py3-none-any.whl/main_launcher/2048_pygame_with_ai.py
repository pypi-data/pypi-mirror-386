import pygame, sys, random, math, time

# ---------- Config ----------
SIZE = 4
TILE_SIZE = 100
MARGIN = 10
WIDTH = SIZE * TILE_SIZE + (SIZE + 1) * MARGIN
HEIGHT = WIDTH + 80
FPS = 60

# AI config
AI_ENABLED = True          
AI_DEPTH = 3               
AI_TIME_LIMIT = 0.12       

# ---------- Utilities ----------
def empty_positions(board):
    return [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]

def spawn_tile(board):
    empties = empty_positions(board)
    if not empties:
        return
    r,c = random.choice(empties)
    board[r][c] = 4 if random.random() < 0.1 else 2 

# ---------- Game logic ----------
def new_board():
    b = [[0]*SIZE for _ in range(SIZE)]
    spawn_tile(b); spawn_tile(b)
    return b

def compress(row):
    """Move non-zeroes left, keeping order."""
    new = [v for v in row if v != 0]
    new += [0] * (SIZE - len(new))
    return new

def merge(row):
    """Merge step assumes row is already compressed."""
    score_gain = 0
    for i in range(SIZE-1):
        if row[i] != 0 and row[i] == row[i+1]:
            row[i] *= 2
            score_gain += row[i]
            row[i+1] = 0
    return row, score_gain

def move_left(board):
    moved = False; score = 0
    new = []
    for r in range(SIZE):
        comp = compress(board[r])
        merged, s = merge(comp)
        comp2 = compress(merged)
        new.append(comp2)
        if comp2 != board[r]:
            moved = True
        score += s
    return new, moved, score

def rotate_board(board):
    """Rotate clockwise"""
    return [list(reversed(col)) for col in zip(*board)]

def move(board, dir):
    b = [row[:] for row in board]  
    moved = False; score = 0
    if dir == 'left':
        b, moved, score = move_left(b)
    elif dir == 'right':
        b = [list(reversed(r)) for r in b]
        b, moved, score = move_left(b)
        b = [list(reversed(r)) for r in b]
    elif dir == 'up':
        b = rotate_board(rotate_board(rotate_board(b)))
        b, moved, score = move_left(b)
        b = rotate_board(b)
    elif dir == 'down':
        b = rotate_board(b)
        b, moved, score = move_left(b)
        b = rotate_board(rotate_board(rotate_board(b)))
    return b, moved, score

    

def any_moves(board):
    if empty_positions(board): return True
    for r in range(SIZE):
        for c in range(SIZE-1):
            if board[r][c] == board[r][c+1]:
                return True
    for c in range(SIZE):
        for r in range(SIZE-1):
            if board[r][c] == board[r+1][c]:
                return True
    return False

# ---------- Heuristic for AI ----------
def heuristic(board):
    """
    Weighted sum of:
    - Empty tiles (higher is better)
    - Monotonicity (favor rows/cols with monotone gradients)
    - Smoothness (penalize adjacent differences)
    - Max tile (bonus)
    """
    empties = len(empty_positions(board))
    max_tile = max(max(row) for row in board)

    # Smoothness: sum of absolute differences between neighbors (lower better)
    smooth = 0
    for r in range(SIZE):
        for c in range(SIZE):
            v = board[r][c]
            if v==0: continue
            for (dr,dc) in [(1,0),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] != 0:
                    smooth += abs(v - board[nr][nc])

    # Monotonicity: prefer rows/cols that are monotone (left->right or right->left)
    mono = 0
    for r in range(SIZE):
        row = board[r]
        inc = sum(row[i] <= row[i+1] for i in range(SIZE-1))
        dec = sum(row[i] >= row[i+1] for i in range(SIZE-1))
        mono += max(inc, dec)
    for c in range(SIZE):
        col = [board[r][c] for r in range(SIZE)]
        inc = sum(col[i] <= col[i+1] for i in range(SIZE-1))
        dec = sum(col[i] >= col[i+1] for i in range(SIZE-1))
        mono += max(inc, dec)

    # Combine heuristics with weights
    return 1000 * empties + 1.0 * mono - 0.1 * smooth + 1.5 * math.log(max_tile + 1)

# ---------- Expectimax AI ----------
DIRECTIONS = ['up','down','left','right']

def get_children_moves(board):
    moves = []
    for d in DIRECTIONS:
        nb, moved, _ = move(board, d)
        if moved:
            moves.append((d, nb))
    return moves

def expectimax(board, depth, start_time=None, time_limit=None):
    """
    Returns (best_score_estimate, best_move)
    Root is a max node (player). Chance nodes are tile spawn (2 or 4).
    Time-limited; returns heuristic if depth==0 or terminal or time exceeded.
    """
    def max_node(b, depth):
        if time_limit and time.time() - start_time > time_limit:
            return heuristic(b)
        children = get_children_moves(b)
        if depth == 0 or not children:
            return heuristic(b)
        best = -float('inf')
        for _, nb in children:
            val = chance_node(nb, depth-1)
            if val > best: best = val
        return best

    def chance_node(b, depth):
        # find empty positions and average over possible spawns (2 with 0.9, 4 with 0.1)
        empt = empty_positions(b)
        if depth == 0 or not empt:
            return heuristic(b)
        total = 0.0
        # To save time, sample if many empties
        positions = empt
        for (r,c) in positions:
            for tile_val, prob in [(2,0.9),(4,0.1)]:
                b2 = [row[:] for row in b]
                b2[r][c] = tile_val
                val = max_node(b2, depth-1)
                total += prob * val
        return total / len(positions)

    start_time = time.time()
    # root: compute best move among possible moves
    best_move = None
    best_score = -float('inf')
    for d in DIRECTIONS:
        nb, moved, _ = move(board, d)
        if not moved: continue
        val = chance_node(nb, depth-1)
        if val > best_score:
            best_score = val
            best_move = d
        # time cutoff
        if AI_TIME_LIMIT and time.time() - start_time > AI_TIME_LIMIT:
            break
    return best_move, best_score


# ----- Pygame Setup -----
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 24)
big_font = pygame.font.SysFont('Arial', 32, bold=True)

COLORS = {
    0: (205,193,180),
    2: (238,228,218),
    4: (237,224,200),
    8: (242,177,121),
    16: (245,149,99),
    32: (246,124,95),
    64: (246,94,59),
    128: (237,207,114),
    256: (237,204,97),
    512: (237,200,80),
    1024: (237,197,63),
    2048: (237,194,46),
}

# ----- Empty Board -----
def draw_board(board, suggested_move=None):
    screen.fill((187,173,160))
    for r in range(SIZE):
        for c in range(SIZE):
            val = board[r][c]
            rect = pygame.Rect(
                MARGIN + c*(TILE_SIZE+MARGIN),
                MARGIN + r*(TILE_SIZE+MARGIN),
                TILE_SIZE, TILE_SIZE
            )
            color = COLORS.get(val, (60,58,50))
            pygame.draw.rect(screen, color, rect, border_radius=8)
            if val != 0:
                txt = big_font.render(str(val), True, (0,0,0) if val <= 4 else (255,255,255))
                txt_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, txt_rect)

    if suggested_move:
        arrow = {
            'left': "<",
            'right': ">",
            'up': "^",
            'down': "v"
        }[suggested_move]
        sug_txt = font.render(f"Suggestion: {suggested_move.upper()} {arrow}", True, (10,10,10))
        screen.blit(sug_txt, (MARGIN, HEIGHT - 70))
    else:
        screen.blit(font.render("Suggestion: (calculating/off)", True, (10,10,10)), (MARGIN, HEIGHT - 70))

def board_to_string(board):
    return "\n".join(" ".join(f"{v:4}" for v in row) for row in board)

# ----- Main Loop -----
def main():
    board = new_board()
    score = 0
    suggestion_time = 0

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                dir = None
                if key in (pygame.K_LEFT, pygame.K_a): dir = 'left'
                if key in (pygame.K_RIGHT, pygame.K_d): dir = 'right'
                if key in (pygame.K_UP, pygame.K_w): dir = 'up'
                if key in (pygame.K_DOWN, pygame.K_s): dir = 'down'
                if key == pygame.K_SPACE:
                    # toggle AI
                    global AI_ENABLED
                    AI_ENABLED = not AI_ENABLED
                    suggested_move = None
                if dir:
                    nb, moved, gained = move(board, dir)
                    if moved:
                        board = nb
                        spawn_tile(board)
                        score += gained

        if AI_ENABLED:
            # re-calc suggestion each loop but time-limited; avoid expensive compute every frame
            if time.time() - suggestion_time > 0.4 or suggested_move is None:
                start = time.time()
                suggested_move, _ = expectimax(board, AI_DEPTH, start_time=start, time_limit=AI_TIME_LIMIT)
                suggestion_time = time.time()

        draw_board(board, suggested_move if AI_ENABLED else None)
        screen.blit(font.render(f"Score: {score}", True, (0,0,0)), (WIDTH - 220, HEIGHT - 70))
        screen.blit(font.render("Space: toggle AI | Arrow keys: move", True, (0,0,0)), (MARGIN, HEIGHT - 40))
        pygame.display.flip()

        if not any_moves(board):
            print("Game over")
            print(board_to_string(board))
            time.sleep(1)
            board = new_board()
            score = 0
            suggested_move = None

if __name__ == '__main__':
    main()
