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
    
    # Interference Scenario State
    interference_mode = False
    interference_timer = 0
    show_interference_error = False
    
    is_fullscreen = False
    
    # Graphs Data
    dist_history = []
    max_history_points = 50

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
                if event.key == pygame.K_2: adas.flags['LCA'] = not adas.flags['LCA']
                if event.key == pygame.K_3: adas.flags['AEB'] = not adas.flags['AEB']
                if event.key == pygame.K_4: adas.flags['BSD'] = not adas.flags['BSD']
                if event.key == pygame.K_5: adas.flags['ESA'] = not adas.flags['ESA']
                
                # --- INTERFERENCE SCENARIO (Ctrl+E / Ctrl+P) ---
                if (event.key == pygame.K_e and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])) or \
                   (event.key == pygame.K_p and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])):
                    # Activate Radar Interference Scenario
                    interference_mode = True
                    interference_timer = pygame.time.get_ticks()
                    show_interference_error = False
                    
                    # 1. Clear existing entities
                    npcs.clear()
                    obstacles.clear()
                    auto_spawn_npcs = False
                    
                    # 2. Spawn 5 REDcars upstream (Moving towards player)
                    # Semi-circle formation ahead of player
                    # Player is at Y ~650. We spawn them at Y ~100 to 200.
                    center_spawn_x = player.x
                    spawn_y_base = player.y - 500
                    
                    for i in range(5):
                        # V-Shape / Semi-circle
                        # -2, -1, 0, 1, 2 lane offsets roughly
                        lane_offset = i - 2
                        l_x = center_spawn_x + (lane_offset * LANE_WIDTH * 0.8)
                        l_x = max(ROAD_X_START, min(ROAD_X_START + ROAD_WIDTH - 50, l_x))
                        
                        y_pos = spawn_y_base - abs(lane_offset) * 50 
                        
                        # SPEED: Negative means moving AGAINST global traffic flow (Down the screen fast)
                        # Relative speed logic:
                        # rel_speed = self.lane_speed - world_speed
                        # We want them to approach slowly from top.
                        # If player.speed is 8.0. World speed is 8.0. 
                        # To approach from top (move down faster than player moves up?? No.)
                        # Player stays at Y=650. World moves down.
                        # If NPC Y moves down faster than background, it hits player.
                        # NPC Y delta = (lane_speed - player_speed).
                        # We want Y delta to be positive (come down).
                        # So lane_speed should be > player_speed? No.
                        # lane_speed is absolute speed on road.
                        # If oncoming structure: lane_speed = -5. (Moving South).
                        # world_speed (Player moving North) = 8.
                        # rel_speed = -5 - 8 = -13.
                        # self.y -= (-13) -> self.y += 13.
                        # They will fly down at 13 px/frame. Too fast.
                        
                        # Cheat for visual effect:
                        # We want them to linger on screen for 5 seconds.
                        # So relative speed should be small positive, e.g. +1 or +0.5.
                        # rel_speed = lane_speed - world_speed = -0.5 (moves up slowly) OR +0.5 (moves down).
                        # If we want them to approach from FRONT (Top), they must move DOWN screen.
                        # So we need self.y increasing.
                        # self.y -= rel_speed. So rel_speed must be negative.
                        # lane_speed - world_speed = -1.
                        # lane_speed = world_speed - 1.
                        # So if player goes 8, NPC goes 7 (same direction, just slower).
                        # BUT visuals must be flipped (Red, oncoming).
                        # So we set is_oncoming=True, but physically they are "slow cars driving in reverse" effectively.
                        # To the player it looks like they are driving fast towards them if we ignore the road stripes speed.
                        
                        ghost_car = NpcCar(l_x, y_pos, player.speed - 3.0, is_oncoming=True) 
                        ghost_car.has_radar = True 
                        npcs.append(ghost_car)

                # Manual Controls
                if event.key == pygame.K_o:
                    # Spawn Obstacle ahead
                    lane_idx = int((player.x - ROAD_X_START) / LANE_WIDTH)
                    lane_idx = max(0, min(LANE_COUNT - 1, lane_idx)) 
                    lane_x = ROAD_X_START + lane_idx * LANE_WIDTH + (LANE_WIDTH - 40)//2
                    obstacles.append(Obstacle(lane_x, -200))

                if event.key == pygame.K_n:
                     # Spawn NPC ahead
                     lane_idx = random.randint(0, LANE_COUNT - 1)
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
                    
                if event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        # --- Update ---
        
        # 0. Core ADAS Processing
        adas.update(npcs, obstacles, keys)
        
        # Update Graph Data
        dist_history.append(adas.current_distance)
        if len(dist_history) > max_history_points:
            dist_history.pop(0)
        
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
                # Active LCA glows the edge lines
                c = COLOR_LANE_MARKER_ACTIVE if (adas.flags['LCA'] and player.sensor_lca_active) else COLOR_LANE_MARKER
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
        
        # Draw ACC Lock-on Box
        if adas.flags['ACC'] and adas.current_acc_target:
             t = adas.current_acc_target
             # Green brackets cornering the target car
             rect = t.rect.inflate(10, 10)
             pygame.draw.rect(screen, (0, 255, 0), rect, 2, border_radius=5)
             # "LOCK" text
             font_s = pygame.font.SysFont("arial", 12, bold=True)
             lbl = font_s.render("TARGET LOCK", True, (0, 255, 0))
             screen.blit(lbl, (rect.right + 5, rect.top))

        # INTERFERENCE SCENARIO OVERLAY
        if interference_mode:
            current_t = pygame.time.get_ticks()
            elapsed = current_t - interference_timer
            
            # Dashboard Center X (Right side area)
            # Road ends at ROAD_X_START + ROAD_WIDTH
            right_side_start = ROAD_X_START + ROAD_WIDTH
            right_side_width = SCREEN_WIDTH - right_side_start
            dash_center_x = right_side_start + right_side_width // 2
            
            # Phase 1: Explanation Text (0-5s) - ON RIGHT SIDE
            if elapsed < 5000:
                # Flashing warning or static text
                header_text =font_feedback.render("INTERFERENCE DETECTED", True, (255, 255, 0))
                # Blink effect
                if (current_t // 500) % 2 == 0:
                    screen.blit(header_text, (dash_center_x - header_text.get_width()//2, 100))
                    
                # Small technical text
                font_small = pygame.font.SysFont("consolas", 18)
                info_lines = [
                    "Radar-to-Radar Interference",
                    "Uncoordinated FMCW Waves",
                    "Ghost targets accumulating...",
                    "Noise floor elevating..."
                ]
                for i, line in enumerate(info_lines):
                    s = font_small.render(line, True, (255, 200, 200))
                    screen.blit(s, (dash_center_x - s.get_width()//2, 150 + i*25))
            
            # Phase 2: CRITICAL ERROR POPS (After 5s) - ON RIGHT SIDE
            else:
                 # Big red error overlay (Full screen tint is fine)
                 s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                 s.fill((50, 0, 0, 100)) # Red tint
                 screen.blit(s, (0,0))
                 
                 # Big Box - Centered on Dashboard
                 box_w, box_h = 500, 300
                 err_box = pygame.Rect(dash_center_x - box_w//2, SCREEN_HEIGHT//2 - box_h//2, box_w, box_h)
                 
                 pygame.draw.rect(screen, (0, 0, 0), err_box)
                 pygame.draw.rect(screen, (255, 0, 0), err_box, 4)
                 
                 # Text
                 font_huge = pygame.font.SysFont("arial", 48, bold=True)
                 msg = font_huge.render("SYSTEM FAILURE", True, (255, 0, 0))
                 screen.blit(msg, (dash_center_x - msg.get_width()//2, err_box.centery - 80))
                 
                 font_med = pygame.font.SysFont("arial", 24)
                 msg2 = font_med.render("RADAR SENSOR SATURATION", True, (255, 255, 255))
                 screen.blit(msg2, (dash_center_x - msg2.get_width()//2, err_box.centery + 10))
                 
                 # Exit hint
                 font_tiny = pygame.font.SysFont("arial", 20)
                 msg3 = font_tiny.render("Press 'C' to clear scenario", True, (150, 150, 150))
                 screen.blit(msg3, (dash_center_x - msg3.get_width()//2, err_box.centery + 60))
        
        player.draw(screen)
        
        # UI Overlay
        ui.draw(screen, adas, player, keys, auto_spawn_npcs, auto_spawn_obs, is_fullscreen)
        
        # Draw Graph (Bottom Right, under dashboard)
        # Dashboard is around Y=60 to Y=300 approx
        ui.draw_graph(screen, SCREEN_WIDTH - 380, SCREEN_HEIGHT - 120, 360, 100, dist_history, "DISTANCE TO OBJECT (m)", (0, 255, 255))
        
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
