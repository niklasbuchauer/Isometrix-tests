import os
import sys
import pygame
from pytmx.util_pygame import load_pygame

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Isometric Player - Idle & Direction Fix")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "test_map.tmx")

try:
    tmx_data = load_pygame(MAP_PATH)
except Exception as e:
    print(f"Fehler beim Laden der Map: {e}")
    sys.exit()


class Player:
    def __init__(self, start_x, start_y, use_hair=True):
        self.grid_x = float(start_x)
        self.grid_y = float(start_y)
        self.speed = 0.05

        self.frame_width = 32
        self.frame_height = 32

        sheet_path = os.path.join(
            BASE_DIR, "Chibi-character-template_skin0_by_AxulArt.png"
        )

        self.row_offset = 0 if use_hair else 4
        self.direction = 0

        self.idle_anims, self.walk_anims = self.load_all_animations(sheet_path)

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 120
        self.is_moving = False

    def load_all_animations(self, sheet_path):
        if not os.path.exists(sheet_path):
            print(f"Datei nicht gefunden: {sheet_path}")
            sys.exit()

        sheet = pygame.image.load(sheet_path).convert_alpha()
        idle_anims = {}
        walk_anims = {}

        for dir_index in range(4):
            actual_row = self.row_offset + dir_index
            dir_walk_frames = []

            # 1. Lade die Geh-Animation (Spalten 3 bis 8)
            for col in range(3, 9):
                frame = self.get_scaled_frame(sheet, col, actual_row)
                dir_walk_frames.append(frame)

            # 2. Idle-Sprite: Verwende den 5. Sprite im Sheet (Spalte 5, d.h. Index 4)
            standing_frame = self.get_scaled_frame(sheet, 4, actual_row)
            dir_idle_frames = [standing_frame]

            idle_anims[dir_index] = dir_idle_frames
            walk_anims[dir_index] = dir_walk_frames

        return idle_anims, walk_anims

    def get_scaled_frame(self, sheet, col, row):
        rect = pygame.Rect(
            col * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height,
        )
        sub_surface = sheet.subsurface(rect)
        return pygame.transform.scale(
            sub_surface,
            (int(self.frame_width * 1.5), int(self.frame_height * 1.5)),
        )

    def update(self, dt, is_moving, direction):
        if direction is not None:
            self.direction = direction

        if is_moving != self.is_moving:
            self.current_frame = 0

        self.is_moving = is_moving

        anim_set = self.walk_anims if self.is_moving else self.idle_anims
        frames = anim_set.get(self.direction, [])

        if not frames:
            return

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(frames)

    def draw(self, surface, screen_x, screen_y, tile_width):
        anim_set = self.walk_anims if self.is_moving else self.idle_anims
        frames = anim_set.get(self.direction, [])

        if not frames:
            return

        current_image = frames[self.current_frame % len(frames)]

        feet_x = screen_x + (tile_width // 2) - (current_image.get_width() // 2)
        feet_y = screen_y - current_image.get_height() + 16

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


player = Player(start_x=5, start_y=5, use_hair=True)

running = True
while running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moving = False
    new_dir = None

    # Tasten- und Richtungs-Mapping:
    # 0 = Runter (Sünchen)
    # 1 = Rechts (D) - Tauscht mit A für korrekte Ausrichtung
    # 2 = Links (A)
    # 3 = Hoch (Norden)
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player.grid_x += player.speed
        player.grid_y += player.speed
        moving = True
        new_dir = 0
    elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.grid_x -= player.speed
        player.grid_y += player.speed
        moving = True
        new_dir = 2  # Nutzt jetzt Zeile 2 für Links
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.grid_x += player.speed
        player.grid_y -= player.speed
        moving = True
        new_dir = 1  # Nutzt jetzt Zeile 1 für Rechts
    elif keys[pygame.K_w] or keys[pygame.K_UP]:
        player.grid_x -= player.speed
        player.grid_y -= player.speed
        moving = True
        new_dir = 3

    player.update(dt, is_moving=moving, direction=new_dir)

    screen.fill((30, 30, 30))

    draw_isometric_map(screen, tmx_data)

    player_screen_x, player_screen_y = grid_to_isometric(
        player.grid_x, player.grid_y, tmx_data.tilewidth, tmx_data.tileheight
    )
    player.draw(screen, player_screen_x, player_screen_y, tmx_data.tilewidth)

    pygame.display.flip()

pygame.quit()
sys.exit()