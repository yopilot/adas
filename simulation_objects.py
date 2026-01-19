import pygame
import math
import os
from simulation_config import *

# Global Asset Cache
IMAGE_CACHE = {}

class Entity:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = 0
        self.vy = 0 # Vertical velocity (relative)
        self.vx = 0 # Horizontal velocity
        self.image = None

    def load_image(self, path):
        global IMAGE_CACHE
        
        # Check cache first
        if path in IMAGE_CACHE:
            img = IMAGE_CACHE[path]
            self.image = pygame.transform.scale(img, (self.width, self.height))
            return

        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                IMAGE_CACHE[path] = img # Store original in cache
                self.image = pygame.transform.scale(img, (self.width, self.height))
        except Exception as e:
            print(f"Failed to load {path}: {e}")

    def update(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=4)


class PlayerCar(Entity):
    def __init__(self):
        # Start in middle lane
        middle_lane_idx = LANE_COUNT // 2
        start_x = ROAD_X_START + middle_lane_idx * LANE_WIDTH + (LANE_WIDTH - 50) // 2
        super().__init__(start_x, SCREEN_HEIGHT - 150, 50, 90, COLOR_PLAYER)
        self.load_image(ASSET_PLAYER_CAR)
        self.target_speed = BASE_SPEED
        self.drift_offset = 0.0
        
        # Sensor states (for visualization)
        self.sensor_acc_active = False
        self.sensor_aeb_active = False
        self.sensor_bsd_left = False
        self.sensor_bsd_right = False
        self.sensor_lca_active = False

    def update(self, keys_pressed, adas_flags, road_speed):
        # Manual Control Logic vs ADAS
        dt = 1.0 # simplistic time step
        
        # 1. Acceleration / Speed
        # Manual: W/S changes target speed
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            self.speed += ACCELERATION
        elif keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            self.speed -= ACCELERATION
        else:
            # Inertia
            self.speed = self.speed * 0.99
            
        self.speed = max(0, min(self.speed, MAX_SPEED))

        # 2. X Movement (Steering)
        move_x = 0
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            move_x = -1
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            move_x = 1
            
        # Physics: Stable control (Simulation style)
        self.vx += move_x * 0.5
        self.vx *= 0.85 # Higher damping for more "grip", less slide
        
        # Remove artificial drift as requested
        # if not adas_flags['LCA']: ...
            
        self.x += self.vx * STEER_SPEED * 0.5
        
        # Clamp to road boundaries
        min_x = ROAD_X_START
        max_x = ROAD_X_START + ROAD_WIDTH - self.width
        self.x = max(min_x, min(self.x, max_x))

        # Update Rect
        super().update()
        
    def draw(self, surface):
        # Draw Vision Cone (Sensors) - RADAR VISUALIZATION
        center_x = self.x + self.width // 2
        center_y = self.y
        
        if self.sensor_acc_active or self.sensor_aeb_active:
            # Radar Waves Visualization (Waves go out and come back)
            current_time = pygame.time.get_ticks()
            
            # Create a transparent surface for the waves
            radar_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # 1. Transmitter Waves (Outward)
            # Cyan/Green waves moving away
            base_color = (0, 255, 255) # Default Cyan
            if self.sensor_aeb_active: base_color = (255, 50, 50) # Red
            elif self.sensor_acc_active: base_color = (50, 255, 100) # Green
            
            # Draw expanding arcs
            num_waves = 4
            max_dist = 250  # Reduced from 400
            speed = 0.15    # Reduced from 0.4 for slower animation
            period = max_dist / speed 
            
            for i in range(num_waves):
                # Offset time for each wave
                t = (current_time + (i * period / num_waves)) % period
                dist = t * speed
                
                # Alpha fade (strong near car, weak far away)
                alpha = int(255 * (1 - dist / max_dist))
                color = (*base_color, alpha)
                
                # Draw arc
                rect = pygame.Rect(center_x - dist, center_y - dist, dist * 2, dist * 2)
                # Angles: North is pi/2. Reduced spread: +/- 0.3 radians
                start_angle = math.pi/2 - 0.3
                end_angle = math.pi/2 + 0.3
                pygame.draw.arc(radar_surf, color, rect, start_angle, end_angle, 3)

            # 2. Receiver Waves (Inward - "Return Signal")
            # Only if active detection
            if self.sensor_acc_active or self.sensor_aeb_active:
                return_color = (255, 255, 0) # Yellow return signal
                
                for i in range(num_waves):
                    t = (current_time + (i * period / num_waves)) % period
                    # Invert distance: Start at max, go to 0
                    dist = max_dist - (t * speed)
                    
                    # Brighten as it returns
                    alpha = int(255 * (1 - (dist/max_dist))) 
                    color = (*return_color, alpha)
                    
                    rect = pygame.Rect(center_x - dist, center_y - dist, dist * 2, dist * 2)
                    pygame.draw.arc(radar_surf, color, rect, start_angle, end_angle, 2)
            
            surface.blit(radar_surf, (0,0))

        # BSD Sensors
        if self.sensor_bsd_left:
             pygame.draw.arc(surface, COLOR_ACCENT_WARN, (self.x - 40, self.y, 40, 70), math.pi/2, 3*math.pi/2, 3)
        if self.sensor_bsd_right:
             pygame.draw.arc(surface, COLOR_ACCENT_WARN, (self.x + self.width, self.y, 40, 70), -math.pi/2, math.pi/2, 3)

        # Draw Car Body
        super().draw(surface)



class NpcCar(Entity):
    def __init__(self, x, y, speed, is_oncoming=False):
        color = (255, 50, 50) if is_oncoming else COLOR_NPC
        super().__init__(x, y, 50, 90, color)
        self.load_image(ASSET_NPC_CAR)
        self.lane_speed = speed 
        self.has_radar = False 
        self.is_oncoming = is_oncoming
        
        # If oncoming (Red hostile car), tint the image or ignore it
        if self.is_oncoming and self.image:
             # Create a red tinted version
             red_surf = pygame.Surface(self.image.get_size()).convert_alpha()
             red_surf.fill((255, 0, 0))
             self.image.blit(red_surf, (0,0), special_flags=pygame.BLEND_MULT)

    def update_relative(self, world_speed):
        rel_speed = self.lane_speed - world_speed
        self.y -= rel_speed * 1 
        self.rect.y = int(self.y)

    def draw(self, surface):
        # Optional Radar Interference Logic
        if self.has_radar:
            # Draw chaotic radar waves
            # If oncoming, waves usually come from front, but for chaos we keep omni or direct
            center_x = self.x + self.width // 2
            center_y = self.y + (0 if self.is_oncoming else self.height)
            
            # Interference is chaotic, so random offsets
            current_time = pygame.time.get_ticks()
            num_waves = 3
            max_dist = 220
            speed = 0.2
            period = max_dist / speed 

            radar_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # Red/Purple chaotic waves
            base_color = (255, 0, 0) if self.is_oncoming else (255, 0, 255)
            
            for i in range(num_waves):
                t = (current_time + (i * period / num_waves)) % period
                dist = t * speed
                alpha = int(200 * (1 - dist / max_dist))
                color = (*base_color, alpha)
                
                rect = pygame.Rect(center_x - dist, center_y - dist, dist * 2, dist * 2)
                
                # If oncoming, they shoot DOWN towards player. Else UP/Omni.
                # Chaotic = Circle
                pygame.draw.circle(radar_surf, color, (center_x, center_y), int(dist), 3)
                
            surface.blit(radar_surf, (0,0))
            
        # Draw body (flipped if oncoming)
        if self.image:
             if self.is_oncoming:
                 # Rotate 180
                 rot_img = pygame.transform.rotate(self.image, 180)
                 surface.blit(rot_img, self.rect)
             else:
                 surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=4)

class Obstacle(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, COLOR_OBSTACLE)
        self.load_image(ASSET_OBSTACLE)
        
    def draw(self, surface):
        if self.image:
             surface.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x + self.width/2), int(self.y + self.height/2)), 20)
            # Warning stripes
            pygame.draw.line(surface, (0,0,0), (self.x+10, self.y+10), (self.x+30, self.y+30), 3)
            pygame.draw.line(surface, (0,0,0), (self.x+10, self.y+10), (self.x+30, self.y+30), 3)
        pygame.draw.line(surface, (0,0,0), (self.x+30, self.y+10), (self.x+10, self.y+30), 3)

    def update_relative(self, world_speed):
        # Static object, so it moves down at world_speed
        # (It has 0 speed itself)
        self.y += world_speed * 1
        self.rect.y = int(self.y)
