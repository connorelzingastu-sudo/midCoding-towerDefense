import sys
import pygame

pygame.init()

GRID_COLS = 16
GRID_ROWS = 12
TILE_SIZE = 56
BOARD_WIDTH = GRID_COLS * TILE_SIZE
BOARD_HEIGHT = GRID_ROWS * TILE_SIZE
PANEL_WIDTH = 280
WIDTH = BOARD_WIDTH + PANEL_WIDTH
HEIGHT = BOARD_HEIGHT
FPS = 60

BG_COLOR = (26, 33, 42)
GRID_COLOR = (43, 52, 63)
GRASS_COLOR = (49, 90, 58)
PANEL_BG = (20, 24, 30)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense - Day 1")
clock = pygame.time.Clock()

def draw_grid():
	for row in range(GRID_ROWS):
		for col in range(GRID_COLS):
			x = col * TILE_SIZE
			y = row * TILE_SIZE
			pygame.draw.rect(screen, GRASS_COLOR, (x, y, TILE_SIZE, TILE_SIZE))
			pygame.draw.rect(screen, GRID_COLOR, (x, y, TILE_SIZE, TILE_SIZE), 1)


def draw_panel():
	pygame.draw.rect(screen, PANEL_BG, (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

def main():
	running = True
	while running:
		clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		screen.fill(BG_COLOR)
		draw_grid()
		draw_panel()
		pygame.display.flip()

	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	main()