import pygame
import sys, os

# --- Initialization ---
pygame.init()
pygame.font.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)
LIGHT_GRAY = (200, 200, 200)

# Fonts
TITLE_FONT = pygame.font.SysFont('Arial', 40)
ITEM_FONT = pygame.font.SysFont('Arial', 20)
MESSAGE_FONT = pygame.font.SysFont('Arial', 25)
TIMER_FONT = pygame.font.SysFont('Arial', 30)
HARD_TIME_LIMIT = 60  
IMAGES = {}
ITEMS = ["Farmer", "Fox", "Chicken", "Grain"]

BASE_DIR = os.path.dirname(__file__)

def load_image(file_name, scale=None):
    """Loads an image, converts alpha, and optionally scales it."""
    try:
        image = pygame.image.load(os.path.join(BASE_DIR, file_name))
        # image = pygame.image.load(file_name)
    except pygame.error as e:
        print(f"Cannot load image: {file_name}")
        raise SystemExit(e)
    
    image = image.convert_alpha() 
    
    if scale:
        image = pygame.transform.scale(image, scale)
    return image

# --- Game Positions ---
BOAT_POS_LEFT = (280, 450)
BOAT_POS_RIGHT = (380, 450)
BOAT_SLOTS = [(15, -60), (75, -60)] 
BANK_SLOTS_LEFT = [
    (20, 450), (90, 450), (160, 450), (230, 450)
]
BANK_SLOTS_RIGHT = [
    (540, 450), (610, 450), (680, 450), (750, 450)
]

# --- Game State Variables ---
game_state = "menu"
level = None
start_ticks = 0
time_left = HARD_TIME_LIMIT
hint_message = ""
hint_timer = 0
item_rects = {} 
boat_rect = None
menu_buttons = {}
game_buttons = {}

def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)
    return text_rect

def reset_game():
    global locations, on_boat, boat_location, game_state, start_ticks, time_left, hint_message
    locations = {"Farmer": "left", "Fox": "left", "Chicken": "left", "Grain": "left"}
    on_boat = []
    boat_location = "left"
    game_state = "playing"
    hint_message = ""
    start_ticks = pygame.time.get_ticks()
    time_left = HARD_TIME_LIMIT

def check_for_danger(items_list):
    """Checks if a given list of items contains a losing combination."""
    
    if "Farmer" in items_list:
        return None
        
    if "Fox" in items_list and "Chicken" in items_list:
        return "The Fox will eat the Chicken!"
    if "Chicken" in items_list and "Grain" in items_list:
        return "The Chicken will eat the Grain!"
    return None

def check_lose_condition():
    """Checks if the current game state is a losing one."""
    global game_state, hint_message
    
    farmer_loc = locations["Farmer"]
    if farmer_loc == "boat":
        farmer_loc = boat_location

    if farmer_loc != "left": 
        items_left = [item for item, loc in locations.items() if loc == "left"]
        danger = check_for_danger(items_left)
        if danger:
            hint_message = danger
            game_state = "lose"
            return True
            
    if farmer_loc != "right":
        items_right = [item for item, loc in locations.items() if loc == "right"]
        danger = check_for_danger(items_right)
        if danger:
            hint_message = danger
            game_state = "lose"
            return True
    
    return False

def check_win_condition():
    global game_state
    if all(loc == "right" for loc in locations.values()):
        game_state = "win"
        return True
    return False

def move_item(item_name):
    global hint_message, hint_timer
    current_loc = locations[item_name]
    
    if current_loc == "boat":
        locations[item_name] = boat_location
        on_boat.remove(item_name)
        
        if item_name == "Farmer" and level == "easy":
            items_on_this_bank = [item for item, loc in locations.items() if loc == boat_location]
            danger_msg = check_for_danger(items_on_this_bank)
            if danger_msg:
                hint_message = f"Wait! {danger_msg}"
                hint_timer = FPS * 3
                locations["Farmer"] = "boat"
                on_boat.append("Farmer")
                return
                
    elif current_loc == boat_location:
        if item_name == "Farmer":
            if "Farmer" not in on_boat:
                locations[item_name] = "boat"
                on_boat.append(item_name)
        elif "Farmer" in on_boat:
            if len(on_boat) < 2:
                locations[item_name] = "boat"
                on_boat.append(item_name)
            else:
                hint_message = "The boat can only hold two items!"
                hint_timer = FPS * 2
        else:
            hint_message = "The Farmer must be on the boat to move items!"
            hint_timer = FPS * 2
            
    if level != "easy":
        if check_lose_condition():
            return
    check_win_condition()

def cross_river():
    global boat_location, hint_message, hint_timer
    
    if "Farmer" not in on_boat:
        hint_message = "The Farmer must be on the boat to cross!"
        hint_timer = FPS * 2
        return

    if level == "easy":
        items_left_behind = [item for item, loc in locations.items() 
                             if loc == boat_location and item not in on_boat]
        danger_msg = check_for_danger(items_left_behind)
        if danger_msg:
            hint_message = f"Wait! If you leave, {danger_msg}"
            hint_timer = FPS * 3
            return
            
    boat_location = "right" if boat_location == "left" else "left"
    
    if level != "easy":
        check_lose_condition()



def draw_menu(screen):
    global menu_buttons
    screen.blit(IMAGES["Background"], (0, 0))

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(100) 
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title_text = "River Crossing Puzzle"
    shadow_offset = 3
    draw_text(title_text, TITLE_FONT, (60, 60, 60), screen, SCREEN_WIDTH // 2 + shadow_offset, 50 + shadow_offset, center=True)
    draw_text(title_text, TITLE_FONT, (255, 223, 0), screen, SCREEN_WIDTH // 2, 50, center=True)

    rules_box = pygame.Rect(100, 90, SCREEN_WIDTH - 200, 250)
    pygame.draw.rect(screen, (255, 255, 255), rules_box, border_radius=20)
    pygame.draw.rect(screen, (0, 0, 0), rules_box, 3, border_radius=20)

    draw_text("How to Play:", MESSAGE_FONT, BLACK, screen, SCREEN_WIDTH // 2, 130, center=True)

    rules_font = ITEM_FONT
    draw_text("Help the Farmer get everyone safely across the river!", rules_font, BLACK, screen, SCREEN_WIDTH // 2, 165, center=True)
    draw_text("1. Click an item to move it on or off the boat.", rules_font, BLACK, screen, 150, 195)
    draw_text("2. The Farmer must be on the boat to cross.", rules_font, BLACK, screen, 150, 220)
    draw_text("3. The boat only fits the Farmer and one other item.", rules_font, BLACK, screen, 150, 245)

    warn_box = pygame.Rect(150, 280, SCREEN_WIDTH - 290, 100)
    pygame.draw.rect(screen, (255, 235, 235), warn_box, border_radius=15)
    pygame.draw.rect(screen, RED, warn_box, 3, border_radius=15)

    draw_text("Watch out!", MESSAGE_FONT, RED, screen, SCREEN_WIDTH // 2, 305, center=True)
    draw_text("Don't leave the Fox and Chicken alone!", rules_font, RED, screen, SCREEN_WIDTH // 2, 330, center=True)
    draw_text("Don't leave the Chicken and Grain alone!", rules_font, RED, screen, SCREEN_WIDTH // 2, 350, center=True)

    # --- Difficulty Selection ---
    draw_text("Select Difficulty", MESSAGE_FONT, (255, 223, 0), screen, SCREEN_WIDTH // 2, 430, center=True)

    def draw_gradient_button(rect, color1, color2, text, text_color):
        gradient = pygame.Surface((rect.width, rect.height))
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(gradient, (r, g, b), (0, y), (rect.width, y))
        gradient = gradient.convert()
        gradient.set_alpha(230) 
        screen.blit(gradient, rect)
        draw_text(text, MESSAGE_FONT, text_color, screen, rect.centerx, rect.centery, center=True)
    
    btn_width = 220
    btn_height = 60
    btn_y = 470
    spacing = 40

    total_width = 3 * btn_width + 2 * spacing
    start_x = (SCREEN_WIDTH - total_width) // 2

    btn_easy = pygame.Rect(start_x, btn_y, btn_width, btn_height)
    btn_medium = pygame.Rect(start_x + btn_width + spacing, btn_y, btn_width, btn_height)
    btn_hard = pygame.Rect(start_x + 2 * (btn_width + spacing), btn_y, btn_width, btn_height)

    draw_gradient_button(btn_easy, (120, 255, 120), (40, 180, 40), "Easy", WHITE)
    draw_gradient_button(btn_medium, (100, 160, 255), (40, 80, 180), "Medium", WHITE)
    draw_gradient_button(btn_hard, (255, 100, 100), (180, 0, 0), "Hard", WHITE)

    menu_buttons = {"easy": btn_easy, "medium": btn_medium, "hard": btn_hard}



# def draw_menu(screen):
#     global menu_buttons
#     screen.blit(IMAGES["Background"], (0, 0))
    
#     draw_text("River Crossing Puzzle", TITLE_FONT, BLACK, screen, SCREEN_WIDTH // 2, 50, center=True)
    
#     draw_text("How to Play:", MESSAGE_FONT, BLACK, screen, SCREEN_WIDTH // 2, 120, center=True)
    
#     rules_font = ITEM_FONT
#     draw_text("Help the Farmer get everyone safely across the river!", rules_font, BLACK, screen, SCREEN_WIDTH // 2, 160, center=True)
    
#     draw_text("1. Click an item to move it on or off the boat.", rules_font, BLACK, screen, 150, 190)
#     draw_text("2. The Farmer must be on the boat to cross.", rules_font, BLACK, screen, 150, 215)
#     draw_text("3. The boat only fits the Farmer and one other item.", rules_font, BLACK, screen, 150, 240)

#     draw_text("Watch out!", rules_font, RED, screen, SCREEN_WIDTH // 2, 280, center=True)
#     draw_text("Don't leave the Fox and Chicken alone!", rules_font, RED, screen, SCREEN_WIDTH // 2, 305, center=True)
#     draw_text("Don't leave the Chicken and Grain alone!", rules_font, RED, screen, SCREEN_WIDTH // 2, 330, center=True)

#     draw_text("Select Difficulty:", MESSAGE_FONT, BLACK, screen, SCREEN_WIDTH // 2, 400, center=True)
    
#     btn_easy = pygame.Rect(250, 440, 300, 50) 
#     pygame.draw.rect(screen, GREEN, btn_easy)
#     draw_text("Easy (With Warnings)", MESSAGE_FONT, BLACK, screen, btn_easy.centerx, btn_easy.centery, center=True)
    
#     btn_medium = pygame.Rect(250, 500, 300, 50) 
#     pygame.draw.rect(screen, BLUE, btn_medium)
#     draw_text("Medium (Classic)", MESSAGE_FONT, WHITE, screen, btn_medium.centerx, btn_medium.centery, center=True)
    
#     btn_hard = pygame.Rect(250, 560, 300, 50) 
#     pygame.draw.rect(screen, RED, btn_hard)
#     draw_text("Hard (60s Timer)", MESSAGE_FONT, WHITE, screen, btn_hard.centerx, btn_hard.centery, center=True)
    
#     menu_buttons = {"easy": btn_easy, "medium": btn_medium, "hard": btn_hard}

def draw_game_world(screen):
    global item_rects, boat_rect
    item_rects = {}
    screen.blit(IMAGES["Background"], (0, 0))
    
    boat_pos = BOAT_POS_LEFT if boat_location == "left" else BOAT_POS_RIGHT
    boat_rect = screen.blit(IMAGES["Boat"], boat_pos)
    
    boat_item_idx = 1
    for i, item in enumerate(ITEMS):
        loc = locations[item]
        if loc == "left":
            pos = BANK_SLOTS_LEFT[i]
            item_rects[item] = screen.blit(IMAGES[item], pos)
        elif loc == "right":
            pos = BANK_SLOTS_RIGHT[i]
            item_rects[item] = screen.blit(IMAGES[item], pos)
        elif loc == "boat":
            slot_pos = BOAT_SLOTS[0] if item == "Farmer" else BOAT_SLOTS[boat_item_idx]
            if item != "Farmer":
                boat_item_idx += 1
            pos = (boat_pos[0] + slot_pos[0], boat_pos[1] + slot_pos[1])
            item_rects[item] = screen.blit(IMAGES[item], pos)

def draw_game_ui(screen):
    global game_buttons, hint_message, hint_timer, time_left
    
    btn_reset = pygame.Rect(10, 10, 100, 40)
    pygame.draw.rect(screen, LIGHT_GRAY, btn_reset)
    draw_text("Reset", ITEM_FONT, BLACK, screen, btn_reset.centerx, btn_reset.centery, center=True)
    
    btn_menu = pygame.Rect(120, 10, 100, 40)
    pygame.draw.rect(screen, LIGHT_GRAY, btn_menu)
    draw_text("Menu", ITEM_FONT, BLACK, screen, btn_menu.centerx, btn_menu.centery, center=True)
    
    game_buttons = {"reset": btn_reset, "menu": btn_menu}

    if level == "hard":
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, HARD_TIME_LIMIT - int(elapsed_seconds))
        draw_text(f"Time: {time_left}", TIMER_FONT, RED, screen, SCREEN_WIDTH - 150, 15)
        if time_left == 0:
            global game_state
            game_state = "lose"
            hint_message = "Time's up!"

    if hint_message:
        draw_text(hint_message, MESSAGE_FONT, RED, screen, SCREEN_WIDTH // 2, 50, center=True)
        if hint_timer > 0:
            hint_timer -= 1
        else:
            hint_message = ""
            
def draw_end_screen(screen, message):
    global game_buttons
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    color = GREEN if game_state == "win" else RED
    draw_text(message, TITLE_FONT, color, screen, SCREEN_WIDTH // 2, 250, center=True)
    
    if hint_message and game_state == "lose":
        draw_text(f"({hint_message})", MESSAGE_FONT, WHITE, screen, SCREEN_WIDTH // 2, 300, center=True)
    
    btn_retry = pygame.Rect(290, 350, 220, 50)
    pygame.draw.rect(screen, LIGHT_GRAY, btn_retry)
    draw_text("Play Again", MESSAGE_FONT, BLACK, screen, btn_retry.centerx, btn_retry.centery, center=True)
    
    btn_menu = pygame.Rect(310, 420, 180, 50)
    pygame.draw.rect(screen, LIGHT_GRAY, btn_menu)
    draw_text("Main Menu", MESSAGE_FONT, BLACK, screen, btn_menu.centerx, btn_menu.centery, center=True)
    
    game_buttons = {"retry": btn_retry, "menu": btn_menu}

# --- Main Game Loop ---
def main():
    global game_state, level, hint_message, IMAGES
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("River Crossing Puzzle")
    clock = pygame.time.Clock()
    
    try:
        item_scale = (70, 70)
        IMAGES = {
            "Background": load_image("assets/background.png", (SCREEN_WIDTH, SCREEN_HEIGHT)),
            "Boat": load_image("assets/boat.png", (150, 70)),
            "Farmer": load_image("assets/farmer.png", item_scale),
            "Fox": load_image("assets/fox.png", item_scale),
            "Chicken": load_image("assets/chicken.png", item_scale),
            "Grain": load_image("assets/grain.png", item_scale),
        }
    except SystemExit:
        print("\n--- ERROR ---")
        print("Could not load one or more image files.")
        print("Please make sure the files are in the same directory as the script.")
        pygame.quit()
        sys.exit()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                
                if game_state == "menu":
                    for lvl, rect in menu_buttons.items():
                        if rect.collidepoint(pos):
                            level = lvl
                            reset_game()
                            
                elif game_state == "playing":
                    if game_buttons["reset"].collidepoint(pos):
                        reset_game()
                        break
                    if game_buttons["menu"].collidepoint(pos):
                        game_state = "menu"
                        break
                        
                    clicked_item = None
                    for item, rect in item_rects.items():
                        if rect.collidepoint(pos):
                            clicked_item = item
                            break
                    
                    if clicked_item:
                        move_item(clicked_item)
                    elif boat_rect and boat_rect.collidepoint(pos): 
                        cross_river()
                        
                elif game_state in ("win", "lose"):
                    if game_buttons["retry"].collidepoint(pos):
                        reset_game()
                    if game_buttons["menu"].collidepoint(pos):
                        game_state = "menu"
                        
        screen.fill(BLACK)
        
        if game_state == "menu":
            draw_menu(screen)
        elif game_state == "playing":
            draw_game_world(screen)
            draw_game_ui(screen)
        elif game_state == "win":
            draw_game_world(screen)
            draw_game_ui(screen)
            draw_end_screen(screen, "You Win! Congratulations!")
        elif game_state == "lose":
            draw_game_world(screen)
            draw_game_ui(screen)
            draw_end_screen(screen, "Game Over!")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()