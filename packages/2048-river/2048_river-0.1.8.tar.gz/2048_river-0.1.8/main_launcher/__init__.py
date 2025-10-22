import pygame
import sys
import subprocess
import os
import math

pygame.init()
pygame.mixer.init() 

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Playtime Arcade Hub")
TITLE_FONT = pygame.font.SysFont(None, 64, bold=True)
SUB_FONT = pygame.font.SysFont(None, 32)
BUTTON_TITLE_FONT = pygame.font.SysFont(None, 36, bold=True)
DESC_FONT = pygame.font.SysFont(None, 24, italic=True)

BASE_DIR = os.path.dirname(__file__)

# Colors 
WHITE = (255, 255, 255)
OFF_WHITE = (240, 240, 240)
DARK_GRAY = (30, 30, 40)
DARK_BLUE= (36, 30, 156)
ACCENT_YELLOW = (235, 216, 52) # Primary Accent
ACCENT_ORANGE = (122, 74, 1) # Game 1 Accent
ACCENT_GREEN = (2, 82, 22) # Game 2 Accent
SHADOW_COLOR = (0, 0, 0, 100) # Semi-transparent black for shadows

try:
    hover_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "assets/audio/btn_hover.wav"))
    click_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "assets/audio/btn-clicking-1.wav"))
    hover_sound.set_volume(0.3)
    click_sound.set_volume(0.5)
except pygame.error:
    print("Warning: Audio files 'assets/audio/hover.wav' or 'click.wav' not found.")
    hover_sound = None
    click_sound = None

try:
    bg_image = pygame.image.load(os.path.join(BASE_DIR, "assets/main_bg.png")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
except pygame.error:
    print("Warning: Background image 'assets/main_bg.png' not found. Using solid color.")
    bg_image = None
    
try:
    img_2048 = pygame.image.load(os.path.join(BASE_DIR, "assets/2048_display.png")).convert_alpha()
    img_cross = pygame.image.load(os.path.join(BASE_DIR, "assets/background.png")).convert_alpha()
    img_2048 = pygame.transform.smoothscale(img_2048, (150, 150))
    img_cross = pygame.transform.smoothscale(img_cross, (150, 150))
except pygame.error:
    print("Warning: Game icons not found. Using placeholder circles.")
    img_2048 = pygame.Surface((150, 150), pygame.SRCALPHA)
    pygame.draw.circle(img_2048, ACCENT_ORANGE, (75, 75), 70)
    pygame.draw.circle(img_2048, WHITE, (75, 75), 30)

    img_cross = pygame.Surface((150, 150), pygame.SRCALPHA)
    pygame.draw.rect(img_cross, (100, 180, 80), (0, 0, 150, 150)) # Grass bg
    pygame.draw.rect(img_cross, (50, 100, 200), (0, 50, 150, 50)) # River
    pygame.draw.circle(img_cross, (255, 0, 0), (30, 25), 10) # Person 1
    pygame.draw.circle(img_cross, (0, 0, 255), (60, 25), 10) # Person 2
    pygame.draw.circle(img_cross, (255, 255, 0), (120, 125), 10) # Person 3


clock = pygame.time.Clock()


def launch_game(file_name):
    """Launch the selected game script."""
    if click_sound:
        click_sound.play()
    script_path = os.path.join(BASE_DIR, file_name)
    subprocess.Popen([sys.executable, script_path])


def create_vignette_surface(width, height, max_alpha=120):
    """Creates a pre-rendered vignette surface. Call this ONCE."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(width):
        for y in range(height):
            dist_sq = (x - width/2)**2 + (y - height/2)**2
            max_dist_sq = (width/2)**2 + (height/2)**2
            
            alpha_factor = (dist_sq / max_dist_sq) ** 0.5
            alpha = int(alpha_factor * max_alpha) 
            
            surface.set_at((x, y), (0, 0, 0, alpha))
    return surface


def draw_button(rect, base_color, hover_color, mouse_pos, clicked, text, image, description):
    """Draws a professional, interactive button with an image, text, and description."""
    hovering = rect.collidepoint(mouse_pos)
    
    is_pushed = clicked and hovering
    
    main_color = base_color if not hovering else hover_color
    title_color = WHITE
    desc_color = OFF_WHITE
    
    # Adjust position for the "pressed" effect
    offset_y = 5 if is_pushed else 0
    
    shadow_depth_base = 8
    shadow_inflate = 0
    
    if hovering and not is_pushed:
        shadow_depth = shadow_depth_base - offset_y + 5 
        shadow_inflate = 10 
    else:
        shadow_depth = shadow_depth_base - offset_y
    
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_depth
    shadow_rect = shadow_rect.inflate(shadow_inflate, shadow_inflate) 
    
    shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, SHADOW_COLOR, shadow_surf.get_rect(), border_radius=25) # More rounded
    screen.blit(shadow_surf, shadow_rect.topleft)

    # 2. Main Body (Layer 2: Middle)
    button_rect = rect.copy()
    button_rect.y += offset_y
    pygame.draw.rect(screen, main_color, button_rect, border_radius=20)
    
    # 3. Inner Border/Highlight (Layer 3: Top)
    pygame.draw.rect(screen, OFF_WHITE, button_rect, width=2, border_radius=20)
    
    # 4. Hover Glow (Dynamic Effect)
    if hovering and not is_pushed:
        time_now = pygame.time.get_ticks() / 1000
        pulse = (math.sin(time_now * 4) + 1) / 2 
        glow_alpha = 60 + (pulse * 30) 
        glow_size = 10 + (pulse * 5)
        
        glow_color = (*hover_color, glow_alpha) 
        
        glow = pygame.Surface((button_rect.width + glow_size, button_rect.height + glow_size), pygame.SRCALPHA)
        # Draw a soft rectangle, not a harsh ellipse
        pygame.draw.rect(glow, glow_color, glow.get_rect(), border_radius=30) 
        
        screen.blit(glow, (button_rect.x - glow_size/2, button_rect.y - glow_size/2), special_flags=pygame.BLEND_RGBA_ADD)

    content_y_offset = button_rect.y 
    
    # Image (Centered)
    img_x = button_rect.centerx - image.get_width() // 2
    img_y = content_y_offset + 25
    screen.blit(image, (img_x, img_y))

    # Game Title (Centered)
    title_text = BUTTON_TITLE_FONT.render(text, True, title_color)
    title_y = img_y + image.get_height() + 15
    screen.blit(title_text, (button_rect.centerx - title_text.get_width() // 2, title_y))

    # Game Description (Centered and wrapped)
    desc_lines = description.split("\n")
    start_y = button_rect.y + button_rect.height - (len(desc_lines) * 26) - 15
    for i, line in enumerate(desc_lines):
        desc_text = DESC_FONT.render(line, True, desc_color)
        screen.blit(desc_text, (button_rect.centerx - desc_text.get_width() // 2, start_y + i * 26))


def draw_title():
    """Animated title with a cleaner, more impactful design."""
    time_now = pygame.time.get_ticks() / 1000
    
    wobble = math.sin(time_now * 1.5) * 3
    
    title_text = "Playtime Arcade!"
    title_surface = TITLE_FONT.render(title_text, True, ACCENT_YELLOW)
    
    # Shadow
    shadow_color = (0, 0, 0)
    title_shadow = TITLE_FONT.render(title_text, True, shadow_color)
    screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 63 + wobble))
    
    # Text
    screen.blit(title_surface, (WIDTH // 2 - title_surface.get_width() // 2, 60 + wobble))

    # Subtitle
    subtitle = SUB_FONT.render("Choose your adventure below", True, DARK_BLUE)
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 135))


def main():
    running = True
    
    is_mouse_down = False 
    
    last_hovered = None # None, '2048', or 'cross'

    vignette_surface = create_vignette_surface(WIDTH, HEIGHT)

    button_width, button_height = 300, 350
    spacing = 40
    total_width = button_width * 2 + spacing
    start_x = (WIDTH - total_width) // 2

    btn_2048 = pygame.Rect(start_x, HEIGHT // 2 - button_height // 2 + 50, button_width, button_height)
    btn_cross = pygame.Rect(start_x + button_width + spacing, HEIGHT // 2 - button_height // 2 + 50, button_width, button_height)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(DARK_GRAY)
            
        screen.blit(vignette_surface, (0, 0)) 
        draw_title()

        current_hovered = None
        if btn_2048.collidepoint(mouse_pos):
            current_hovered = '2048'
        elif btn_cross.collidepoint(mouse_pos):
            current_hovered = 'cross'

        if current_hovered != last_hovered:
            if current_hovered is not None and hover_sound:
                hover_sound.play()
        last_hovered = current_hovered
        
        if current_hovered:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Buttons
        draw_button(
            btn_2048,
            DARK_GRAY, ACCENT_ORANGE, # Base color is dark gray, hover is orange accent
            mouse_pos,
            is_mouse_down,
            "2048 Puzzle",
            img_2048,
            "Merge tiles to reach\n2048! Use arrow keys."
        )

        draw_button(
            btn_cross,
            DARK_GRAY, ACCENT_GREEN, # Base color is dark gray, hover is green accent
            mouse_pos,
            is_mouse_down,
            "River Crossing",
            img_cross,
            "Guide people safely\nacross the river!"
        )

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_mouse_down = True
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_mouse_down = False
                    if last_hovered == '2048':
                        launch_game("2048_pygame_with_ai.py")
                    elif last_hovered == 'cross':
                        launch_game("river_crossing.py")

        pygame.display.flip()
        clock.tick(60)

    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW) 
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()