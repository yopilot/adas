import pygame
import random
import sys
from simulation_config import *
from simulation_objects import PlayerCar, NpcCar, Obstacle
from simulation_adas import ADAS_System
from simulation_ui import UI_Manager

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Aptiv ADAS Simulation Showcase")
    clock = pygame.time.Clock()

    font_feedback = pygame.font.SysFont("arial", 40, bold=True)

    # --- Game Objects ---
    player = PlayerCar()
    adas = ADAS_System(player)
    ui = UI_Manager()
    
    npcs = []
    obstacles = []
    
    # Road Scrolling
    road_y_offset = 0
    
    # Spawn Timers
    npc_timer = 0
    obs_timer = 0
    
    # Logic Toggles
    auto_spawn_npcs = False # Default Off for control
    auto_spawn_obs = False

    running = True
    
    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        
        keys = pygame.key.get_pressed()
        
        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Toggle ADAS
                if event.key == pygame.K_1: adas.flags['ACC'] = not adas.flags['ACC']
                if event.key == pygame.K_2: adas.flags['LKA'] = not adas.flags['LKA']
                if event.key == pygame.K_3: adas.flags['AEB'] = not adas.flags['AEB']
                if event.key == pygame.K_4: adas.flags['BSD'] = not adas.flags['BSD']
                if event.key == pygame.K_5: adas.flags['ESA'] = not adas.flags['ESA']
                
                # Manual Controls
                if event.key == pygame.K_o:
                    # Spawn Obstacle ahead
                    lane_idx = int((player.x - ROAD_X_START) / LANE_WIDTH)
                    lane_idx = max(0, min(2, lane_idx)) 
                    lane_x = ROAD_X_START + lane_idx * LANE_WIDTH + (LANE_WIDTH - 40)//2
                    obstacles.append(Obstacle(lane_x, -200))

                if event.key == pygame.K_n:
                     # Spawn NPC ahead
                     lane_idx = random.choice([0, 1, 2])
                     lane_x = ROAD_X_START + lane_idx * LANE_WIDTH + (LANE_WIDTH - 40)//2
                     npcs.append(NpcCar(lane_x, -100, random.uniform(BASE_SPEED * 0.5, BASE_SPEED * 1.2)))
                
                if event.key == pygame.K_c:
                    # Clear all
                    npcs.clear()
                    obstacles.clear()
                    
                if event.key == pygame.K_8:
                    auto_spawn_npcs = not auto_spawn_npcs
                if event.key == pygame.K_9:
                    auto_spawn_obs = not auto_spawn_obs

        # --- Update ---
        
        # 0. Core ADAS Processing
        adas.update(npcs, obstacles, keys)
        
        # 1. Player Update
        # Pass ADAS flags and speed info to player controller
        player.update(keys, adas.flags, player.speed)
        
        # 2. Road Logic (Infinite Scroll)
        road_y_offset += player.speed * 20 * dt 
        if road_y_offset >= 100: # Dash segment length + gap
            road_y_offset = 0
            
        # 3. Spawners
        # NPCs
        npc_timer += dt
        if auto_spawn_npcs and npc_timer > 2.0:
            lane_idx = random.randint(0, LANE_COUNT - 1)
            lane_x = ROAD_X_START + lane_idx * LANE_WIDTH + (LANE_WIDTH - 40)//2
            # Spawn ahead or behind
            # For ACC, we want cars ahead that are kinda slow
            spawn_y = -100
            npc_speed = random.uniform(BASE_SPEED * 0.5, BASE_SPEED * 1.2)
            
            # Simple overlap check
            valid = True
            for c in npcs:
                 if abs(c.y - spawn_y) < 150 and c.x == lane_x: valid = False
                 
            if valid:
                npcs.append(NpcCar(lane_x, spawn_y, npc_speed))
                npc_timer = 0
                
        # Obstacles (Pedestrians/Boxes) - Only spawn if safe-ish or for AEB test
        obs_timer += dt
        if auto_spawn_obs and obs_timer > 5.0 and random.random() < 0.3:
            lane_idx = int((player.x - ROAD_X_START) / LANE_WIDTH)
            lane_idx = max(0, min(LANE_COUNT - 1, lane_idx)) # Spawn in player lane to force AEB/ESA
            lane_x = ROAD_X_START + lane_idx * LANE_WIDTH + (LANE_WIDTH - 40)//2
            obstacles.append(Obstacle(lane_x, -200)) # Spawn far ahead
            obs_timer = 0

        # 4. Entity Updates (Relative movement)
        for car in npcs[:]:
            car.update_relative(player.speed)
            if car.y > SCREEN_HEIGHT + 100 or car.y < -500:
                npcs.remove(car)
                
        for obs in obstacles[:]:
            obs.update_relative(player.speed)
            if obs.y > SCREEN_HEIGHT + 100:
                obstacles.remove(obs)
                
        # 5. Drawing ---
        screen.fill(COLOR_BG)
        
        # Draw Road
        pygame.draw.rect(screen, COLOR_ROAD, (ROAD_X_START, 0, ROAD_WIDTH, SCREEN_HEIGHT))
        
        # Draw Lane Lines
        for i in range(LANE_COUNT + 1):
            x = ROAD_X_START + i * LANE_WIDTH
            if i == 0 or i == LANE_COUNT:
                # Solid edge lines
                # Active LKA glows the edge lines
                c = COLOR_LANE_MARKER_ACTIVE if (adas.flags['LKA'] and player.sensor_lka_active) else COLOR_LANE_MARKER
                pygame.draw.line(screen, c, (x, 0), (x, SCREEN_HEIGHT), 5)
            else:
                # Dashed lines for inner lanes
                # Calculate movement based on road_y_offset
                # Pattern: 50px line, 50px gap -> 100px stride
                for y in range(int(road_y_offset) - 100, SCREEN_HEIGHT, 100):
                    pygame.draw.line(screen, COLOR_LANE_MARKER, (x, y), (x, y + 50), 2)
                    
        # Entities
        for car in npcs: car.draw(screen)
        for obs in obstacles: obs.draw(screen)
        
        player.draw(screen)
        
        # UI Overlay
        ui.draw(screen, adas, player.speed, keys, auto_spawn_npcs, auto_spawn_obs)
        
        # Crash/Safety Feedback
        # Simple collision check
        player_rect = player.rect
        crashed = False
        for c in npcs:
            if player_rect.colliderect(c.rect):
                crashed = True
        for o in obstacles:
            if player_rect.colliderect(o.rect):
                crashed = True
                
        if crashed:
            txt = font_feedback.render("COLLISION DETECTED", True, COLOR_ACCENT_BAD)
            screen.blit(txt, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))
            # In a real sim, we might reset or pause
            player.speed = -2 # Bump back

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
