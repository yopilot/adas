"""
ADAS Simulation Game - Aptiv Showcase Mode
===========================================
A professional 2D driving simulator demonstrating Advanced Driver Assistance Systems.

Author: Senior Simulation Engineer
Company: Aptiv
Date: January 12, 2026

Features:
- Adaptive Cruise Control (ACC)
- Lane Keep Assist (LKA)
- Automatic Emergency Braking (AEB)
- Blind Spot Detection (BSD)
- Evasive Steer Assist (ESA)
"""

import pygame
import random
import math
import os
import sys

# Initialize Pygame
pygame.init()

# ========== CONSTANTS & CONFIGURATION ==========
# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
ROAD_WIDTH = 600
DASHBOARD_WIDTH = SCREEN_WIDTH - ROAD_WIDTH

# Colors - Cyberpunk/Automotive Dashboard Theme
COLOR_BG = (15, 15, 25)  # Dark background
COLOR_ROAD = (25, 25, 35)  # Dark road
COLOR_LANE_LINE = (50, 50, 70)  # Lane markings
COLOR_NEON_GREEN = (0, 255, 150)  # Active ADAS
COLOR_NEON_BLUE = (0, 200, 255)  # UI elements
COLOR_NEON_RED = (255, 50, 80)  # Warnings/danger
COLOR_NEON_YELLOW = (255, 220, 0)  # Caution
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (100, 100, 120)
COLOR_DARK_GRAY = (40, 40, 50)

# Game physics
FPS = 60
GRAVITY = 0.5

# Player car physics
PLAYER_MAX_SPEED = 8.0
PLAYER_ACCELERATION = 0.3
PLAYER_DECELERATION = 0.15
PLAYER_TURN_SPEED = 0.12  # Lateral movement
PLAYER_DRIFT_FACTOR = 0.88  # Lower = more drift (makes it slippery)
ADAS_DRIFT_FACTOR = 0.75  # Tighter control when ADAS is active

# Lane configuration
NUM_LANES = 3
LANE_WIDTH = ROAD_WIDTH / NUM_LANES
LANE_CENTERS = [LANE_WIDTH * i + LANE_WIDTH / 2 for i in range(NUM_LANES)]

# NPC car configuration
NPC_SPAWN_RATE = 0.015  # Probability per frame
NPC_MIN_SPEED = 2.0
NPC_MAX_SPEED = 6.0

# Obstacle configuration
OBSTACLE_SPAWN_RATE = 0.003  # Pedestrians/obstacles

# ADAS sensor ranges
ACC_DETECTION_RANGE = 250  # Adaptive Cruise Control forward detection
AEB_DETECTION_RANGE = 150  # Emergency braking range
AEB_CRITICAL_RANGE = 80   # Critical emergency range
BSD_DETECTION_RANGE = 100  # Blind spot detection range
ESA_DETECTION_RANGE = 100  # Evasive steer assist range


# ========== CLASSES ==========

class Car:
    """
    Player's vehicle with realistic drift physics.
    Manual mode: More drift, harder to control (simulates human error).
    ADAS mode: Tighter control, computer-assisted.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 70
        self.speed = 0
        self.velocity_x = 0  # Lateral velocity for drift
        self.velocity_y = 0  # Forward velocity
        self.target_lane = 1  # Middle lane (0, 1, or 2)
        self.drift_accumulation = 0  # Random drift for manual mode
        
        # ADAS states
        self.adas = {
            'ACC': False,  # Adaptive Cruise Control
            'LKA': False,  # Lane Keep Assist
            'AEB': False,  # Automatic Emergency Braking
            'BSD': False,  # Blind Spot Detection
            'ESA': False   # Evasive Steer Assist
        }
        
        # ACC state
        self.acc_target_speed = PLAYER_MAX_SPEED
        self.acc_active = False
        
        # AEB state
        self.aeb_braking = False
        self.aeb_brake_timer = 0
        
        # ESA state
        self.esa_evading = False
        self.esa_timer = 0
        self.esa_direction = 0
        
        # Collision state
        self.crashed = False
        self.crash_timer = 0
        
    def update(self, keys, npc_cars, obstacles, road_scroll):
        """
        Update car physics and position.
        Implements drift and inertia for realistic feel.
        """
        if self.crashed:
            self.crash_timer -= 1
            if self.crash_timer <= 0:
                self.crashed = False
                self.speed = 0
                self.velocity_x = 0
                self.velocity_y = 0
            return
        
        # Determine drift factor based on ADAS
        drift_factor = ADAS_DRIFT_FACTOR if any(self.adas.values()) else PLAYER_DRIFT_FACTOR
        
        # === ADAPTIVE CRUISE CONTROL (ACC) ===
        if self.adas['ACC']:
            self._handle_acc(npc_cars, road_scroll)
        
        # === AUTOMATIC EMERGENCY BRAKING (AEB) ===
        if self.adas['AEB']:
            self._handle_aeb(npc_cars, obstacles, road_scroll)
        
        # === EVASIVE STEER ASSIST (ESA) ===
        if self.adas['ESA']:
            self._handle_esa(npc_cars, obstacles, road_scroll)
        
        # Manual controls (unless AEB is braking or ESA is evading)
        if not self.aeb_braking and not self.esa_evading:
            # Forward/Backward
            if keys[pygame.K_w]:
                self.velocity_y += PLAYER_ACCELERATION
            if keys[pygame.K_s]:
                self.velocity_y -= PLAYER_ACCELERATION * 0.8
            
            # Apply deceleration
            if not keys[pygame.K_w] and not keys[pygame.K_s]:
                self.velocity_y *= 0.97
            
            # Clamp speed
            self.velocity_y = max(-PLAYER_MAX_SPEED * 0.5, min(PLAYER_MAX_SPEED, self.velocity_y))
            
            # Lateral movement (with blind spot detection)
            lateral_input = 0
            if keys[pygame.K_a]:
                lateral_input = -1
            if keys[pygame.K_d]:
                lateral_input = 1
            
            # === BLIND SPOT DETECTION (BSD) ===
            if lateral_input != 0 and self.adas['BSD']:
                if self._check_blind_spot(lateral_input, npc_cars, road_scroll):
                    lateral_input = 0  # Block the movement
            
            self.velocity_x += lateral_input * PLAYER_TURN_SPEED
        
        # === LANE KEEP ASSIST (LKA) ===
        if not self.adas['LKA']:
            # Manual mode: Add random drift (simulating distraction)
            self.drift_accumulation += random.uniform(-0.02, 0.02)
            self.drift_accumulation *= 0.95  # Decay
            self.velocity_x += self.drift_accumulation
        else:
            # LKA: Auto-correct if touching lane lines
            self._handle_lka()
        
        # Apply drift/friction to lateral movement
        self.velocity_x *= drift_factor
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Keep car on road
        self.x = max(10, min(ROAD_WIDTH - self.width - 10, self.x))
        
        # Keep car in visible area vertically
        self.y = max(50, min(SCREEN_HEIGHT - self.height - 50, self.y))
        
        # Update speed for display
        self.speed = abs(self.velocity_y)
        
    def _handle_acc(self, npc_cars, road_scroll):
        """
        Adaptive Cruise Control:
        Automatically maintains safe distance from car ahead.
        Slows down when approaching, speeds up when clear.
        """
        self.acc_active = False
        min_distance = ACC_DETECTION_RANGE
        car_ahead = None
        
        # Find closest car in front in the same lane
        current_lane = self._get_current_lane()
        for npc in npc_cars:
            npc_lane = int(npc.x / LANE_WIDTH)
            npc_y = npc.y - road_scroll
            
            # Check if in same lane and ahead
            if npc_lane == current_lane and npc_y < self.y:
                distance = self.y - npc_y
                if distance < min_distance:
                    min_distance = distance
                    car_ahead = npc
        
        if car_ahead:
            self.acc_active = True
            # Calculate safe following distance based on speed
            safe_distance = 100 + self.velocity_y * 10
            
            if min_distance < safe_distance:
                # Too close - slow down
                target_speed = car_ahead.speed * 0.9
                self.velocity_y = max(target_speed, self.velocity_y - 0.2)
            else:
                # Good distance - match speed
                self.velocity_y = min(PLAYER_MAX_SPEED, car_ahead.speed * 1.1)
        else:
            # No car ahead - maintain cruise speed
            if self.velocity_y < PLAYER_MAX_SPEED * 0.8:
                self.velocity_y += 0.1
    
    def _handle_aeb(self, npc_cars, obstacles, road_scroll):
        """
        Automatic Emergency Braking:
        Detects imminent collision and applies emergency braking.
        """
        if self.aeb_brake_timer > 0:
            self.aeb_brake_timer -= 1
            self.aeb_braking = True
            self.velocity_y *= 0.8  # Hard braking
            if self.aeb_brake_timer == 0:
                self.aeb_braking = False
            return
        
        self.aeb_braking = False
        current_lane = self._get_current_lane()
        
        # Check for obstacles (pedestrians)
        for obs in obstacles:
            obs_y = obs.y - road_scroll
            obs_lane = int(obs.x / LANE_WIDTH)
            
            if obs_lane == current_lane:
                distance = obs_y - self.y
                if 0 < distance < AEB_CRITICAL_RANGE:
                    # EMERGENCY BRAKING!
                    self.aeb_braking = True
                    self.aeb_brake_timer = 30
                    self.velocity_y *= 0.5
                    return
        
        # Check for stopped/slow NPC cars
        for npc in npc_cars:
            npc_lane = int(npc.x / LANE_WIDTH)
            npc_y = npc.y - road_scroll
            
            if npc_lane == current_lane and npc_y < self.y:
                distance = self.y - npc_y
                collision_time = distance / max(self.velocity_y - npc.speed, 0.1)
                
                if collision_time < 1.5 and distance < AEB_DETECTION_RANGE:
                    # Collision imminent!
                    self.aeb_braking = True
                    self.aeb_brake_timer = 20
                    self.velocity_y *= 0.6
                    return
    
    def _handle_lka(self):
        """
        Lane Keep Assist:
        Automatically steers car back to lane center if drifting.
        """
        current_lane = self._get_current_lane()
        lane_center = LANE_CENTERS[current_lane]
        car_center = self.x + self.width / 2
        
        # Calculate distance from lane center
        offset = car_center - lane_center
        
        # If drifting too far, apply corrective steering
        if abs(offset) > LANE_WIDTH * 0.3:
            correction = -offset * 0.05  # Proportional control
            self.velocity_x += correction
    
    def _check_blind_spot(self, direction, npc_cars, road_scroll):
        """
        Blind Spot Detection:
        Checks if there's a car in the blind spot before lane change.
        Returns True if blind spot is occupied (blocks movement).
        """
        for npc in npc_cars:
            npc_y = npc.y - road_scroll
            
            # Check vertical overlap (car is beside us)
            if abs(npc_y - self.y) < 80:
                # Check horizontal proximity
                if direction < 0:  # Moving left
                    if self.x - npc.x - npc.width < 60 and self.x - npc.x > -20:
                        return True  # Blocked!
                else:  # Moving right
                    if npc.x - self.x - self.width < 60 and npc.x - self.x > -20:
                        return True  # Blocked!
        return False
    
    def _handle_esa(self, npc_cars, obstacles, road_scroll):
        """
        Evasive Steer Assist:
        When collision is unavoidable by braking alone, performs
        emergency swerve maneuver to avoid obstacle.
        """
        if self.esa_evading:
            self.esa_timer -= 1
            # Execute the evasive maneuver
            self.velocity_x = self.esa_direction * 3.0 * (self.esa_timer / 30.0)
            if self.esa_timer <= 0:
                self.esa_evading = False
            return
        
        current_lane = self._get_current_lane()
        
        # Check for critical obstacles
        for obs in obstacles:
            obs_y = obs.y - road_scroll
            obs_lane = int(obs.x / LANE_WIDTH)
            
            if obs_lane == current_lane:
                distance = obs_y - self.y
                if 0 < distance < ESA_DETECTION_RANGE and self.velocity_y > 3:
                    # Too close for braking alone - EVADE!
                    self._execute_evasive_maneuver(current_lane)
                    return
        
        # Check for imminent NPC collision
        for npc in npc_cars:
            npc_lane = int(npc.x / LANE_WIDTH)
            npc_y = npc.y - road_scroll
            
            if npc_lane == current_lane and npc_y < self.y:
                distance = self.y - npc_y
                if distance < 60 and self.velocity_y > npc.speed + 2:
                    # About to rear-end - EVADE!
                    self._execute_evasive_maneuver(current_lane)
                    return
    
    def _execute_evasive_maneuver(self, current_lane):
        """Execute the evasive swerve."""
        # Determine swerve direction (prefer right, unless in rightmost lane)
        if current_lane < NUM_LANES - 1:
            self.esa_direction = 1  # Swerve right
        elif current_lane > 0:
            self.esa_direction = -1  # Swerve left
        else:
            return  # Nowhere to swerve
        
        self.esa_evading = True
        self.esa_timer = 30
        self.velocity_y *= 0.9  # Slow down a bit during maneuver
    
    def _get_current_lane(self):
        """Determine which lane the car is currently in."""
        car_center = self.x + self.width / 2
        return max(0, min(NUM_LANES - 1, int(car_center / LANE_WIDTH)))
    
    def trigger_crash(self):
        """Handle collision event."""
        self.crashed = True
        self.crash_timer = 60
        self.velocity_x = 0
        self.velocity_y = 0
    
    def draw(self, screen):
        """Draw the player's car."""
        if self.crashed:
            # Flash red when crashed
            color = COLOR_NEON_RED if (self.crash_timer // 5) % 2 == 0 else COLOR_WHITE
        else:
            color = COLOR_NEON_BLUE
        
        # Car body
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height), 0, 5)
        pygame.draw.rect(screen, COLOR_WHITE, (self.x, self.y, self.width, self.height), 2, 5)
        
        # Windshield
        pygame.draw.rect(screen, COLOR_BG, (self.x + 5, self.y + 10, self.width - 10, 20))
        
        # Headlights
        pygame.draw.circle(screen, COLOR_NEON_YELLOW, (int(self.x + 10), int(self.y + 5)), 4)
        pygame.draw.circle(screen, COLOR_NEON_YELLOW, (int(self.x + self.width - 10), int(self.y + 5)), 4)
        
        # Draw active ADAS sensors
        if self.adas['ACC'] and self.acc_active:
            # ACC sensor cone
            points = [
                (self.x + self.width // 2, self.y),
                (self.x - 30, self.y - ACC_DETECTION_RANGE),
                (self.x + self.width + 30, self.y - ACC_DETECTION_RANGE)
            ]
            pygame.draw.polygon(screen, (*COLOR_NEON_GREEN, 30), points)
        
        if self.adas['AEB'] and self.aeb_braking:
            # AEB warning indicator
            pygame.draw.circle(screen, (*COLOR_NEON_RED, 100), 
                             (int(self.x + self.width // 2), int(self.y - 40)), 30)
            pygame.draw.circle(screen, COLOR_NEON_RED, 
                             (int(self.x + self.width // 2), int(self.y - 40)), 30, 3)


class NPCCar:
    """Non-player car moving on the highway."""
    def __init__(self, lane, y_offset):
        self.lane = lane
        self.x = LANE_CENTERS[lane] - 20
        self.y = y_offset
        self.width = 40
        self.height = 60
        self.speed = random.uniform(NPC_MIN_SPEED, NPC_MAX_SPEED)
        self.color = random.choice([COLOR_GRAY, COLOR_DARK_GRAY, (80, 80, 100)])
    
    def update(self):
        """Move the NPC car forward."""
        self.y += self.speed
    
    def draw(self, screen, road_scroll):
        """Draw the NPC car."""
        draw_y = self.y - road_scroll
        if -100 < draw_y < SCREEN_HEIGHT + 100:
            pygame.draw.rect(screen, self.color, 
                           (self.x, draw_y, self.width, self.height), 0, 4)
            pygame.draw.rect(screen, COLOR_WHITE, 
                           (self.x, draw_y, self.width, self.height), 1, 4)
            # Rear lights
            pygame.draw.circle(screen, COLOR_NEON_RED, 
                             (int(self.x + 8), int(draw_y + self.height - 5)), 3)
            pygame.draw.circle(screen, COLOR_NEON_RED, 
                             (int(self.x + self.width - 8), int(draw_y + self.height - 5)), 3)


class Obstacle:
    """Pedestrian or stopped obstacle on the road."""
    def __init__(self, lane, y_offset):
        self.lane = lane
        self.x = LANE_CENTERS[lane]
        self.y = y_offset
        self.radius = 15
        self.type = random.choice(['pedestrian', 'cone'])
    
    def draw(self, screen, road_scroll):
        """Draw the obstacle."""
        draw_y = self.y - road_scroll
        if -100 < draw_y < SCREEN_HEIGHT + 100:
            if self.type == 'pedestrian':
                # Pedestrian (red circle)
                pygame.draw.circle(screen, COLOR_NEON_RED, 
                                 (int(self.x), int(draw_y)), self.radius)
                pygame.draw.circle(screen, COLOR_WHITE, 
                                 (int(self.x), int(draw_y)), self.radius, 2)
            else:
                # Traffic cone (yellow triangle)
                points = [
                    (self.x, draw_y - 20),
                    (self.x - 15, draw_y + 10),
                    (self.x + 15, draw_y + 10)
                ]
                pygame.draw.polygon(screen, COLOR_NEON_YELLOW, points)
                pygame.draw.polygon(screen, COLOR_WHITE, points, 2)


class Dashboard:
    """UI Dashboard for ADAS controls and information."""
    def __init__(self):
        self.x = ROAD_WIDTH
        self.y = 0
        self.width = DASHBOARD_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Logo
        self.logo = None
        self.load_logo()
        
        # Button positions
        self.buttons = {}
        button_names = ['ACC', 'LKA', 'AEB', 'BSD', 'ESA']
        for i, name in enumerate(button_names):
            self.buttons[name] = {
                'rect': pygame.Rect(self.x + 30, 200 + i * 90, self.width - 60, 70),
                'name': name,
                'full_name': self._get_full_name(name)
            }
    
    def load_logo(self):
        """Attempt to load Aptiv logo."""
        logo_path = os.path.join(os.path.dirname(__file__), 'aptiv_logo.png')
        if os.path.exists(logo_path):
            try:
                self.logo = pygame.image.load(logo_path)
                self.logo = pygame.transform.scale(self.logo, (200, 80))
            except:
                self.logo = None
    
    def _get_full_name(self, abbr):
        """Get full feature name."""
        names = {
            'ACC': 'Adaptive Cruise\nControl',
            'LKA': 'Lane Keep\nAssist',
            'AEB': 'Automatic Emergency\nBraking',
            'BSD': 'Blind Spot\nDetection',
            'ESA': 'Evasive Steer\nAssist'
        }
        return names.get(abbr, abbr)
    
    def draw(self, screen, car, score):
        """Draw the dashboard."""
        # Background
        pygame.draw.rect(screen, COLOR_DARK_GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.line(screen, COLOR_NEON_BLUE, (self.x, 0), (self.x, SCREEN_HEIGHT), 3)
        
        # Logo or title
        if self.logo:
            screen.blit(self.logo, (self.x + 20, 20))
        else:
            # Text placeholder
            font_title = pygame.font.Font(None, 48)
            title = font_title.render('APTIV', True, COLOR_NEON_BLUE)
            screen.blit(title, (self.x + 50, 30))
            font_sub = pygame.font.Font(None, 24)
            subtitle = font_sub.render('ADAS Showcase', True, COLOR_WHITE)
            screen.blit(subtitle, (self.x + 50, 75))
        
        # Title
        font_header = pygame.font.Font(None, 32)
        header = font_header.render('ADAS CONTROLS', True, COLOR_NEON_GREEN)
        screen.blit(header, (self.x + 30, 140))
        
        # ADAS feature buttons
        font_button = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 20)
        
        for key, button in self.buttons.items():
            rect = button['rect']
            is_active = car.adas[key]
            
            # Button background
            color = COLOR_NEON_GREEN if is_active else COLOR_GRAY
            pygame.draw.rect(screen, color, rect, 0, 10)
            pygame.draw.rect(screen, COLOR_WHITE, rect, 2, 10)
            
            # Button text
            text_color = COLOR_BG if is_active else COLOR_WHITE
            abbr_text = font_button.render(key, True, text_color)
            screen.blit(abbr_text, (rect.x + 15, rect.y + 12))
            
            # Full name (multiline)
            lines = button['full_name'].split('\n')
            for i, line in enumerate(lines):
                line_text = font_small.render(line, True, text_color)
                screen.blit(line_text, (rect.x + 15, rect.y + 40 + i * 18))
            
            # Status indicator
            status = "ON" if is_active else "OFF"
            status_text = font_button.render(status, True, text_color)
            screen.blit(status_text, (rect.x + rect.width - 60, rect.y + 22))
        
        # Stats
        font_stats = pygame.font.Font(None, 28)
        stats_y = 650
        
        # Speed
        speed_text = font_stats.render(f'Speed: {int(car.speed * 10)} km/h', True, COLOR_WHITE)
        screen.blit(speed_text, (self.x + 30, stats_y))
        
        # Score
        score_text = font_stats.render(f'Distance: {score} m', True, COLOR_NEON_BLUE)
        screen.blit(score_text, (self.x + 30, stats_y + 35))
        
        # Instructions
        font_help = pygame.font.Font(None, 18)
        help_y = SCREEN_HEIGHT - 80
        help_texts = [
            'WASD: Drive',
            'Click buttons: Toggle ADAS',
            'ESC: Quit'
        ]
        for i, text in enumerate(help_texts):
            help_render = font_help.render(text, True, COLOR_GRAY)
            screen.blit(help_render, (self.x + 30, help_y + i * 22))
    
    def handle_click(self, pos, car):
        """Handle mouse click on buttons."""
        for key, button in self.buttons.items():
            if button['rect'].collidepoint(pos):
                car.adas[key] = not car.adas[key]
                return True
        return False


# ========== GAME FUNCTIONS ==========

def draw_road(screen, road_scroll):
    """Draw the scrolling highway with lanes."""
    # Road background
    pygame.draw.rect(screen, COLOR_ROAD, (0, 0, ROAD_WIDTH, SCREEN_HEIGHT))
    
    # Road borders
    pygame.draw.line(screen, COLOR_NEON_YELLOW, (0, 0), (0, SCREEN_HEIGHT), 5)
    pygame.draw.line(screen, COLOR_NEON_YELLOW, (ROAD_WIDTH, 0), (ROAD_WIDTH, SCREEN_HEIGHT), 5)
    
    # Lane markings (dashed lines)
    dash_length = 40
    dash_gap = 40
    
    for lane in range(1, NUM_LANES):
        x = lane * LANE_WIDTH
        y_offset = int(road_scroll) % (dash_length + dash_gap)
        y = -y_offset
        
        while y < SCREEN_HEIGHT:
            pygame.draw.line(screen, COLOR_LANE_LINE, (x, y), (x, y + dash_length), 3)
            y += dash_length + dash_gap


def check_collision(car, npc_cars, obstacles, road_scroll):
    """
    Check for collisions between player and NPCs/obstacles.
    Returns True if collision detected.
    """
    car_rect = pygame.Rect(car.x, car.y, car.width, car.height)
    
    # Check NPC cars
    for npc in npc_cars:
        npc_y = npc.y - road_scroll
        npc_rect = pygame.Rect(npc.x, npc_y, npc.width, npc.height)
        if car_rect.colliderect(npc_rect):
            return True
    
    # Check obstacles
    for obs in obstacles:
        obs_y = obs.y - road_scroll
        # Circle collision
        car_center = (car.x + car.width // 2, car.y + car.height // 2)
        obs_center = (obs.x, obs_y)
        distance = math.sqrt((car_center[0] - obs_center[0])**2 + 
                           (car_center[1] - obs_center[1])**2)
        if distance < obs.radius + 25:
            return True
    
    return False


def main():
    """Main game loop."""
    # Setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Aptiv ADAS Simulation - Showcase Mode')
    clock = pygame.time.Clock()
    
    # Game objects
    player = Car(ROAD_WIDTH // 2 - 20, SCREEN_HEIGHT - 150)
    npc_cars = []
    obstacles = []
    dashboard = Dashboard()
    
    # Game state
    road_scroll = 0
    score = 0
    running = True
    
    print("=" * 60)
    print("APTIV ADAS SIMULATION - SHOWCASE MODE")
    print("=" * 60)
    print("\nControls:")
    print("  W/A/S/D - Drive the car")
    print("  Mouse Click - Toggle ADAS features on/off")
    print("  ESC - Quit")
    print("\nExperience the difference between manual driving")
    print("and ADAS-assisted driving!")
    print("=" * 60)
    
    # Main game loop
    while running:
        clock.tick(FPS)
        
        # Event handling
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    dashboard.handle_click(event.pos, player)
        
        # Update road scroll (creates movement illusion)
        if not player.crashed:
            road_scroll += player.velocity_y
            score = int(road_scroll / 10)
        
        # Spawn NPC cars
        if random.random() < NPC_SPAWN_RATE:
            lane = random.randint(0, NUM_LANES - 1)
            npc_cars.append(NPCCar(lane, road_scroll - 100))
        
        # Spawn obstacles
        if random.random() < OBSTACLE_SPAWN_RATE:
            lane = random.randint(0, NUM_LANES - 1)
            obstacles.append(Obstacle(lane, road_scroll - 100))
        
        # Update game objects
        player.update(keys, npc_cars, obstacles, road_scroll)
        
        for npc in npc_cars:
            npc.update()
        
        # Remove off-screen objects
        npc_cars = [npc for npc in npc_cars if npc.y - road_scroll < SCREEN_HEIGHT + 200]
        obstacles = [obs for obs in obstacles if obs.y - road_scroll < SCREEN_HEIGHT + 200]
        
        # Collision detection (only if not already crashed)
        if not player.crashed:
            if check_collision(player, npc_cars, obstacles, road_scroll):
                player.trigger_crash()
                print(f"CRASH! Distance traveled: {score} meters")
        
        # Drawing
        screen.fill(COLOR_BG)
        draw_road(screen, road_scroll)
        
        # Draw game objects
        for npc in npc_cars:
            npc.draw(screen, road_scroll)
        
        for obs in obstacles:
            obs.draw(screen, road_scroll)
        
        player.draw(screen)
        
        # Draw dashboard
        dashboard.draw(screen, player, score)
        
        # Draw warnings
        if player.adas['BSD']:
            # Check for blind spot warnings
            for npc in npc_cars:
                npc_y = npc.y - road_scroll
                if abs(npc_y - player.y) < 80:
                    # Left blind spot
                    if player.x - npc.x - npc.width < 60 and player.x - npc.x > -20:
                        draw_blind_spot_warning(screen, 'LEFT')
                    # Right blind spot
                    if npc.x - player.x - player.width < 60 and npc.x - player.x > -20:
                        draw_blind_spot_warning(screen, 'RIGHT')
        
        pygame.display.flip()
    
    pygame.quit()
    print("\nThanks for trying the Aptiv ADAS Simulation!")
    sys.exit()


def draw_blind_spot_warning(screen, side):
    """Draw blind spot warning indicators."""
    font = pygame.font.Font(None, 36)
    text = font.render('!', True, COLOR_NEON_RED)
    
    if side == 'LEFT':
        x = 20
    else:
        x = ROAD_WIDTH - 50
    
    y = SCREEN_HEIGHT // 2
    
    # Flashing warning
    if pygame.time.get_ticks() % 500 < 250:
        pygame.draw.circle(screen, COLOR_NEON_RED, (x + 15, y), 25)
        screen.blit(text, (x + 5, y - 15))


# ========== ENTRY POINT ==========
if __name__ == '__main__':
    main()
