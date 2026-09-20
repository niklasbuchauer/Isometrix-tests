import sys
import pygame
from pytmx.util_pygame import load_pygame

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1100, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Isometric Tilemap Test")
clock = pygame.time.Clock()

# Load the Tiled map
tmx_data = load_pygame("test_map.tmx")

def draw_isometric_map(surface, tmx_data):
    """Render isometric tiles in correct depth order."""
    # Loop through each layer defined in Tiled
    for layer in tmx_data.visible_layers:
        # Check if the layer contains tile graphics
        if hasattr(layer, "data"):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    # Translate grid (x, y) coordinates into isometric screen space
                    screen_x = (x - y) * (tmx_data.tilewidth // 2) + (SCREEN_WIDTH // 2)
                    screen_y = (x + y) * (tmx_data.tileheight // 2) + 100
                    
                    # Draw the tile
                    surface.blit(tile, (screen_x, screen_y))

# Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))  # Dark gray background
    
    # Draw map
    draw_isometric_map(screen, tmx_data)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
