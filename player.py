from ursina import *

class PlayerCar(Entity):
    def __init__(self):
        super().__init__()
        self.model = None # Container
        self.position = (0, 0, 0)
        self.collider = 'box'

        # --- Car Visuals ---
        # Main Body
        self.body = Entity(parent=self, model='cube', color=color.azure, scale=(2, 1, 4), position=(0, 0.5, 0))
        
        # Cabin (Windshield area)
        self.cabin = Entity(parent=self.body, model='cube', color=color.black50, scale=(0.8, 0.5, 0.5), position=(0, 0.75, -0.2))
        
        # Wheels
        wheel_scale = (0.4, 0.8, 0.8)
        wheel_color = color.black
        
        self.wheels = []
        # Front Left - Using cubes to avoid missing model errors
        self.wheels.append(Entity(parent=self, model='cube', color=wheel_color, rotation=(0,0,90), scale=wheel_scale, position=(-1.1, 0.4, 1.2)))
        # Front Right
        self.wheels.append(Entity(parent=self, model='cube', color=wheel_color, rotation=(0,0,90), scale=wheel_scale, position=(1.1, 0.4, 1.2)))
        # Back Left
        self.wheels.append(Entity(parent=self, model='cube', color=wheel_color, rotation=(0,0,90), scale=wheel_scale, position=(-1.1, 0.4, -1.2)))
        # Back Right
        self.wheels.append(Entity(parent=self, model='cube', color=wheel_color, rotation=(0,0,90), scale=wheel_scale, position=(1.1, 0.4, -1.2)))

        # Lights
        # Headlights
        Entity(parent=self.body, model='cube', color=color.yellow, scale=(0.2, 0.2, 0.1), position=(-0.3, 0.1, 0.51))
        Entity(parent=self.body, model='cube', color=color.yellow, scale=(0.2, 0.2, 0.1), position=(0.3, 0.1, 0.51))
        # Taillights
        Entity(parent=self.body, model='cube', color=color.red, scale=(0.2, 0.2, 0.1), position=(-0.3, 0.1, -0.51))
        Entity(parent=self.body, model='cube', color=color.red, scale=(0.2, 0.2, 0.1), position=(0.3, 0.1, -0.51))
        
        # --- Physics Properties ---
        self.base_speed = 0
        self.max_speed = 50
        self.acceleration = 15
        self.deceleration = 10
        self.steering_speed = 20
        self.drift_factor = 0.5
        
        # Setup Camera
        camera.parent = self
        camera.position = (0, 8, -15)
        camera.rotation_x = 20

    def update(self):
        # 1. Acceleration Logic
        if held_keys['w']:
            self.base_speed += self.acceleration * time.dt
        elif held_keys['s']:
            self.base_speed -= self.acceleration * time.dt
        else:
            # Natural friction
            self.base_speed = lerp(self.base_speed, 0, time.dt * 0.5)

        # Clamp Speed
        self.base_speed = clamp(self.base_speed, -15, self.max_speed)
        
        # 2. Steering Logic
        manual_turn = 0
        if held_keys['a']:
            manual_turn = -1
        if held_keys['d']:
            manual_turn = 1
            
        # Turning is effective when moving, but for arcade feel we allow some static turning or scale it
        # We scale turning by a small factor of speed to prevent spinning in place awkwardly, 
        # but keep it responsive.
        turn_sensitivity = 1.0
        if abs(self.base_speed) < 1:
            turn_sensitivity = 0 # Can't turn if stopped
            
        self.x += manual_turn * self.steering_speed * time.dt * (0.5 if abs(self.base_speed) < 5 else 1.0)

        # 3. Apply Movement
        # Move forward in Z
        self.z += self.base_speed * time.dt
        
        # 4. Wheel Animation
        rotation_amount = self.base_speed * 10 * time.dt
        for w in self.wheels:
            w.rotation_x += rotation_amount
            
        # Steer front wheels visual
        steer_angle = manual_turn * 30
        self.wheels[0].rotation_y = steer_angle
        self.wheels[1].rotation_y = steer_angle

        # 5. Constraints
        # Keep on road (approx width 20 -> -10 to 10 boundary)
        # Car width is about 2-3
        self.x = clamp(self.x, -8, 8)
        
        # Tilt car body slightly when turning for "Lookable" feel
        target_lean = manual_turn * 5
        self.body.rotation_z = lerp(self.body.rotation_z, target_lean, time.dt * 5)
