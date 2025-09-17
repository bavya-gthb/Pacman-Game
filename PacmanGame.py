import pygame
import random
import time

# Initialize pygame
pygame.init()

# Game settings
screen_width, screen_height = 800, 600
background_color = (0, 0, 0)
pacman_color = (255, 255, 0)
ghost_color = (255, 0, 0)
food_color = (0, 255, 0)
wall_color = (128, 128, 128)
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pac-Man")

pacman_size = 20
pacman_speed = 5
pacman_x, pacman_y = screen_width // 2, screen_height // 2

ghost_size = 20
ghosts = []
ghost_speed = 3

food_size = 10
food_items = []

walls = []
wall_size = 30
wall_count = 5

score = 0
level = 1
font = pygame.font.Font(None, 36)

celebration_duration = 80
explosion_particles = []
celebration_timer = 0
celebration_active = False

clock = pygame.time.Clock()

# Collision detection
def rects_collide(x1, y1, w1, h1, x2, y2, w2, h2):
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)

# Particle class for celebrations
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(3, 7)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.x_velocity = random.uniform(-4, 4)
        self.y_velocity = random.uniform(-4, 4)
        self.life = random.randint(20, 40)
    def move(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.life -= 1
    def draw(self):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

def celebration_blast(x, y):
    global explosion_particles
    explosion_particles.clear()
    for _ in range(120):
        explosion_particles.append(Particle(x + random.randint(-10, 10), y + random.randint(-10, 10)))

# --- UPDATED spawn_ghost ---
def spawn_ghost(level, pacman_x, pacman_y, region=None):
    attempts = 0
    min_distance = 120  # <-- always keep ghosts away from Pac-Man at start
    while attempts < 1000:
        attempts += 1
        if level == 3 and region is not None:
            x = random.randint(region[0], region[2] - ghost_size)
            y = random.randint(region[1], region[3] - ghost_size)
        else:
            x = random.randint(0, screen_width - ghost_size)
            y = random.randint(0, screen_height - ghost_size)
            if level == 2 and region is not None:
                if region == "upper" and y >= screen_height // 2:
                    continue
                if region == "lower" and y < screen_height // 2:
                    continue
        # Keep enough distance from Pac-Man
        if abs(pacman_x - x) < min_distance and abs(pacman_y - y) < min_distance:
            continue
        # Make sure it doesn't spawn inside walls
        collides_with_wall = any(
            rects_collide(x, y, ghost_size, ghost_size, w["x"], w["y"], w["width"], w["height"]) 
            for w in walls
        )
        if collides_with_wall:
            continue
        ghosts.append({"x": x, "y": y, "speed": ghost_speed, "region": region})
        return
    ghosts.append({"x": random.randint(0, screen_width - ghost_size),
                   "y": random.randint(0, screen_height - ghost_size),
                   "speed": ghost_speed, "region": region})

# Spawn food
def spawn_food():
    attempts = 0
    while attempts < 1000:
        attempts += 1
        food_x = random.randint(0, screen_width - food_size)
        food_y = random.randint(0, screen_height - food_size)
        if rects_collide(food_x, food_y, food_size, food_size, pacman_x, pacman_y, pacman_size, pacman_size):
            continue
        overlap = False
        for w in walls:
            if rects_collide(food_x, food_y, food_size, food_size, w["x"], w["y"], w["width"], w["height"]):
                overlap = True
                break
        if overlap:
            continue
        food_items.clear()
        food_items.append({"x": food_x, "y": food_y})
        return
    food_items.clear()
    food_items.append({"x": 10, "y": 10})

# Generate walls
def generate_walls():
    global walls
    walls.clear()
    tries = 0
    while len(walls) < wall_count and tries < 2000:
        tries += 1
        wall_length = random.randint(100, 250)
        horizontal = random.choice([True, False])
        if horizontal:
            x = random.randint(0, max(0, screen_width - wall_length))
            y = random.randint(0, max(0, screen_height - wall_size))
            new_wall = {"x": x, "y": y, "width": wall_length, "height": wall_size}
        else:
            x = random.randint(0, max(0, screen_width - wall_size))
            y = random.randint(0, max(0, screen_height - wall_length))
            new_wall = {"x": x, "y": y, "width": wall_size, "height": wall_length}
        # Avoid center
        if rects_collide(new_wall["x"], new_wall["y"], new_wall["width"], new_wall["height"],
                         screen_width // 2 - 40, screen_height // 2 - 40, 80, 80):
            continue
        overlap = False
        for w in walls:
            if rects_collide(new_wall["x"], new_wall["y"], new_wall["width"], new_wall["height"],
                             w["x"], w["y"], w["width"], w["height"]):
                overlap = True
                break
        if overlap:
            continue
        walls.append(new_wall)

# Check collision with walls
def check_wall_collision(x, y):
    for wall in walls:
        if rects_collide(x, y, pacman_size, pacman_size, wall["x"], wall["y"], wall["width"], wall["height"]):
            return True
    return False

# Reset game
def reset_game():
    global pacman_x, pacman_y, score, level, ghosts, food_items, walls, game_over, celebration_active, celebration_timer
    walls.clear()
    generate_walls()

    pacman_x, pacman_y = screen_width // 2, screen_height // 2
    while check_wall_collision(pacman_x, pacman_y):
        pacman_x = random.randint(0, screen_width - pacman_size)
        pacman_y = random.randint(0, screen_height - pacman_size)

    score = 0
    level = 1
    ghosts = []
    food_items = []
    celebration_active = False
    celebration_timer = 0
    game_over = False

    spawn_ghost(level, pacman_x, pacman_y)
    spawn_food()

# Initial setup
walls.clear()
generate_walls()
while check_wall_collision(pacman_x, pacman_y):
    pacman_x = random.randint(0, screen_width - pacman_size)
    pacman_y = random.randint(0, screen_height - pacman_size)

spawn_ghost(level, pacman_x, pacman_y)
spawn_food()
running = True
game_over = False

# --- Main Game Loop ---
while running:
    screen.fill(background_color)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and game_over:
                reset_game()

    if not game_over:
        # --- Pac-Man movement ---
        move_x, move_y = 0, 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            move_x = -pacman_speed
        if keys[pygame.K_RIGHT]:
            move_x = pacman_speed
        if keys[pygame.K_UP]:
            move_y = -pacman_speed
        if keys[pygame.K_DOWN]:
            move_y = pacman_speed

        proposed_x = pacman_x + move_x
        proposed_y = pacman_y + move_y

        # Prevent Pac-Man from entering walls in Level 3
        if level == 3:
            if not check_wall_collision(proposed_x, pacman_y):
                pacman_x = max(0, min(screen_width - pacman_size, proposed_x))
            if not check_wall_collision(pacman_x, proposed_y):
                pacman_y = max(0, min(screen_height - pacman_size, proposed_y))
        else:
            pacman_x = max(0, min(screen_width - pacman_size, proposed_x))
            pacman_y = max(0, min(screen_height - pacman_size, proposed_y))

        # --- Ghost movement ---
        for ghost in ghosts:
            if level == 2 and ghost.get("region") == "upper" and pacman_y >= screen_height // 2:
                continue
            if level == 2 and ghost.get("region") == "lower" and pacman_y < screen_height // 2:
                continue
            if level == 3:
                region = ghost["region"]
                # Ghost chases only if Pac-Man is inside its region
                if region[0] <= pacman_x < region[2] and region[1] <= pacman_y < region[3]:
                    possible_moves = [(ghost_speed, 0), (-ghost_speed, 0), (0, ghost_speed), (0, -ghost_speed)]
                    possible_moves.sort(key=lambda m: abs((ghost["x"] + m[0]) - pacman_x) +
                                                   abs((ghost["y"] + m[1]) - pacman_y))
                    moved = False
                    for dx, dy in possible_moves:
                        new_x = ghost["x"] + dx
                        new_y = ghost["y"] + dy
                        if check_wall_collision(new_x, new_y):
                            continue
                        collision_with_ghost = any(rects_collide(new_x, new_y, ghost_size, ghost_size,
                                                                other["x"], other["y"], ghost_size, ghost_size)
                                                   for other in ghosts if other != ghost)
                        if not collision_with_ghost:
                            ghost["x"] = new_x
                            ghost["y"] = new_y
                            moved = True
                            break
                    if not moved:
                        random.shuffle(possible_moves)
                        for dx, dy in possible_moves:
                            new_x = ghost["x"] + dx
                            new_y = ghost["y"] + dy
                            if check_wall_collision(new_x, new_y):
                                continue
                            collision_with_ghost = any(rects_collide(new_x, new_y, ghost_size, ghost_size,
                                                                    other["x"], other["y"], ghost_size, ghost_size)
                                                       for other in ghosts if other != ghost)
                            if not collision_with_ghost:
                                ghost["x"] = new_x
                                ghost["y"] = new_y
                                break
                # Else: Pac-Man not in this region → ghost stays idle
            else:
                dx, dy = 0, 0
                if pacman_x > ghost["x"]:
                    dx = ghost["speed"]
                elif pacman_x < ghost["x"]:
                    dx = -ghost["speed"]
                if pacman_y > ghost["y"]:
                    dy = ghost["speed"]
                elif pacman_y < ghost["y"]:
                    dy = -ghost["speed"]
                ghost["x"] += dx
                ghost["y"] += dy

            ghost["x"] = max(0, min(screen_width - ghost_size, ghost["x"]))
            ghost["y"] = max(0, min(screen_height - ghost_size, ghost["y"]))

            if rects_collide(pacman_x, pacman_y, pacman_size, pacman_size, ghost["x"], ghost["y"], ghost_size, ghost_size):
                game_over = True

        # --- Food collection ---
        for food in food_items[:]:
            if rects_collide(pacman_x, pacman_y, pacman_size, pacman_size, food["x"], food["y"], food_size, food_size):
                score += 1
                food_items.clear()
                spawn_food()

        # --- Level progression ---
        if score >= 10:
            if level < 3:
                screen.blit(pygame.font.Font(None, 36).render(f"Level {level} Passed - Next level starting...", True, (255, 255, 255)), (screen_width // 2 - 200, screen_height // 2))
                pygame.display.flip()
                pygame.time.delay(1000)
                level += 1
                score = 0
                if level == 2:
                    ghosts.clear()
                    spawn_ghost(level, pacman_x, pacman_y, region="upper")
                    spawn_ghost(level, pacman_x, pacman_y, region="lower")
                elif level == 3:
                    ghosts.clear()
                    quadrants = [
                        (0, 0, screen_width // 2, screen_height // 2),
                        (screen_width // 2, 0, screen_width, screen_height // 2),
                        (0, screen_height // 2, screen_width // 2, screen_height),
                        (screen_width // 2, screen_height // 2, screen_width, screen_height)
                    ]
                    generate_walls()
                    for q in quadrants:
                        attempts = 0
                        while attempts < 1000:
                            attempts += 1
                            x = random.randint(q[0], q[2] - ghost_size)
                            y = random.randint(q[1], q[3] - ghost_size)
                            collides_with_wall = any(rects_collide(x, y, ghost_size, ghost_size,
                                                                  w["x"], w["y"], w["width"], w["height"]) for w in walls)
                            if not collides_with_wall:
                                ghosts.append({"x": x, "y": y, "speed": ghost_speed, "region": q})
                                break
                    while check_wall_collision(pacman_x, pacman_y):
                        pacman_x = random.randint(0, screen_width - pacman_size)
                        pacman_y = random.randint(0, screen_height - pacman_size)
                spawn_food()
            else:
                celebration_active = True
                celebration_blast(x=screen_width // 2, y=screen_height // 2)
                celebration_timer = 0
                level = 3
                game_over = True

        # --- Drawing ---
        pygame.draw.rect(screen, pacman_color, (int(pacman_x), int(pacman_y), pacman_size, pacman_size))
        for ghost in ghosts:
            pygame.draw.rect(screen, ghost_color, (int(ghost["x"]), int(ghost["y"]), ghost_size, ghost_size))
        for food in food_items:
            pygame.draw.rect(screen, food_color, (food["x"], food["y"], food_size, food_size))
        if level == 3:
            for wall in walls:
                pygame.draw.rect(screen, wall_color, (wall["x"], wall["y"], wall["width"], wall["height"]))
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        level_text = font.render(f"Level: {level}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (screen_width - 120, 10))

    else:
        # --- Game over screen ---
        game_over_text = font.render("Game Over!", True, (255, 255, 255))
        final_score_text = font.render("Final Score: " + str(score), True, (255, 255, 255))
        screen.blit(game_over_text, (screen_width // 2 - 70, screen_height // 2 - 20))
        screen.blit(final_score_text, (screen_width // 2 - 90, screen_height // 2 + 10))
        screen.blit(pygame.font.Font(None, 28).render("Press Enter to Play Again", True, (255, 255, 255)), (screen_width // 2 - 115, screen_height // 2 + 90))
        if celebration_active:
            celebration_timer += 1
            if celebration_timer < celebration_duration:
                for particle in explosion_particles:
                    particle.move()
                    particle.draw()
            else:
                screen.blit(pygame.font.Font(None, 36).render("Congratulations! You Completed All Levels!", True, (255, 255, 255)), (screen_width // 2 - 220, screen_height // 2 - 50))
        else:
            celebration_active = False

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
