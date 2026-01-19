from ursina import *
import random

class RoadSegment(Entity):
    def __init__(self, z_pos, index):
        super().__init__()
        self.position = (0, 0, z_pos)
        self.z_pos = z_pos
        
        # Road Surface
        self.surface = Entity(
            parent=self,
            model='plane',
            color=color.rgb(50, 50, 50), # Dark Asphalt
            scale=(20, 1, 40),
            position=(0, 0, 0),
            collider='box'
        )
        
        # Markings (Center lines)
        # Dashed line
        for i in range(4): # 4 dashes per segment
            Entity(
                parent=self.surface,
                model='cube',
                color=color.white,
                scale=(0.02, 0.01, 0.15),
                position=(0, 0.01, -0.375 + i * 0.25)
            )
            
        # Side Lines
        Entity(parent=self.surface, model='cube', color=color.white, scale=(0.02, 0.01, 1), position=(-0.45, 0.01, 0))
        Entity(parent=self.surface, model='cube', color=color.white, scale=(0.02, 0.01, 1), position=(0.45, 0.01, 0))

        # Grass / Shoulders
        self.grass_l = Entity(parent=self, model='plane', color=color.rgb(34, 139, 34), scale=(40, 1, 40), position=(-30, -0.01, 0))
        self.grass_r = Entity(parent=self, model='plane', color=color.rgb(34, 139, 34), scale=(40, 1, 40), position=(30, -0.01, 0))

        # Decorations (Trees/Lamps)
        # Simple procedural generation
        if index % 2 == 0:
            self.create_tree(-15, random.uniform(-10, 10))
            self.create_tree(15, random.uniform(-10, 10))

    def create_tree(self, x, z):
        # Trunk - Using cubes
        trunk = Entity(parent=self, model='cube', color=color.rgb(100, 50, 0), scale=(1, 3, 1), position=(x, 1.5, z))
        # Leaves - Using cubes (pyramid-like if we scale them, but cubes are safe)
        leaves = Entity(parent=self, model='cube', color=color.rgb(0, 100, 0), scale=(3, 4, 3), position=(x, 3.5, z))


class Environment(Entity):
    def __init__(self):
        super().__init__()
        self.road_segments = []
        self.segment_length = 40
        self.num_segments = 12
        self.segment_count = 0
        
        # Initial Road Generation
        for i in range(self.num_segments):
            self.add_segment()
            
        # Skybox
        # Using solid color to avoid texture issues
        self.sky = Sky(color=color.sky_blue if hasattr(color, 'sky_blue') else color.azure)

    def add_segment(self):
        z = self.segment_count * self.segment_length
        seg = RoadSegment(z, self.segment_count)
        self.road_segments.append(seg)
        self.segment_count += 1
        
    def update_road(self, player_z):
        # Infinite generation logic
        # If the first segment is totally behind the player (plus buffer), move it to front
        while self.road_segments[0].z_pos < player_z - self.segment_length * 2:
            old_seg = self.road_segments.pop(0)
            destroy(old_seg) # Clean up old entity
            
            self.add_segment() # Add new at front
