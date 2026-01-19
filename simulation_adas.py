import pygame
import math
from simulation_config import *

class ADAS_System:
    def __init__(self, player):
        self.player = player
        self.flags = {
            'ACC': False,
            'LKA': False,
            'AEB': False,
            'BSD': False,
            'ESA': False
        }
        
    def update(self, npcs, obstacles, keys):
        # Reset sensor visuals
        self.player.sensor_acc_active = False
        self.player.sensor_aeb_active = False
        self.player.sensor_bsd_left = False
        self.player.sensor_bsd_right = False
        self.player.sensor_lka_active = False
        
        # 1. ACC (Adaptive Cruise Control)
        # Scan for car in front
        closest_dist = 9999
        closest_car = None
        
        lane_center_x = self.get_lane_center()
        
        # Look ahead in current lane
        for car in npcs:
            if abs(car.x - self.player.x) < LANE_WIDTH / 2: # Very rough "same lane" check
                if car.y < self.player.y: # Ahead
                    dist = self.player.y - (car.y + car.height)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_car = car

        if self.flags['ACC']:
            self.player.sensor_acc_active = True
            if closest_car and closest_dist < 200: # Detection range
                target = closest_car.lane_speed
                # Smoothly match speed
                if self.player.speed > target:
                    self.player.speed -= 0.1 # Brake
                else: 
                     self.player.speed += 0.05 # Accelerate slowly
            else:
                 # Resume cruise speed
                 if self.player.speed < MAX_SPEED * 0.8:
                     self.player.speed += 0.02
        
        # 2. AEB (Automatic Emergency Braking)
        # Check obstacles AND NPCs strictly ahead
        if self.flags['AEB']:
            # Check Obstacles
            for obs in obstacles:
                # Box collision prediction
                if (abs(obs.x - self.player.x) < 40) and (obs.y < self.player.y) and (obs.y > self.player.y - 150):
                     # IMPACT IMMINENT
                     self.player.sensor_aeb_active = True
                     self.player.speed = 0 # FULL STOP
            
            # Check NPCs
            for car in npcs:
                if (abs(car.x - self.player.x) < 40) and (car.y < self.player.y) and (car.y > self.player.y - 150):
                     # IMPACT IMMINENT WITH CAR
                     self.player.sensor_aeb_active = True
                     self.player.speed = 0 # FULL STOP
                     
        # 3. LKA (Lane Keep Assist)
        # Calculate offset from center of nearest lane
        current_lane_idx = int((self.player.x - ROAD_X_START) / LANE_WIDTH)
        current_lane_center = ROAD_X_START + (current_lane_idx * LANE_WIDTH) + (LANE_WIDTH - 40)//2
        
        dist_from_center = self.player.x - current_lane_center
        
        if self.flags['LKA']:
            if abs(dist_from_center) > 10: # Threshold
                self.player.sensor_lka_active = True
                # Steer back
                correction = -0.1 * dist_from_center
                self.player.vx += correction * 0.1
                
        # 4. BSD (Blind Spot Detection)
        # Check cars in adjacent lanes nearby
        left_clear = True
        right_clear = True
        
        for car in npcs:
            # Check Y overlap
            if abs(car.y - self.player.y) < 100:
                # Check X relative
                if car.x < self.player.x - 20: # Left side
                     self.player.sensor_bsd_left = True
                     left_clear = False
                elif car.x > self.player.x + 20: # Right side
                     self.player.sensor_bsd_right = True
                     right_clear = False
                     
        if self.flags['BSD']:
             # Override input if blocked
             input_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
             input_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

             if input_left and not left_clear:
                 self.player.vx = max(0, self.player.vx) # Cancel left movement
             if input_right and not right_clear:
                 self.player.vx = min(0, self.player.vx) # Cancel right movement

        # 5. ESA (Evasive Steer Assist)
        # If AEB fails (too close) or toggled, swerve
        if self.flags['ESA']:
            curr_lane = int((self.player.x - ROAD_X_START) / LANE_WIDTH)
            
            for obs in obstacles:
                 dist = self.player.y - (obs.y + obs.height)
                 if dist < 80 and dist > 0 and abs(obs.x - self.player.x) < 40:
                      # Too close to brake? SWERVE
                      
                      # Edge Case Logic: Always swerve towards center if on edge lanes
                      if curr_lane <= 0:
                          self.player.vx += 1.0 # Force Right
                      elif curr_lane >= LANE_COUNT - 1:
                          self.player.vx -= 1.0 # Force Left
                      else:
                          # Standard logic: swerve away from obstacle center
                          if self.player.x < obs.x:
                              self.player.vx -= 1.0 # Swerve Left
                          else:
                              self.player.vx += 1.0 # Swerve Right
            
    def get_lane_center(self):
        # Helper implementation
        center = self.player.x + self.player.width // 2
        return center
