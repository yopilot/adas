import pygame

# --- Colors (Cyberpunk / Automotive) ---
COLOR_BG = (20, 24, 28)        # Dark Slate Grey
COLOR_ROAD = (50, 50, 50)      # Standard Grey Asphalt
COLOR_LANE_MARKER = (255, 255, 255) # White Strips
COLOR_LANE_MARKER_ACTIVE = (50, 255, 200) # Neon Cyan
COLOR_PLAYER = (255, 255, 255) # Clean White
COLOR_NPC = (100, 120, 140)    # Muted Blue-Grey
COLOR_OBSTACLE = (255, 50, 50) # Danger Red
COLOR_TEXT = (200, 200, 200)
COLOR_ACCENT_GOOD = (50, 255, 100) # Neon Green
COLOR_ACCENT_WARN = (255, 200, 50) # Amber
COLOR_ACCENT_BAD = (255, 50, 50)   # Red

# --- Dimensions ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
LANE_WIDTH = 80
ROAD_WIDTH = LANE_WIDTH * 3
ROAD_X_START = (SCREEN_WIDTH - ROAD_WIDTH) // 2

# --- Physics / Gameplay ---
FPS = 60
BASE_SPEED = 5.0
MAX_SPEED = 10.0
ACCELERATION = 0.1
FRICTION = 0.05
STEER_SPEED = 4.0
LANE_SNAP_SPEED = 2.0

# --- Assets ---
LOGO_PATH_PNG = "aptiv_logo.png"
ASSET_PLAYER_CAR = "car.png"
ASSET_NPC_CAR = "car2.png"
ASSET_OBSTACLE = "pit.png"
