import math
import sys
from dataclasses import dataclass

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
PATH_COLOR = (116, 89, 68)
PANEL_BG = (20, 24, 30)
ENEMY_COLOR = (223, 104, 90)
TOWER_COLOR = (0, 225, 0)
BULLET_COLOR = (252, 210, 225)
TEXT_COLOR = (230, 234, 240)

PATH_TILES = [
    (0, 5),
    (1, 5),
    (2, 5),
    (3, 5),
    (4, 5),
    (5, 5),
    (5, 6),
    (5, 7),
    (6, 7),
    (7, 7),
    (8, 7),
    (8, 6),
    (8, 5),
    (9, 5),
    (10, 5),
    (11, 5),
    (12, 5),
    (12, 4),
    (12, 3),
    (13, 3),
    (14, 3),
    (15, 3),
]
PATH_SET = set(PATH_TILES)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")
clock = pygame.time.Clock()
font = pygame.font.SysFont("menlo", 20)
small_font = pygame.font.SysFont("menlo", 16)


def tile_center(col, row):
    return (col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2)


PATH_POINTS = [tile_center(c, r) for c, r in PATH_TILES]


@dataclass
class Enemy:
    x: float
    y: float
    speed: float = 90.0
    path_index: int = 0
    health: float = 40.0
    max_health: float = 40.0
    is_boss: bool = False

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
        radius = 22 if self.is_boss else 14
        color = (180, 70, 48) if self.is_boss else ENEMY_COLOR
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius)
        bar_w = 44 if self.is_boss else 28
        pct = 0.0 if self.max_health <= 0 else max(0.0, self.health / self.max_health)
        bar_x = int(self.x - bar_w / 2)
        bar_y = int(self.y - (32 if self.is_boss else 22))
        pygame.draw.rect(screen, (45, 16, 14), (bar_x, bar_y, bar_w, 6))
        pygame.draw.rect(screen, (77, 201, 112), (bar_x, bar_y, int(bar_w * pct), 6))


@dataclass
class Tower:
    col: int
    row: int
    level: int = 1
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
        size = 24 + (self.level - 1) * 2
        pygame.draw.rect(
            screen,
            TOWER_COLOR,
            (cx - size // 2, cy - size // 2, size, size),
            border_radius=4,
        )
        if self.level > 1:
            level_text = small_font.render(str(self.level), True, (10, 17, 25))
            screen.blit(level_text, (cx - 4, cy - 8))


@dataclass
class Bullet:
    x: float
    y: float
    target: Enemy
    damage: float
    speed: float = 420.0

    def update(self, dt):
        if self.target.health <= 0 or self.target.path_index >= len(PATH_POINTS) - 1:
            return True

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 8:
            self.target.health -= self.damage
            return True

        step = min(self.speed * dt, dist)
        if dist > 1e-6:
            self.x += dx / dist * step
            self.y += dy / dist * step
        return False

    def draw(self):
        pygame.draw.circle(screen, BULLET_COLOR, (int(self.x), int(self.y)), 4)


class WaveController:
    def __init__(self):
        self.wave_index = 0
        self.active = False
        self.spawned = 0
        self.total = 0
        self.spawn_timer = 0.0
        self.enemy_health = 40.0
        self.enemy_speed = 90.0
        self.spawn_interval = 0.8
        self.boss_pending = False
        self.boss_spawned = False
        self.boss_health = 0.0
        self.boss_speed = 0.0
        self.auto_mode = False

    def begin_wave(self):
        if self.active:
            return False
        self.active = True
        self.wave_index += 1
        self.spawned = 0
        self.total = 8 + self.wave_index * 4
        self.enemy_health = 30 + self.wave_index * 10
        self.enemy_speed = min(270.0, 84 + self.wave_index * 6.5)
        self.spawn_interval = max(0.18, 0.8 - self.wave_index * 0.015)
        self.boss_pending = self.wave_index % 10 == 0
        self.boss_spawned = False
        self.boss_health = self.enemy_health * 24
        self.boss_speed = max(75.0, self.enemy_speed * 0.78)
        self.spawn_timer = 0.2
        return True

    def update(self, dt, enemies):
        if not self.active:
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and self.spawned < self.total:
            enemies.append(
                Enemy(
                    *PATH_POINTS[0],
                    speed=self.enemy_speed,
                    health=self.enemy_health,
                    max_health=self.enemy_health,
                )
            )
            self.spawned += 1
            self.spawn_timer = self.spawn_interval

        if self.spawned >= self.total and self.boss_pending and not self.boss_spawned and self.spawn_timer <= 0:
            enemies.append(
                Enemy(
                    *PATH_POINTS[0],
                    speed=self.boss_speed,
                    health=self.boss_health,
                    max_health=self.boss_health,
                    is_boss=True,
                )
            )
            self.boss_spawned = True

        if self.spawned >= self.total and (not self.boss_pending or self.boss_spawned) and len(enemies) == 0:
            self.active = False


def tower_at(towers, col, row):
    for tower in towers:
        if tower.col == col and tower.row == row:
            return tower
    return None


def can_place_tower(towers, col, row):
    if col < 0 or col >= GRID_COLS or row < 0 or row >= GRID_ROWS:
        return False
    if (col, row) in PATH_SET:
        return False
    if tower_at(towers, col, row) is not None:
        return False
    return True


def tower_range(tower):
    return 120 + (tower.level - 1) * 28


def tower_damage(tower):
    return 18 + (tower.level - 1) * 12


def tower_fire_rate(tower):
    return 1.0 + (tower.level - 1) * 0.35


def update_towers(towers, enemies, bullets, dt):
    for tower in towers:
        tower.cooldown -= dt
        if tower.cooldown > 0:
            continue

        target = None
        for enemy in enemies:
            if enemy.health <= 0:
                continue
            d = math.hypot(enemy.x - tower.x, enemy.y - tower.y)
            if d <= tower_range(tower):
                target = enemy
                break

        if target is not None:
            bullets.append(Bullet(tower.x, tower.y, target, tower_damage(tower)))
            tower.cooldown = 1.0 / tower_fire_rate(tower)


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


def draw_hud(gold, lives, wave_num, message, tower_cost, upgrade_cost, auto_mode):
    lines = [
        f"Gold: {gold}",
        f"Lives: {lives}",
        f"Wave: {wave_num}",
        f"Tower Cost: {tower_cost}",
        f"Upgrade Cost: {upgrade_cost}",
        "",
        "S: start wave",
        f"A: auto waves: {'ON' if auto_mode else 'OFF'}",
        "U: upgrade selected",
        "R: restart",
        "",
        message,
    ]

    y = 18
    for line in lines:
        surf = font.render(line, True, TEXT_COLOR)
        screen.blit(surf, (BOARD_WIDTH + 14, y))
        y += 26


def draw_overlay(game_state):
    if game_state == "playing":
        return

    overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((7, 10, 14, 170))
    screen.blit(overlay, (0, 0))

    title = "Victory" if game_state == "win" else "Defeat"
    title_surf = font.render(title, True, TEXT_COLOR)
    prompt_surf = font.render("Press R to play again", True, TEXT_COLOR)
    screen.blit(title_surf, (BOARD_WIDTH // 2 - 44, BOARD_HEIGHT // 2 - 30))
    screen.blit(prompt_surf, (BOARD_WIDTH // 2 - 120, BOARD_HEIGHT // 2 + 5))


def reset_game_state():
    return {
        "gold": 220,
        "lives": 20,
        "message": "Press S to start wave.",
        "game_state": "playing",
        "towers": [],
        "selected_tower": None,
        "enemies": [],
        "bullets": [],
        "waves": WaveController(),
    }


def main():
    state = reset_game_state()
    gold = state["gold"]
    lives = state["lives"]
    message = state["message"]
    game_state = state["game_state"]
    towers = state["towers"]
    selected_tower = state["selected_tower"]
    enemies = state["enemies"]
    bullets = state["bullets"]
    waves = state["waves"]

    tower_cost = 70
    upgrade_cost = 90
    total_waves = 50

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    state = reset_game_state()
                    gold = state["gold"]
                    lives = state["lives"]
                    message = state["message"]
                    game_state = state["game_state"]
                    towers = state["towers"]
                    selected_tower = state["selected_tower"]
                    enemies = state["enemies"]
                    bullets = state["bullets"]
                    waves = state["waves"]

                if game_state != "playing":
                    continue

                if event.key == pygame.K_s:
                    if waves.begin_wave():
                        if waves.boss_pending:
                            message = f"Wave {waves.wave_index} started. Boss incoming!"
                        else:
                            message = f"Wave {waves.wave_index} started."
                if event.key == pygame.K_a:
                    waves.auto_mode = not waves.auto_mode
                    message = f"Auto waves {'enabled' if waves.auto_mode else 'disabled'}."
                if event.key == pygame.K_u and selected_tower is not None:
                    if selected_tower.level >= 10:
                        message = "Tower is already max level."
                    elif gold >= upgrade_cost:
                        selected_tower.level += 1
                        gold -= upgrade_cost
                        message = f"Tower upgraded to L{selected_tower.level}."
                    else:
                        message = "Not enough gold for upgrade."

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state == "playing":
                mx, my = event.pos
                if mx < BOARD_WIDTH:
                    col = mx // TILE_SIZE
                    row = my // TILE_SIZE
                    clicked = tower_at(towers, col, row)
                    if clicked is not None:
                        selected_tower = clicked
                    elif can_place_tower(towers, col, row) and gold >= tower_cost:
                        towers.append(Tower(col, row))
                        selected_tower = towers[-1]
                        gold -= tower_cost
                        message = "Tower placed."
                    elif gold < tower_cost:
                        message = "Not enough gold."

        if game_state == "playing":
            if waves.auto_mode and not waves.active and len(enemies) == 0 and waves.wave_index < total_waves:
                waves.begin_wave()

            waves.update(dt, enemies)

            for enemy in list(enemies):
                enemy.update(dt)
                if enemy.path_index >= len(PATH_POINTS) - 1:
                    enemies.remove(enemy)
                    if enemy.is_boss:
                        lives -= 5
                        message = "Boss leaked through!"
                    else:
                        lives -= 1
                        message = "Enemy leaked through!"
                elif enemy.health <= 0:
                    enemies.remove(enemy)
                    gold += 120 if enemy.is_boss else 12

            update_towers(towers, enemies, bullets, dt)

            for bullet in list(bullets):
                if bullet.update(dt):
                    bullets.remove(bullet)

            if waves.active and waves.spawned >= waves.total and len(enemies) == 0:
                waves.active = False
                if waves.wave_index % 10 == 0:
                    message = f"Boss wave {waves.wave_index} cleared."
                else:
                    message = f"Wave {waves.wave_index} cleared."

            if lives <= 0:
                game_state = "lose"
                message = "Defeat. Press R to restart."

            if waves.wave_index >= total_waves and not waves.active and len(enemies) == 0:
                game_state = "win"
                message = "Victory. Press R to restart."

        screen.fill(BG_COLOR)
        draw_grid()

        for enemy in enemies:
            enemy.draw()

        for bullet in bullets:
            bullet.draw()

        for tower in towers:
            tower.draw()
            if tower is selected_tower:
                pygame.draw.circle(
                    screen,
                    (255, 215, 117),
                    (int(tower.x), int(tower.y)),
                    int(tower_range(tower)),
                    2,
                )

        draw_panel()
        draw_hud(gold, lives, waves.wave_index, message, tower_cost, upgrade_cost, waves.auto_mode)
        draw_overlay(game_state)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()