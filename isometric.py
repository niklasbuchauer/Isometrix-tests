import os
import sys
import pygame
from pytmx.util_pygame import load_pygame

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Isometric Player Animation & Cutoff Fix")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "test_map.tmx")

try:
    tmx_data = load_pygame(MAP_PATH)
except Exception as e:
    print(f"Fehler beim Laden der Map: {e}")
    sys.exit()

class Player:
    def __init__(self, start_x, start_y):
        self.grid_x = float(start_x)
        self.grid_y = float(start_y)
        self.speed = 0.05
        
        # FIX FOR CUTOFF: Frame width changed from 16 to 32
        self.frame_width = 32  
        self.frame_height = 32

        idle_path = os.path.join(BASE_DIR, "16x32 Idle-Sheet.png")
        walk_path = os.path.join(BASE_DIR, "16x32 Walk-Sheet.png")

        self.idle_frames = self.load_sheet(idle_path)
        self.walk_frames = self.load_sheet(walk_path)

        self.current_frames = self.idle_frames
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 120  # Milliseconds per frame
        self.is_moving = False

    def load_sheet(self, sheet_path):
        if not os.path.exists(sheet_path):
            fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (255, 0, 0), (16, 32), 12)
            return [fallback]

        sheet = pygame.image.load(sheet_path).convert_alpha()
        frames = []
        num_frames = sheet.get_width() // self.frame_width

        for i in range(num_frames):
            frame_rect = pygame.Rect(
                i * self.frame_width, 0, self.frame_width, self.frame_height
            )
            frame_surface = sheet.subsurface(frame_rect)

            # Scale 1.5x so it fits isometric tiles nicely
            scaled_surface = pygame.transform.scale(
                frame_surface, (int(self.frame_width * 1.5), int(self.frame_height * 1.5))
            )
            frames.append(scaled_surface)

        return frames

    def update(self, dt, is_moving):
        """Switch between idle/walk animation sheets and animate frames."""
        # Switch sheets when movement state changes
        if is_moving and not self.is_moving:
            self.current_frames = self.walk_frames
            self.current_frame = 0
        elif not is_moving and self.is_moving:
            self.current_frames = self.idle_frames
            self.current_frame = 0

        self.is_moving = is_moving

        # Cycle animation frames continuously while moving
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.current_frames)
        else:
            # Freeze at frame 0 when standing still
            self.current_frame = 0

    def draw(self, surface, screen_x, screen_y, tile_width):
        current_image = self.current_frames[self.current_frame]

        feet_x = screen_x + (tile_width // 2) - (current_image.get_width() // 2)
        feet_y = screen_y - current_image.get_height() + 12

        surface.blit(current_image, (feet_x, feet_y))


def grid_to_isometric(x, y, tile_width, tile_height):
    screen_x = (x - y) * (tile_width // 2) + (SCREEN_WIDTH // 2)
    screen_y = (x + y) * (tile_height // 2) + 100
    return screen_x, screen_y


def draw_isometric_map(surface, tmx_data):
    for layer in tmx_data.visible_layers:
        if hasattr(layer, "data"):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen_x, screen_y = grid_to_isometric(
                        x, y, tmx_data.tilewidth, tmx_data.tileheight
                    )
                    surface.blit(tile, (screen_x, screen_y))


player = Player(start_x=5, start_y=5)

running = True
while running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moving = False

    # Movement controls (straight screen directions)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player.grid_x -= player.speed
        player.grid_y -= player.speed
        moving = True
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player.grid_x += player.speed
        player.grid_y += player.speed
        moving = True
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.grid_x -= player.speed
        player.grid_y += player.speed
        moving = True
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.grid_x += player.speed
        player.grid_y -= player.speed
        moving = True

    # Update animation state with delta time
    player.update(dt, is_moving=moving)

    screen.fill((30, 30, 30))

    draw_isometric_map(screen, tmx_data)

    player_screen_x, player_screen_y = grid_to_isometric(
        player.grid_x, player.grid_y, tmx_data.tilewidth, tmx_data.tileheight
    )
    player.draw(screen, player_screen_x, player_screen_y, tmx_data.tilewidth)

    pygame.display.flip()

pygame.quit()
sys.exit()