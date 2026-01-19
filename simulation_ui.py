import pygame
from simulation_config import *

class UI_Manager:
    def __init__(self):
        self.font_large = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Load Logo or Fallback
        self.logo_surf = None
        try:
            self.logo_surf = pygame.image.load(LOGO_PATH_PNG)
            self.logo_surf = pygame.transform.scale(self.logo_surf, (150, 40))
        except:
            pass # Will render text if None
            
        # Panel Rect
        self.panel_rect = pygame.Rect(20, 20, 250, 400)

    def draw_keys(self, surface, keys, start_x, start_y):
        # Layout:
        #   ^
        # < v >
        key_size = 60
        gap = 10
        
        # Mapping Direction -> Keys
        # We want to light up if either WASD or Arrow is pressed
        controls = [
            {'label': '^', 'pos_idx': (1, 0), 'keys': [pygame.K_w, pygame.K_UP]},
            {'label': '<', 'pos_idx': (0, 1), 'keys': [pygame.K_a, pygame.K_LEFT]},
            {'label': 'v', 'pos_idx': (1, 1), 'keys': [pygame.K_s, pygame.K_DOWN]},
            {'label': '>', 'pos_idx': (2, 1), 'keys': [pygame.K_d, pygame.K_RIGHT]},
        ]
        
        for c in controls:
            col, row = c['pos_idx']
            x = start_x + col * (key_size + gap)
            y = start_y + row * (key_size + gap)
            
            is_pressed = any(keys[k] for k in c['keys'])
            
            rect = pygame.Rect(x, y, key_size, key_size)
            
            # Draw BG
            color = (50, 255, 100) if is_pressed else (60, 60, 60)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, (200, 200, 200), rect, 2, border_radius=4)
            
            # Draw Text
            txt_color = (0, 0, 0) if is_pressed else (200, 200, 200)
            lbl = self.font_small.render(c['label'], True, txt_color)
            
            # Center text
            text_rect = lbl.get_rect(center=rect.center)
            surface.blit(lbl, text_rect)

    def draw(self, surface, adas_system, player_speed, keys, auto_npc, auto_obs):
        # Draw Dashboard Background
        # pygame.draw.rect(surface, (10, 10, 10, 200), self.panel_rect, border_radius=10)
        # Use a translucent surface because direct tuple alpha doesn't work with draw.rect
        s = pygame.Surface((250, 400), pygame.SRCALPHA)
        s.fill((10, 10, 10, 220))
        surface.blit(s, (20, 20))
        
        pygame.draw.rect(surface, COLOR_LANE_MARKER, self.panel_rect, 2, border_radius=10)
        
        # Draw Logo
        if self.logo_surf:
            surface.blit(self.logo_surf, (30, 30))
        else:
            # Fallback text
            lbl = self.font_large.render("APTIV", True, (255, 255, 255))
            pygame.draw.circle(surface, (255, 100, 0), (45, 45), 6) # Orange dot logo style
            surface.blit(lbl, (60, 30))
            
        render_y = 90
        
        # Simulation Info
        spd_text = self.font_large.render(f"{int(player_speed * 10)} KM/H", True, COLOR_ACCENT_GOOD)
        surface.blit(spd_text, (30, render_y))
        render_y += 50
        
        # ADAS Toggles List
        features = ["ACC", "LKA", "AEB", "BSD", "ESA"]
        
        lbl_head = self.font_small.render("ADAS SYSTEMS (1-5 to Toggle)", True, (150, 150, 150))
        surface.blit(lbl_head, (30, render_y))
        render_y += 30
        
        for idx, feat in enumerate(features):
            is_active = adas_system.flags[feat]
            col = COLOR_ACCENT_GOOD if is_active else (80, 80, 80)
            status_txt = "ON" if is_active else "OFF"
            
            # Indicator box
            pygame.draw.rect(surface, col, (30, render_y, 10, 10))
            
            # Text
            line = f"{idx+1}. {feat} [{status_txt}]"
            txt_surf = self.font_small.render(line, True, COLOR_TEXT if is_active else (100,100,100))
            surface.blit(txt_surf, (50, render_y - 3))
            
            render_y += 25

        # Instructions
        render_y += 20
        ins = [
            "N: Add NPC | O: Add Obstacle",
            "C: Clear All Screen",
            f"F1: Auto NPC: {'ON' if auto_npc else 'OFF'}",
            f"F2: Auto Obs: {'ON' if auto_obs else 'OFF'}",
            "",
            "1-5: Toggle ADAS Features",
        ]
        for l in ins:
            color = (50, 255, 100) if "ON" in l else (200, 200, 200)
            if "OFF" in l: color = (100, 100, 100)
            
            t = self.font_small.render(l, True, color)
            surface.blit(t, (30, render_y))
            render_y += 20
            
        # Draw WASD Keys on Right Side
        # Screen Width 1280. We want it on right.
        keys_x = SCREEN_WIDTH - 250
        keys_y = SCREEN_HEIGHT - 250
        self.draw_keys(surface, keys, keys_x, keys_y)
