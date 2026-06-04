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
TOWER_COLOR = (0, 225, 0)
BULLET_COLOR = (252, 210, 78)
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
class WaveController:
	def __init__(self):
		self.wave_index = 0
		self.active = False
		self.spawned = 0
		self.total = 0
		self.spawn_timer = 0.0

	def begin_wave(self):
		if self.active:
			return False
		self.active = True
		self.wave_index += 1
		self.spawned = 0
		self.total = 6 + self.wave_index * 2
		self.spawn_timer = 0.2
		return True

	def update(self, dt, enemies):
		if not self.active:
			return
		self.spawn_timer -= dt
		if self.spawn_timer <= 0 and self.spawned < self.total:
			enemies.append(Enemy(*PATH_POINTS[0]))
			self.spawned += 1
			self.spawn_timer = 0.8

@dataclass
class Tower:
	col: int
	row: int
	cooldown: float = 0.0
	@property
	def x(self):
		return self.col * TILE_SIZE + TILE_SIZE / 2

	@property
	def y(self):
		return self.row * TILE_SIZE + TILE_SIZE / 2

	def draw(self):
		cx = int(self.x)
		cy = int(self.y)
		pygame.draw.rect(screen, TOWER_COLOR, (cx - 14, cy - 14, 28, 28), border_radius=4)

@dataclass
class Enemy:
	x: float
	y: float
	speed: float = 90.0
	path_index: int = 0
	health: float = 40
	max_health: float = 40

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
		bar_w = 28
		pct = max(0.0, self.health / self.max_health)
		pygame.draw.rect(screen, (45, 16, 14), (int(self.x - 14), int(self.y - 22), bar_w, 5))
		pygame.draw.rect(screen, (77, 201, 112), (int(self.x - 14), int(self.y - 22), int(bar_w * pct), 5))
		pygame.draw.circle(screen, ENEMY_COLOR, (int(self.x), int(self.y)), 14)

@dataclass
class Bullet:
	x: float
	y: float
	target: Enemy
	damage: float
	speed: float = 420.0

	def update(self, dt):
		if self.target.health <= 0:
			return True
		dx = self.target.x - self.x
		dy = self.target.y - self.y
		dist = math.hypot(dx, dy)
		if dist < 8:
			self.target.health -= self.damage
			return True
		step = self.speed * dt
		self.x += dx / dist * min(step, dist)
		self.y += dy / dist * min(step, dist)
		return False

	def draw(self):
		pygame.draw.circle(screen, BULLET_COLOR, (int(self.x), int(self.y)), 4)
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

def update_towers(towers, enemies, bullets, dt):
	for tower in towers:
		tower.cooldown -= dt
		if tower.cooldown > 0:
			continue

		target = None
		for enemy in enemies:
			d = math.hypot(enemy.x - tower.x, enemy.y - tower.y)
			if enemy.health > 0 and d <= tower_range(tower):
				target = enemy
				break

		if target is not None:
			bullets.append(Bullet(tower.x, tower.y, target, tower_damage(tower)))
			tower.cooldown = 1.0 / tower_fire_rate(tower)

def draw_panel():
	pygame.draw.rect(screen, PANEL_BG, (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

def tower_range(tower):
	return 120
def tower_damage(tower):
	return 18
def tower_fire_rate(tower):
	return 1.0

def tower_at(towers, col, row):
	for t in towers:
		if t.col == col and t.row == row:
			return t
	return None

def can_place_tower(towers, col, row):
	if col < 0 or col >= GRID_COLS or row < 0 or row >= GRID_ROWS:
		return False
	if (col, row) in PATH_SET:
		return False
	if tower_at(towers, col, row) is not None:
		return False
	return True

def main():
	running = True
	enemies = []
	towers = []
	bullets = []
	waves = WaveController()
	enemy = Enemy(*PATH_POINTS[0])

	while running:
		screen.fill(BG_COLOR)
		dt = clock.tick(FPS) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_s:
					waves.begin_wave()
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				mx, my = event.pos
				if mx < BOARD_WIDTH:
					col = mx // TILE_SIZE
					row = my // TILE_SIZE
					if can_place_tower(towers, col, row):
						towers.append(Tower(col, row))
		waves.update(dt, enemies)
		
		for enemy in enemies:
			enemy.update(dt)
		draw_grid()
		for enemy in enemies:
			enemy.draw()
		for tower in towers:
			tower.draw()
		draw_panel()
		update_towers(towers, enemies, bullets, dt)

		for b in list(bullets):
			if b.update(dt):
				bullets.remove(b)
		for b in bullets:
			b.draw()

		for enemy in list(enemies):
			if enemy.health <= 0:
				enemies.remove(enemy)
		
		pygame.display.flip()

	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	main()