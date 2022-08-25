import pygame

class moving_circle():

    def __init__(self, x, y, r, color):
        self.x = x
        self.y = y
        self.r = r
        self.color = color

        # Global iteration count (of how many cycles the circle passes)
        self.iter = 1
        self.old_iter = 1 # This is just for printing on the web interface

    def draw_circle(self, window):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.r)
    
    def move_circle(self, window_width, x):
        self.x += x
        self.old_iter = self.iter

        if self.x > window_width + self.r:
            self.x = -self.r
            self.iter += 1
            