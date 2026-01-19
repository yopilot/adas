from ursina import *

class KeyDisplay(Entity):
    def __init__(self, key_char, position):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=color.black66,
            position=position,
            scale=(0.08, 0.08)
        )
        self.key_char = key_char
        self.label = Text(
            parent=self, 
            text=key_char.upper(), 
            origin=(0,0), 
            scale=1.5,
            color=color.white
        )
        
        # Border
        self.border = Entity(parent=self, model='quad', color=color.white, scale=(1.1, 1.1), z=1)

    def update(self):
        if held_keys[self.key_char]:
            self.color = color.white
            self.label.color = color.black
        else:
            self.color = color.rgba(0,0,0, 0.5)
            self.label.color = color.white

class HUD(Entity):
    def __init__(self):
        super().__init__()
        
        # WASD Layout on screen
        # Centre point for keys: Bottom Left area
        base_x = -0.75
        base_y = -0.35
        gap = 0.09
        
        # W is above S
        self.key_w = KeyDisplay('w', (base_x, base_y + gap))
        self.key_a = KeyDisplay('a', (base_x - gap, base_y))
        self.key_s = KeyDisplay('s', (base_x, base_y))
        self.key_d = KeyDisplay('d', (base_x + gap, base_y))
        
        # Speedometer
        self.speed_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.black66,
            position=(0.7, -0.4),
            scale=(0.3, 0.1)
        )
        
        self.speed_text = Text(
            parent=camera.ui,
            text='0 km/h',
            position=(0.7, -0.4),
            scale=2,
            origin=(0,0),
            color=color.yellow
        )
        
        self.info_text = Text(
            parent=camera.ui,
            text='WASD to Drive',
            position=(0, 0.45),
            origin=(0,0),
            scale=1,
            color=color.white
        )

    def update_speed(self, speed):
        # Convert absolute speed unit to display km/h (arbitrary scale)
        # Using abs() because reversing shows negative speed
        display_speed = int(speed * 3.0) 
        self.speed_text.text = f'{display_speed} KM/H'
