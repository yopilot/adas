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

    def draw(self, surface, adas_system, player, keys, auto_npc, auto_obs, is_fullscreen=False):
        # Draw Left Panel (Controls & Info)
        # Use a translucent surface for left panel
        s = pygame.Surface((300, 500), pygame.SRCALPHA)
        s.fill((10, 10, 10, 220))
        surface.blit(s, (20, 20))
        
        left_panel_rect = pygame.Rect(20, 20, 300, 500)
        pygame.draw.rect(surface, COLOR_LANE_MARKER, left_panel_rect, 2, border_radius=10)
        
        # Draw Logo
        if self.logo_surf:
            surface.blit(self.logo_surf, (30, 30))
        else:
            # Fallback text
            lbl = self.font_large.render("APTIV", True, (255, 255, 255))
            pygame.draw.circle(surface, (255, 100, 0), (45, 45), 6) # Orange dot logo style
            surface.blit(lbl, (60, 30))
            
        render_y = 90
        
        # Simulation Info (Left Side - Basic)
        spd_text = self.font_large.render(f"{int(player.speed * 10)} KM/H", True, COLOR_ACCENT_GOOD)
        surface.blit(spd_text, (30, render_y))
        render_y += 50
        
        # ADAS Toggles List (With Full Names)
        feature_map = {
            "ACC": "Adaptive Cruise Control",
            "LCA": "Lane Centering Assistance",
            "AEB": "Automatic Emergency Braking",
            "BSD": "Blind Spot Detection",
            "ESA": "Evasive Steering Assist"
        }
        features = list(feature_map.keys())
        
        lbl_head = self.font_small.render("ADAS SYSTEMS (1-5 to Toggle)", True, (150, 150, 150))
        surface.blit(lbl_head, (30, render_y))
        render_y += 30
        
        for idx, feat in enumerate(features):
            is_active = adas_system.flags[feat]
            col = COLOR_ACCENT_GOOD if is_active else (80, 80, 80)
            status_txt = "ON" if is_active else "OFF"
            
            # Indicator box
            pygame.draw.rect(surface, col, (30, render_y, 10, 10))
            
            # Text line 1: Acronym + Status
            line1 = f"{idx+1}. {feat} [{status_txt}]"
            txt_surf1 = self.font_small.render(line1, True, COLOR_TEXT if is_active else (100,100,100))
            surface.blit(txt_surf1, (50, render_y - 5))
            
            # Text line 2: Full Name
            full_name = feature_map[feat]
            txt_surf2 = pygame.font.SysFont("consolas", 12).render(full_name, True, (120, 120, 120))
            surface.blit(txt_surf2, (50, render_y + 12))
            
            render_y += 35 # Increased spacing for 2 lines

        # Instructions
        render_y += 20
        ins = [
            "N: Add NPC | O: Add Obstacle",
            "C: Clear All Screen",
            f"F11: Full Screen: {'ON' if is_fullscreen else 'OFF'}",
            f"8: Auto NPC: {'ON' if auto_npc else 'OFF'}",
            f"9: Auto Obs: {'ON' if auto_obs else 'OFF'}",
            "",
            "1-5: Toggle ADAS Features",
        ]
        for l in ins:
            color = (50, 255, 100) if "ON" in l else (200, 200, 200)
            if "OFF" in l: color = (100, 100, 100)
            
            t = self.font_small.render(l, True, color)
            surface.blit(t, (30, render_y))
            render_y += 20
            
        # --- RIGHT SIDE DASHBOARD ---
        
        dash_width = 360
        dash_height = 240
        dash_x = SCREEN_WIDTH - dash_width - 20
        dash_y = 60 # Lowered position
        
        # Background
        ds = pygame.Surface((dash_width, dash_height), pygame.SRCALPHA)
        ds.fill((20, 24, 28, 230))
        surface.blit(ds, (dash_x, dash_y))
        
        dash_rect = pygame.Rect(dash_x, dash_y, dash_width, dash_height)
        pygame.draw.rect(surface, (100, 120, 140), dash_rect, 2, border_radius=8)
        
        # Dashboard Content
        dx = dash_x + 20
        dy = dash_y + 20
        
        # 1. Digital Speedo Central
        # Slightly larger and repositioned
        speedo_center_x = dx + 70
        speedo_center_y = dy + 80
        radius = 65
        
        pygame.draw.circle(surface, (10, 10, 10), (speedo_center_x, speedo_center_y), radius)
        pygame.draw.circle(surface, (0, 200, 255), (speedo_center_x, speedo_center_y), radius, 3)
        
        spd_val = int(player.speed * 10)
        spd_font = pygame.font.SysFont("arial", 60, bold=True)
        lbl_spd = spd_font.render(str(spd_val), True, (255, 255, 255))
        surface.blit(lbl_spd, lbl_spd.get_rect(center=(speedo_center_x, speedo_center_y - 10)))
        
        lbl_unit = self.font_small.render("km/h", True, (150, 150, 255))
        surface.blit(lbl_unit, lbl_unit.get_rect(center=(speedo_center_x, speedo_center_y + 35)))
        
        # 2. Indicators (Lights)
        # Positioned to right of speedo
        lx = dx + 170
        ly = dy + 10
        
        # BSD Left / Right Warning Lights
        # Left Warning
        bsd_l_col = (255, 165, 0) if player.sensor_bsd_left else (50, 30, 0)
        self.draw_indicator(surface, dx, dy, "BSD-L", bsd_l_col, width=60) # Top Left independent

        # Right Warning
        bsd_r_col = (255, 165, 0) if player.sensor_bsd_right else (50, 30, 0)
        # Put BSD-R on the far right
        self.draw_indicator(surface, lx + 50, dy, "BSD-R", bsd_r_col, width=60)

        # AEB Warning (Big Red) - Center Right
        aeb_col = (255, 0, 0) if player.sensor_aeb_active else (50, 0, 0)
        self.draw_indicator(surface, lx, ly + 50, "BRAKE", aeb_col, width=100, height=35)
        
        # LCA Active (Green)
        lca_col = (0, 255, 0) if player.sensor_lca_active else (0, 50, 0)
        self.draw_indicator(surface, lx, ly + 100, "STEER", lca_col, width=100, height=35)
        
        # ACC Distance Info
        if adas_system.flags['ACC']:
            dist_col = (50, 200, 255)
            pygame.draw.rect(surface, (20, 40, 60), (lx, ly + 150, 100, 30), border_radius=4)
            lbl_acc = self.font_small.render("ACC: ON", True, dist_col)
            surface.blit(lbl_acc, (lx + 15, ly + 155))
        else:
            pygame.draw.rect(surface, (20, 20, 20), (lx, ly + 150, 100, 30), border_radius=4)
            lbl_acc = self.font_small.render("ACC: OFF", True, (100, 100, 100))
            surface.blit(lbl_acc, (lx + 15, ly + 155))
            
        
        # Draw WASD Keys on Right Side (Bottom)
        keys_x = SCREEN_WIDTH - 250
        keys_y = SCREEN_HEIGHT - 250
        self.draw_keys(surface, keys, keys_x, keys_y)

    def draw_indicator(self, surface, x, y, text, color, width=50, height=25):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, (200, 200, 200), rect, 1, border_radius=4)
        
        # Text contrast
        start_c = sum(color)/3
        txt_col = (0,0,0) if start_c > 100 else (100,100,100)
        
        lbl = pygame.font.SysFont("arial", 10, bold=True).render(text, True, txt_col)
        surface.blit(lbl, lbl.get_rect(center=rect.center))
