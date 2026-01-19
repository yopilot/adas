from ursina import *
import random

class TrafficCar(Entity):
    def __init__(self, z_start, speed_offset):
        lane_positions = [-5, 0, 5]
        x_pos = random.choice(lane_positions)
        super().__init__()
        
        self.position = (x_pos, 0.5, z_start)
        self.collider = 'box'
        
        # Visuals
        body_color = random.choice([color.red, color.yellow, color.blue, color.orange, color.violet])
        self.body = Entity(parent=self, model='cube', color=body_color, scale=(2, 1, 4), position=(0, 0, 0))
        self.cabin = Entity(parent=self.body, model='cube', color=color.black66, scale=(0.9, 0.6, 0.6), position=(0, 0.6, 0))
        
        # Wheels
        w_scale = (0.4, 0.8, 0.8)
        w_col = color.black
        # Using cube models to avoid missing asset errors
        Entity(parent=self, model='cube', color=w_col, rotation=(0,0,90), scale=w_scale, position=(-1.1, -0.2, 1.2))
        Entity(parent=self, model='cube', color=w_col, rotation=(0,0,90), scale=w_scale, position=(1.1, -0.2, 1.2))
        Entity(parent=self, model='cube', color=w_col, rotation=(0,0,90), scale=w_scale, position=(-1.1, -0.2, -1.2))
        Entity(parent=self, model='cube', color=w_col, rotation=(0,0,90), scale=w_scale, position=(1.1, -0.2, -1.2))

        # Taillights (Visible to player usually)
        Entity(parent=self.body, model='cube', color=color.red, scale=(0.2, 0.2, 0.1), position=(-0.3, 0.1, -0.51))
        Entity(parent=self.body, model='cube', color=color.red, scale=(0.2, 0.2, 0.1), position=(0.3, 0.1, -0.51))

        self.speed = 20 + speed_offset # Base speed for traffic
        
    def update(self):
        # Move forward constantly
        self.z += self.speed * time.dt
        
        # Simple subtle lane sway
        # self.x += math.sin(time.time() + self.z) * 0.01 

class TrafficManager(Entity):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.cars = []
        self.spawn_timer = 0
        self.spawn_rate = 2.0 # Decreased for more traffic
        
    def update(self):
        # Despawn cars behind
        for c in self.cars[:]:
            if c.z < self.player.z - 50:
                self.cars.remove(c)
                destroy(c)
                
        # Spawn new cars
        self.spawn_timer -= time.dt
        if self.spawn_timer <= 0:
            self.spawn_car()
            self.spawn_timer = random.uniform(1.0, 3.0)
            
        # Collision Check (Simple box overlap)
        # Player vs Traffic
        hit_info = self.player.intersects()
        if hit_info.hit and isinstance(hit_info.entity, TrafficCar):
             # Crash logic - Stop player or bounce
             self.player.base_speed = -5
             print_on_screen("CRASH!", scale=2, duration=1)

    def spawn_car(self):
        spawn_dist = 200
        z_pos = self.player.z + spawn_dist
        
        # Varies speed so some are faster/slower than others
        speed_var = random.uniform(-5, 10) 
        
        new_car = TrafficCar(z_pos, speed_var)
        
        # Prevent spawning on top of another car
        for c in self.cars:
            if abs(c.z - z_pos) < 15 and abs(c.x - new_car.x) < 2:
                destroy(new_car)
                return
                
        self.cars.append(new_car)
