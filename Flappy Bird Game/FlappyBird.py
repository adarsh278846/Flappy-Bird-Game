import pygame
import random
import math
import json
import os
import wave
import struct
from pathlib import Path

# ============================================================
# INITIALIZATION
# ============================================================

pygame.init()

WIDTH = 1000
HEIGHT = 700
FPS = 240

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird - Ultimate Edition")
CLOCK = pygame.time.Clock()

# ============================================================
# PATHS / SAVE DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SAVE_FILE = DATA_DIR / "flappy_data.json"
SOUND_DIR = DATA_DIR / "sounds"
SOUND_DIR.mkdir(exist_ok=True)

default_data = {
    "high_score": 0,
    "sound": True,
    "music": True
}

if SAVE_FILE.exists():
    try:
        with open(SAVE_FILE, "r") as f:
            save_data = json.load(f)
    except:
        save_data = default_data.copy()
else:
    save_data = default_data.copy()


def save_game_data():
    with open(SAVE_FILE, "w") as f:
        json.dump(save_data, f, indent=4)


# ============================================================
# COLORS
# ============================================================

WHITE = (255, 255, 255)
BLACK = (15, 15, 20)

SKY_DAY_TOP = (92, 190, 245)
SKY_DAY_BOTTOM = (190, 235, 255)

SKY_NIGHT_TOP = (20, 28, 70)
SKY_NIGHT_BOTTOM = (55, 70, 125)

GROUND = (90, 190, 70)
GROUND_DARK = (60, 145, 50)

PIPE_GREEN = (65, 190, 70)
PIPE_DARK = (35, 130, 45)
PIPE_LIGHT = (110, 225, 105)

BIRD_YELLOW = (255, 215, 55)
BIRD_ORANGE = (235, 150, 25)
BIRD_WHITE = (255, 255, 255)

RED = (235, 65, 65)
GOLD = (255, 205, 50)

# ============================================================
# FONTS
# ============================================================

FONT_SMALL = pygame.font.Font(None, 28)
FONT_MEDIUM = pygame.font.Font(None, 38)
FONT_LARGE = pygame.font.Font(None, 58)
FONT_HUGE = pygame.font.Font(None, 92)
FONT_TITLE = pygame.font.Font(None, 105)

# ============================================================
# AUDIO
# ============================================================

audio_available = False
sounds = {}


def create_tone(
    filename,
    frequency=440,
    duration=0.1,
    volume=0.4,
    second_frequency=None
):
    sample_rate = 44100
    frames = int(sample_rate * duration)

    with wave.open(str(filename), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(frames):
            t = i / sample_rate

            if second_frequency:
                progress = i / frames
                freq = frequency * (1 - progress) + second_frequency * progress
            else:
                freq = frequency

            envelope = 1.0

            fade = int(sample_rate * 0.015)

            if i < fade:
                envelope = i / fade
            elif i > frames - fade:
                envelope = (frames - i) / fade

            value = math.sin(2 * math.pi * freq * t)
            value *= volume * envelope

            sample = int(value * 32767)

            wav.writeframes(struct.pack("<h", sample))


def create_music(filename):
    sample_rate = 44100

    melody = [
        523,
        659,
        784,
        659,
        587,
        698,
        880,
        698
    ]

    note_duration = 0.25
    total_frames = int(sample_rate * note_duration * len(melody))

    with wave.open(str(filename), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(total_frames):
            t = i / sample_rate

            note_index = int(t / note_duration)
            note_index = min(note_index, len(melody) - 1)

            freq = melody[note_index]

            local_t = t % note_duration

            envelope = 1.0

            fade = 0.03

            if local_t < fade:
                envelope = local_t / fade
            elif local_t > note_duration - fade:
                envelope = (note_duration - local_t) / fade

            value = math.sin(2 * math.pi * freq * local_t)
            value *= 0.08 * envelope

            sample = int(value * 32767)

            wav.writeframes(struct.pack("<h", sample))


try:
    pygame.mixer.init()
    audio_available = True

    sound_files = {
        "flap": (700, 0.08, 0.35),
        "score": (900, 0.12, 0.35),
        "hit": (150, 0.25, 0.45),
        "click": (1100, 0.05, 0.25),
        "life": (500, 0.15, 0.3),
    }

    for name, values in sound_files.items():
        path = SOUND_DIR / f"{name}.wav"

        if not path.exists():
            create_tone(
                path,
                values[0],
                values[1],
                values[2]
            )

        sounds[name] = pygame.mixer.Sound(str(path))

    music_path = SOUND_DIR / "music.wav"

    if not music_path.exists():
        create_music(music_path)

    pygame.mixer.music.load(str(music_path))

except pygame.error:
    audio_available = False


def play_sound(name):
    if audio_available and save_data.get("sound", True):
        try:
            sounds[name].play()
        except:
            pass


def update_music():
    if not audio_available:
        return

    if save_data.get("music", True):
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def lerp(a, b, amount):
    return a + (b - a) * amount


def lerp_color(c1, c2, amount):
    return (
        int(lerp(c1[0], c2[0], amount)),
        int(lerp(c1[1], c2[1], amount)),
        int(lerp(c1[2], c2[2], amount))
    )


def draw_text(
    surface,
    text,
    font,
    color,
    center,
    shadow=True
):
    if shadow:
        shadow_surface = font.render(text, True, BLACK)
        shadow_rect = shadow_surface.get_rect(
            center=(center[0] + 3, center[1] + 3)
        )
        surface.blit(shadow_surface, shadow_rect)

    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=center)

    surface.blit(text_surface, rect)


def draw_gradient(surface, top_color, bottom_color, height):
    surface.fill(top_color)

    steps = 40

    for i in range(steps):
        y = int(height * i / steps)
        next_y = int(height * (i + 1) / steps)

        amount = i / (steps - 1)

        color = lerp_color(
            top_color,
            bottom_color,
            amount
        )

        pygame.draw.rect(
            surface,
            color,
            (
                0,
                y,
                WIDTH,
                next_y - y + 1
            )
        )


# ============================================================
# PARTICLES
# ============================================================

class Particle:

    def __init__(self, x, y, color, speed=3):
        self.x = x
        self.y = y

        angle = random.uniform(0, math.pi * 2)

        velocity = random.uniform(1, speed)

        self.vx = math.cos(angle) * velocity
        self.vy = math.sin(angle) * velocity

        self.life = random.uniform(0.4, 0.9)
        self.max_life = self.life

        self.size = random.randint(3, 7)

        self.color = color

    def update(self, dt):

        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt

        self.vy += 0.08

        self.life -= dt

    def draw(self, surface):

        if self.life <= 0:
            return

        ratio = self.life / self.max_life

        size = max(1, int(self.size * ratio))

        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            size
        )


class ParticleSystem:

    def __init__(self):
        self.particles = []

    def burst(self, x, y, color, count=15):

        for _ in range(count):
            self.particles.append(
                Particle(x, y, color)
            )

    def update(self, dt):

        for particle in self.particles:
            particle.update(dt)

        self.particles = [
            p for p in self.particles
            if p.life > 0
        ]

    def draw(self, surface):

        for particle in self.particles:
            particle.draw(surface)


# ============================================================
# CLOUDS
# ============================================================

class Cloud:

    def __init__(self):

        self.x = random.randint(-100, WIDTH)
        self.y = random.randint(60, 250)

        self.speed = random.uniform(15, 35)

        self.scale = random.uniform(0.7, 1.5)

    def update(self, dt):

        self.x -= self.speed * dt

        if self.x < -180:
            self.x = WIDTH + random.randint(20, 150)
            self.y = random.randint(50, 250)

    def draw(self, surface, night):

        color_day = (255, 255, 255)
        color_night = (120, 130, 160)

        color = lerp_color(
            color_day,
            color_night,
            night
        )

        s = self.scale

        x = int(self.x)
        y = int(self.y)

        pygame.draw.ellipse(
            surface,
            color,
            (
                x,
                y + int(15 * s),
                int(100 * s),
                int(40 * s)
            )
        )

        pygame.draw.circle(
            surface,
            color,
            (
                x + int(30 * s),
                y + int(15 * s)
            ),
            int(30 * s)
        )

        pygame.draw.circle(
            surface,
            color,
            (
                x + int(65 * s),
                y + int(5 * s)
            ),
            int(38 * s)
        )


# ============================================================
# BIRD
# ============================================================

class Bird:

    def __init__(self):

        self.x = 230
        self.y = HEIGHT // 2

        self.velocity = 0

        self.gravity = 1550
        self.flap_strength = -510

        self.width = 48
        self.height = 38

        self.angle = 0

        self.animation_time = 0

    def reset(self):

        self.y = HEIGHT // 2
        self.velocity = 0
        self.angle = 0

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x - self.width / 2),
            int(self.y - self.height / 2),
            self.width,
            self.height
        )

    def flap(self):

        self.velocity = self.flap_strength

        play_sound("flap")

    def update(self, dt):

        self.velocity += self.gravity * dt

        self.y += self.velocity * dt

        self.angle = clamp(
            -self.velocity * 0.07,
            -25,
            85
        )

        self.animation_time += dt

    def draw(self, surface):

        # Create bird surface
        bird_surface = pygame.Surface(
            (80, 70),
            pygame.SRCALPHA
        )

        # Body
        pygame.draw.ellipse(
            bird_surface,
            BIRD_YELLOW,
            (12, 18, 52, 38)
        )

        # Body outline
        pygame.draw.ellipse(
            bird_surface,
            BIRD_ORANGE,
            (12, 18, 52, 38),
            3
        )

        # Wing animation
        wing_offset = math.sin(
            self.animation_time * 14
        ) * 5

        pygame.draw.ellipse(
            bird_surface,
            (245, 180, 35),
            (
                20,
                int(34 + wing_offset),
                30,
                18
            )
        )

        # Eye
        pygame.draw.circle(
            bird_surface,
            WHITE,
            (50, 27),
            10
        )

        pygame.draw.circle(
            bird_surface,
            BLACK,
            (53, 27),
            5
        )

        # Beak
        pygame.draw.polygon(
            bird_surface,
            (245, 120, 30),
            [
                (58, 35),
                (78, 42),
                (58, 46)
            ]
        )

        # Tail
        pygame.draw.polygon(
            bird_surface,
            BIRD_ORANGE,
            [
                (15, 32),
                (0, 23),
                (4, 42)
            ]
        )

        rotated = pygame.transform.rotate(
            bird_surface,
            self.angle
        )

        rect = rotated.get_rect(
            center=(int(self.x), int(self.y))
        )

        surface.blit(rotated, rect)


# ============================================================
# PIPE
# ============================================================

class Pipe:

    WIDTH = 85

    def __init__(self, x, gap_y, gap, speed):

        self.x = x
        self.gap_y = gap_y
        self.gap = gap

        self.speed = speed

        self.passed = False

    @property
    def top_rect(self):

        return pygame.Rect(
            int(self.x),
            0,
            self.WIDTH,
            int(self.gap_y - self.gap / 2)
        )

    @property
    def bottom_rect(self):

        bottom_y = self.gap_y + self.gap / 2

        return pygame.Rect(
            int(self.x),
            int(bottom_y),
            self.WIDTH,
            HEIGHT - int(bottom_y)
        )

    def update(self, dt):

        self.x -= self.speed * dt

    def draw_pipe_part(self, surface, rect, cap_at_top):

        # Shadow
        shadow_rect = rect.move(6, 5)

        pygame.draw.rect(
            surface,
            (30, 80, 35),
            shadow_rect
        )

        # Main pipe
        pygame.draw.rect(
            surface,
            PIPE_GREEN,
            rect
        )

        # Highlight
        pygame.draw.rect(
            surface,
            PIPE_LIGHT,
            (
                rect.x + 8,
                rect.y,
                13,
                rect.height
            )
        )

        # Dark side
        pygame.draw.rect(
            surface,
            PIPE_DARK,
            (
                rect.right - 12,
                rect.y,
                12,
                rect.height
            )
        )

        cap_height = 25
        cap_width = self.WIDTH + 14

        if cap_at_top:

            cap = pygame.Rect(
                rect.x - 7,
                rect.bottom - cap_height,
                cap_width,
                cap_height
            )

        else:

            cap = pygame.Rect(
                rect.x - 7,
                rect.top,
                cap_width,
                cap_height
            )

        pygame.draw.rect(
            surface,
            PIPE_GREEN,
            cap,
            border_radius=4
        )

        pygame.draw.rect(
            surface,
            PIPE_DARK,
            cap,
            3,
            border_radius=4
        )

    def draw(self, surface):

        self.draw_pipe_part(
            surface,
            self.top_rect,
            True
        )

        self.draw_pipe_part(
            surface,
            self.bottom_rect,
            False
        )

    def offscreen(self):

        return self.x + self.WIDTH < 0


# ============================================================
# BUTTON
# ============================================================

class Button:

    def __init__(
        self,
        rect,
        text,
        color=(70, 150, 80)
    ):

        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color

    def draw(self, surface):

        mouse_pos = pygame.mouse.get_pos()

        hover = self.rect.collidepoint(mouse_pos)

        color = self.color

        if hover:

            color = tuple(
                min(255, c + 25)
                for c in color
            )

        shadow = self.rect.move(0, 6)

        pygame.draw.rect(
            surface,
            (30, 30, 35),
            shadow,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            color,
            self.rect,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            WHITE,
            self.rect,
            2,
            border_radius=12
        )

        draw_text(
            surface,
            self.text,
            FONT_MEDIUM,
            WHITE,
            self.rect.center
        )

    def clicked(self, event):

        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# ============================================================
# GAME
# ============================================================

MENU = "menu"
COUNTDOWN = "countdown"
PLAYING = "playing"
PAUSED = "paused"
SETTINGS = "settings"
GAME_OVER = "game_over"


class Game:

    def __init__(self):

        self.state = MENU

        self.bird = Bird()

        self.pipes = []

        self.particles = ParticleSystem()

        self.clouds = [
            Cloud()
            for _ in range(8)
        ]

        self.stars = [
            (
                random.randint(0, WIDTH),
                random.randint(20, 350),
                random.randint(1, 3)
            )
            for _ in range(80)
        ]

        self.score = 0
        self.lives = 3

        self.spawn_timer = 0

        self.countdown = 3

        self.world_time = 0

        self.ground_offset = 0

        self.message_timer = 0

        self.start_button = Button(
            (WIDTH // 2 - 130, 360, 260, 65),
            "PLAY"
        )

        self.settings_button = Button(
            (WIDTH // 2 - 130, 445, 260, 65),
            "SETTINGS",
            (70, 100, 170)
        )

        self.menu_button = Button(
            (WIDTH // 2 - 130, 525, 260, 60),
            "MAIN MENU",
            (100, 100, 110)
        )

        self.restart_button = Button(
            (WIDTH // 2 - 130, 450, 260, 65),
            "PLAY AGAIN"
        )

        self.settings_back_button = Button(
            (WIDTH // 2 - 130, 560, 260, 60),
            "BACK",
            (100, 100, 110)
        )

        self.game_over_menu_button = Button(
            (WIDTH // 2 - 130, 530, 260, 60),
            "MAIN MENU",
            (100, 100, 110)
        )

        self.sound_button = Button(
            (WIDTH // 2 - 150, 290, 300, 60),
            ""
        )

        self.music_button = Button(
            (WIDTH // 2 - 150, 370, 300, 60),
            ""
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_game(self):

        self.bird.reset()

        self.pipes.clear()

        self.score = 0

        self.lives = 3

        self.spawn_timer = 0.4

        self.countdown = 3

        self.state = COUNTDOWN

        self.particles.particles.clear()

    # ========================================================
    # DIFFICULTY
    # ========================================================

    def get_difficulty(self):

        speed = 270 + min(
            self.score * 5,
            180
        )

        gap = max(
            135,
            205 - self.score * 1.5
        )

        spawn_interval = max(
            1.05,
            1.65 - self.score * 0.012
        )

        return speed, gap, spawn_interval

    # ========================================================
    # SPAWN PIPE
    # ========================================================

    def spawn_pipe(self):

        speed, gap, _ = self.get_difficulty()

        margin = 100

        min_y = margin + gap / 2
        max_y = HEIGHT - 130 - gap / 2

        gap_y = random.randint(
            int(min_y),
            int(max_y)
        )

        self.pipes.append(
            Pipe(
                WIDTH + 50,
                gap_y,
                gap,
                speed
            )
        )

    # ========================================================
    # SCORE
    # ========================================================

    def increase_score(self):

        self.score += 1

        play_sound("score")

        self.particles.burst(
            self.bird.x,
            self.bird.y,
            GOLD,
            18
        )

        if self.score > save_data["high_score"]:

            save_data["high_score"] = self.score

            save_game_data()

    # ========================================================
    # COLLISION
    # ========================================================

    def check_collision(self):

        bird_rect = self.bird.rect.inflate(
            -10,
            -8
        )

        # Ceiling
        if bird_rect.top <= 0:
            return True

        # Ground
        if bird_rect.bottom >= HEIGHT - 70:
            return True

        for pipe in self.pipes:

            if (
                bird_rect.colliderect(pipe.top_rect)
                or
                bird_rect.colliderect(pipe.bottom_rect)
            ):
                return True

        return False

    # ========================================================
    # HIT
    # ========================================================

    def player_hit(self):

        self.lives -= 1

        play_sound("hit")

        self.particles.burst(
            self.bird.x,
            self.bird.y,
            RED,
            35
        )

        if self.lives <= 0:

            self.state = GAME_OVER

            if self.score > save_data["high_score"]:

                save_data["high_score"] = self.score

            save_game_data()

        else:

            play_sound("life")

            self.bird.reset()

            self.pipes.clear()

            self.spawn_timer = 0.4

            self.countdown = 3

            self.state = COUNTDOWN

    # ========================================================
    # UPDATE
    # ========================================================

    def update(self, dt):

        self.world_time += dt

        self.ground_offset -= 150 * dt

        if self.ground_offset < -40:
            self.ground_offset += 40

        # Clouds always move
        for cloud in self.clouds:
            cloud.update(dt)

        # Particles
        self.particles.update(dt)

        # Music
        update_music()

        # ====================================================
        # COUNTDOWN
        # ====================================================

        if self.state == COUNTDOWN:

            self.countdown -= dt

            self.bird.velocity = 0

            if self.countdown <= 0:

                self.state = PLAYING

            return

        # ====================================================
        # PLAYING
        # ====================================================

        if self.state == PLAYING:

            self.bird.update(dt)

            self.spawn_timer -= dt

            if self.spawn_timer <= 0:

                self.spawn_pipe()

                _, _, interval = self.get_difficulty()

                self.spawn_timer = interval

            for pipe in self.pipes:

                pipe.update(dt)

                if (
                    not pipe.passed
                    and pipe.x + pipe.WIDTH < self.bird.x
                ):

                    pipe.passed = True

                    self.increase_score()

            self.pipes = [
                p for p in self.pipes
                if not p.offscreen()
            ]

            if self.check_collision():

                self.player_hit()

    # ========================================================
    # BACKGROUND
    # ========================================================

    def draw_background(self):

        # 45 second day/night cycle
        cycle = (
            self.world_time % 45
        ) / 45

        night = (
            math.sin(
                cycle * math.pi * 2
                - math.pi / 2
            )
            + 1
        ) / 2

        draw_gradient(
            SCREEN,
            lerp_color(
                SKY_DAY_TOP,
                SKY_NIGHT_TOP,
                night
            ),
            lerp_color(
                SKY_DAY_BOTTOM,
                SKY_NIGHT_BOTTOM,
                night
            ),
            HEIGHT - 70
        )

        # Stars
        if night > 0.35:

            star_strength = (
                night - 0.35
            ) / 0.65

            for x, y, size in self.stars:

                brightness = int(
                    100 + 155 * star_strength
                )

                pygame.draw.circle(
                    SCREEN,
                    (
                        brightness,
                        brightness,
                        brightness
                    ),
                    (x, y),
                    size
                )

        # Sun / Moon
        phase = cycle * math.pi * 2

        sun_x = int(
            WIDTH / 2
            + math.cos(phase) * 400
        )

        sun_y = int(
            250
            + math.sin(phase) * 170
        )

        if night < 0.6:

            pygame.draw.circle(
                SCREEN,
                (255, 230, 100),
                (sun_x, sun_y),
                38
            )

        if night > 0.4:

            moon_x = int(
                WIDTH / 2
                - math.cos(phase) * 400
            )

            moon_y = int(
                250
                - math.sin(phase) * 170
            )

            pygame.draw.circle(
                SCREEN,
                (235, 240, 255),
                (moon_x, moon_y),
                32
            )

        # Clouds
        for cloud in self.clouds:
            cloud.draw(SCREEN, night)

    # ========================================================
    # GROUND
    # ========================================================

    def draw_ground(self):

        y = HEIGHT - 70

        pygame.draw.rect(
            SCREEN,
            GROUND,
            (0, y, WIDTH, 70)
        )

        pygame.draw.rect(
            SCREEN,
            GROUND_DARK,
            (0, y, WIDTH, 8)
        )

        # Moving ground pattern
        offset = int(self.ground_offset)

        for x in range(
            -40 + offset,
            WIDTH + 40,
            40
        ):

            pygame.draw.rect(
                SCREEN,
                GROUND_DARK,
                (
                    x,
                    y + 25,
                    20,
                    8
                )
            )

            pygame.draw.rect(
                SCREEN,
                GROUND_DARK,
                (
                    x + 20,
                    y + 42,
                    20,
                    8
                )
            )

    # ========================================================
    # HUD
    # ========================================================

    def draw_hud(self):

        # Score
        draw_text(
            SCREEN,
            str(self.score),
            FONT_HUGE,
            WHITE,
            (WIDTH // 2, 75)
        )

        # Lives
        for i in range(3):

            x = 50 + i * 48

            if i < self.lives:

                pygame.draw.circle(
                    SCREEN,
                    RED,
                    (x, 55),
                    15
                )

                pygame.draw.circle(
                    SCREEN,
                    WHITE,
                    (x - 5, 50),
                    4
                )

            else:

                pygame.draw.circle(
                    SCREEN,
                    (100, 100, 100),
                    (x, 55),
                    15
                )

        # High score
        draw_text(
            SCREEN,
            f"BEST {save_data['high_score']}",
            FONT_SMALL,
            WHITE,
            (WIDTH - 100, 50)
        )

        # Difficulty indicator
        if self.score >= 40:

            difficulty = "INSANE"

        elif self.score >= 25:

            difficulty = "HARD"

        elif self.score >= 10:

            difficulty = "FAST"

        else:

            difficulty = "NORMAL"

        draw_text(
            SCREEN,
            difficulty,
            FONT_SMALL,
            WHITE,
            (WIDTH - 70, 85)
        )

    # ========================================================
    # MEDAL
    # ========================================================

    def get_medal(self):

        if self.score >= 60:
            return "PLATINUM"

        if self.score >= 40:
            return "GOLD"

        if self.score >= 25:
            return "SILVER"

        if self.score >= 10:
            return "BRONZE"

        return "NONE"

    # ========================================================
    # MENU
    # ========================================================

    def draw_menu(self):

        self.draw_background()

        # Dark overlay
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 45)
        )

        SCREEN.blit(
            overlay,
            (0, 0)
        )

        draw_text(
            SCREEN,
            "FLAPPY",
            FONT_TITLE,
            BIRD_YELLOW,
            (WIDTH // 2, 125)
        )

        draw_text(
            SCREEN,
            "BIRD",
            FONT_TITLE,
            WHITE,
            (WIDTH // 2, 210)
        )

        # Small bird preview
        preview_bird = Bird()
        preview_bird.x = WIDTH // 2
        preview_bird.y = 290
        preview_bird.animation_time = self.world_time

        preview_bird.draw(SCREEN)

        self.start_button.draw(SCREEN)

        self.settings_button.draw(SCREEN)

        draw_text(
            SCREEN,
            f"BEST SCORE: {save_data['high_score']}",
            FONT_MEDIUM,
            GOLD,
            (WIDTH // 2, 625)
        )

        draw_text(
            SCREEN,
            "SPACE / CLICK = FLAP     P = PAUSE",
            FONT_SMALL,
            WHITE,
            (WIDTH // 2, 660)
        )

    # ========================================================
    # COUNTDOWN DRAW
    # ========================================================

    def draw_countdown(self):

        self.draw_game_scene()

        number = max(
            1,
            int(math.ceil(self.countdown))
        )

        draw_text(
            SCREEN,
            str(number),
            FONT_HUGE,
            WHITE,
            (WIDTH // 2, HEIGHT // 2)
        )

    # ========================================================
    # GAME SCENE
    # ========================================================

    def draw_game_scene(self):

        self.draw_background()

        for pipe in self.pipes:
            pipe.draw(SCREEN)

        self.bird.draw(SCREEN)

        self.particles.draw(SCREEN)

        self.draw_ground()

        self.draw_hud()

    # ========================================================
    # PAUSE
    # ========================================================

    def draw_pause(self):

        self.draw_game_scene()

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 150)
        )

        SCREEN.blit(
            overlay,
            (0, 0)
        )

        draw_text(
            SCREEN,
            "PAUSED",
            FONT_HUGE,
            WHITE,
            (WIDTH // 2, 260)
        )

        draw_text(
            SCREEN,
            "Press P to resume",
            FONT_MEDIUM,
            WHITE,
            (WIDTH // 2, 350)
        )

        draw_text(
            SCREEN,
            "ESC = Main Menu",
            FONT_SMALL,
            WHITE,
            (WIDTH // 2, 410)
        )

    # ========================================================
    # GAME OVER
    # ========================================================

    def draw_game_over(self):

        self.draw_game_scene()

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 165)
        )

        SCREEN.blit(
            overlay,
            (0, 0)
        )

        draw_text(
            SCREEN,
            "GAME OVER",
            FONT_HUGE,
            RED,
            (WIDTH // 2, 150)
        )

        draw_text(
            SCREEN,
            f"SCORE  {self.score}",
            FONT_LARGE,
            WHITE,
            (WIDTH // 2, 250)
        )

        draw_text(
            SCREEN,
            f"BEST  {save_data['high_score']}",
            FONT_MEDIUM,
            GOLD,
            (WIDTH // 2, 310)
        )

        medal = self.get_medal()

        if medal != "NONE":

            draw_text(
                SCREEN,
                medal,
                FONT_LARGE,
                GOLD,
                (WIDTH // 2, 370)
            )

        self.restart_button.draw(SCREEN)

        self.game_over_menu_button.draw(SCREEN)

        draw_text(
            SCREEN,
            "R = Restart",
            FONT_SMALL,
            WHITE,
            (WIDTH // 2, 615)
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def draw_settings(self):

        self.draw_background()

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 90)
        )

        SCREEN.blit(
            overlay,
            (0, 0)
        )

        draw_text(
            SCREEN,
            "SETTINGS",
            FONT_HUGE,
            WHITE,
            (WIDTH // 2, 140)
        )

        sound_state = (
            "SOUND: ON"
            if save_data["sound"]
            else "SOUND: OFF"
        )

        music_state = (
            "MUSIC: ON"
            if save_data["music"]
            else "MUSIC: OFF"
        )

        self.sound_button.text = sound_state
        self.music_button.text = music_state

        self.sound_button.draw(SCREEN)
        self.music_button.draw(SCREEN)

        self.settings_back_button.draw(SCREEN)

        draw_text(
            SCREEN,
            "Click an option to toggle it",
            FONT_SMALL,
            WHITE,
            (WIDTH // 2, 470)
        )

        draw_text(
            SCREEN,
            "Controls",
            FONT_MEDIUM,
            GOLD,
            (WIDTH // 2, 510)
        )

        draw_text(
            SCREEN,
            "SPACE / LEFT CLICK  →  FLAP",
            FONT_SMALL,
            WHITE,
            (WIDTH // 2, 545)
        )

    # ========================================================
    # MAIN DRAW
    # ========================================================

    def draw(self):

        if self.state == MENU:

            self.draw_menu()

        elif self.state == COUNTDOWN:

            self.draw_countdown()

        elif self.state == PLAYING:

            self.draw_game_scene()

        elif self.state == PAUSED:

            self.draw_pause()

        elif self.state == SETTINGS:

            self.draw_settings()

        elif self.state == GAME_OVER:

            self.draw_game_over()


# ============================================================
# GAME OBJECT
# ============================================================

game = Game()

# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = CLOCK.tick(FPS) / 1000.0

    dt = min(dt, 0.033)

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        # ====================================================
        # KEYBOARD
        # ====================================================

        if event.type == pygame.KEYDOWN:

            # Quit
            if event.key == pygame.K_ESCAPE:

                if game.state == MENU:

                    running = False

                elif game.state == SETTINGS:

                    game.state = MENU

                elif game.state in (
                    PLAYING,
                    PAUSED,
                    COUNTDOWN,
                    GAME_OVER
                ):

                    game.state = MENU

            # Flap
            if event.key in (
                pygame.K_SPACE,
                pygame.K_UP
            ):

                if game.state == PLAYING:

                    game.bird.flap()

                elif game.state == MENU:

                    game.reset_game()

                elif game.state == GAME_OVER:

                    game.reset_game()

            # Pause
            if event.key == pygame.K_p:

                if game.state == PLAYING:

                    game.state = PAUSED

                elif game.state == PAUSED:

                    game.state = PLAYING

            # Restart
            if event.key == pygame.K_r:

                if game.state == GAME_OVER:

                    game.reset_game()

        # ====================================================
        # MOUSE
        # ====================================================

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Menu
                if game.state == MENU:

                    if game.start_button.clicked(event):

                        play_sound("click")

                        game.reset_game()

                    elif game.settings_button.clicked(event):

                        play_sound("click")

                        game.state = SETTINGS

                # Playing
                elif game.state == PLAYING:

                    game.bird.flap()

                # Game over
                elif game.state == GAME_OVER:

                    if game.restart_button.clicked(event):

                        play_sound("click")

                        game.reset_game()

                    elif game.game_over_menu_button.clicked(event):

                        play_sound("click")

                        game.state = MENU

                # Settings
                elif game.state == SETTINGS:

                    if game.sound_button.clicked(event):

                        save_data["sound"] = not save_data["sound"]

                        save_game_data()

                        play_sound("click")

                    elif game.music_button.clicked(event):

                        save_data["music"] = not save_data["music"]

                        save_game_data()

                        update_music()

                        play_sound("click")

                    elif game.settings_back_button.clicked(event):

                        play_sound("click")

                        game.state = MENU

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    game.update(dt)

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    game.draw()

    pygame.display.flip()


# ============================================================
# EXIT
# ============================================================

save_game_data()

pygame.quit()