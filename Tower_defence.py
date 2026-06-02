import sys
import pygame
import math
from dataclasses import dataclass
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

PATH_COLOR = (116, 89, 68)
ENEMY_COLOR = (223, 104, 90)

PATH_TILES = [
	(0, 5), (1, 5), (2, 5), (3, 5), (4, 5),
	(5, 5), (5, 6), (5, 7), (6, 7), (7, 7),
	(8, 7), (8, 6), (8, 5), (9, 5), (10, 5),
	(11, 5), (12, 5), (12, 4), (12, 3),
	(13, 3), (14, 3), (15, 3),
]
PATH_SET = set(PATH_TILES)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense - Day 1")
clock = pygame.time.Clock()

@dataclass
class Enemy:
	x: float
	y: float
	speed: float = 90.0
	path_index: int = 0

	def update(self, dt):
		if self.path_index >= len(PATH_POINTS) - 1:
			return
		tx, ty = PATH_POINTS[self.path_index + 1]
		dx = tx - self.x
		dy = ty - self.y
		dist = math.hypot(dx, dy)
		if dist < 1e-4:
			self.path_index += 1
			return

		step = self.speed * dt
		if step >= dist:
			self.x, self.y = tx, ty
			self.path_index += 1
		else:
			self.x += dx / dist * step
			self.y += dy / dist * step

	def draw(self):
		pygame.draw.circle(screen, ENEMY_COLOR, (int(self.x), int(self.y)), 14)

def tile_center(col, row):
	return (col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2)


PATH_POINTS = [tile_center(c, r) for c, r in PATH_TILES]

def draw_grid():
	for row in range(GRID_ROWS):
		for col in range(GRID_COLS):
			x = col * TILE_SIZE
			y = row * TILE_SIZE
			tile_color = PATH_COLOR if (col, row) in PATH_SET else GRASS_COLOR
			pygame.draw.rect(screen, tile_color, (x, y, TILE_SIZE, TILE_SIZE))
			pygame.draw.rect(screen, GRID_COLOR, (x, y, TILE_SIZE, TILE_SIZE), 1)


def draw_panel():
	pygame.draw.rect(screen, PANEL_BG, (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

def main():
	running = True
	enemy = Enemy(*PATH_POINTS[0])
	while running:
		dt = clock.tick(FPS) / 1000.0
	enemy.update(dt)
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