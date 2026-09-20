import os
import sys
import pygame
from pytmx.util_pygame import load_pygame

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Isometric Player - Custom Tile Property Water Collision")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "test_map.tmx")

try:
    tmx_data = load_pygame(MAP_PATH)
except Exception as e:
    print(f"Fehler beim Laden der Map: {e}")
    sys.exit()


def is_wall(grid_x, grid_y, tmx_data):
    """
    Prüft, ob ein Feld blockiert ist.
    Unterstützt sowohl Wände über Layer-Namen als auch Wasser/Kollisionen
    auf DENSELBEN Layer über Tile Custom Properties (z.B. is_water = True).
    """
    map_width = tmx_data.width
    map_height = tmx_data.height

    # 1. Prüfen, ob der Spieler außerhalb der Map-Ränder ist
    if grid_x < 0 or grid_x >= map_width or grid_y < 0 or grid_y >= map_height:
        return True

    tile_x = int(grid_x)
    tile_y = int(grid_y)

    blocked_keywords = ["wall", "wand", "wände"]

    # 2. Prüfen aller sichtbaren Ebenen am Standort des Spielers
    for layer in tmx_data.visible_layers:
        if hasattr(layer, "data"):
            gid = layer.data[tile_y][tile_x]
            if gid != 0:
                layer_name = layer.name.lower().strip()

                # Blockade falls die Ebene selbst eine Wand-Ebene ist
                if any(keyword in layer_name for keyword in blocked_keywords):
                    return True

                # Blockade prüfen über Tile Custom Properties auf DENSELBEN Ebene
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props:
                    if (
                        props.get("is_water") is True
                        or props.get("collidable") is True
                        or props.get("water") is True
                    ):
                        return True

    return False


class Player:
    def __init__(self, start_x, start_y, use_hair=True, scale_factor=1.15):
        self.grid_x = float(start_x)
        self.grid_y = float(start_y)

        self.speed = 0.04
        self.radius = 0.25

        self.frame_width = 32
        self.frame_height = 32
        self.scale_factor = scale_factor

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

            for col in range(3, 9):
                frame = self.get_scaled_frame(sheet, col, actual_row)
                dir_walk_frames.append(frame)

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

        scaled_w = int(self.frame_width * self.scale_factor)
        scaled_h = int(self.frame_height * self.scale_factor)

        return pygame.transform.scale(sub_surface, (scaled_w, scaled_h))

    def move(self, dx, dy, tmx_data):
        new_x = self.grid_x + dx
        if not is_wall(
            new_x + (self.radius if dx > 0 else -self.radius),
            self.grid_y,
            tmx_data,
        ):
            self.grid_x = new_x

        new_y = self.grid_y + dy
        if not is_wall(
            self.grid_x,
            new_y + (self.radius if dy > 0 else -self.radius),
            tmx_data,
        ):
            self.grid_y = new_y

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


def draw_scene_sorted(surface, tmx_data, player):
    # SCHRITT 1: Zeichne alle Boden-Ebenen (Wasser und Boden liegen auf derselben Ebene)
    for layer in tmx_data.visible_layers:
        if hasattr(layer, "data"):
            # Wand-Ebenen überspringen, da diese erst in Schritt 2 kommen
            if any(w in layer.name.lower() for w in ["walls", "wand", "wände"]):
                continue

            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen_x, screen_y = grid_to_isometric(
                        x, y, tmx_data.tilewidth, tmx_data.tileheight
                    )
                    surface.blit(tile, (screen_x, screen_y))

    # SCHRITT 2: Sortiere und zeichne vertikale Objekte (Wände und den Spieler) nach Tiefe
    sortable_objects = []

    for layer in tmx_data.visible_layers:
        if hasattr(layer, "data") and any(
            w in layer.name.lower() for w in ["walls", "wand", "wände"]
        ):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen_x, screen_y = grid_to_isometric(
                        x, y, tmx_data.tilewidth, tmx_data.tileheight
                    )
                    depth = x + y
                    sortable_objects.append(
                        ("tile", depth, tile, screen_x, screen_y)
                    )

    player_screen_x, player_screen_y = grid_to_isometric(
        player.grid_x, player.grid_y, tmx_data.tilewidth, tmx_data.tileheight
    )
    player_depth = player.grid_x + player.grid_y
    sortable_objects.append(
        ("player", player_depth, player, player_screen_x, player_screen_y)
    )

    sortable_objects.sort(key=lambda item: item[1])

    for obj_type, depth, obj, sx, sy in sortable_objects:
        if obj_type == "tile":
            surface.blit(obj, (sx, sy))
        elif obj_type == "player":
            obj.draw(surface, sx, sy, tmx_data.tilewidth)


player = Player(start_x=5, start_y=5, use_hair=True, scale_factor=1.15)

running = True
while running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moving = False
    new_dir = None
    dx, dy = 0, 0

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        dx += player.speed
        dy += player.speed
        moving = True
        new_dir = 0
    elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
        dx -= player.speed
        dy += player.speed
        moving = True
        new_dir = 2
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        dx += player.speed
        dy -= player.speed
        moving = True
        new_dir = 1
    elif keys[pygame.K_w] or keys[pygame.K_UP]:
        dx -= player.speed
        dy -= player.speed
        moving = True
        new_dir = 3

    if moving:
        player.move(dx, dy, tmx_data)

    player.update(dt, is_moving=moving, direction=new_dir)

    screen.fill((30, 30, 30))

    draw_scene_sorted(screen, tmx_data, player)

    pygame.display.flip()

pygame.quit()
sys.exit()