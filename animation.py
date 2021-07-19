import pygame
import sys
import time
import math
import ctypes

def cal_distance(p1, p2):
    return math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))

class LoadPoint:
    def __init__(self, load):
        self.load = load
        self.init()
    def destroy(self):
        self.load.addtime = pygame.time.get_ticks()
        self.load.loadpoints.remove(self)
    def init(self):
        self.angle = 90
        self.r = self.load.r
        self.r2 = self.load.r2
        self.speed = 9
        self.speedscale = 0
        self.times = 1
    def update(self):
        x = math.cos(math.radians(self.angle))
        y = math.sin(math.radians(self.angle))
        pygame.draw.circle(self.load.loadsurface, (0, 0, 0),
                           (self.r2 + self.r + int(x * self.r), self.r2 + self.r + int(y * self.r)), self.r2)
        self.angle += self.speed
        if self.angle >= 180 and self.angle <= 330:
            if self.speedscale == 0:
                if self.speed >= 3.5:
                    self.speed -= 0.5
                else:
                    self.speedscale = 1
                    self.times += 1
        if self.angle >= 330 or self.angle <= 180:
            if self.speedscale == 1:
                if self.speed <= 10:
                    self.speed += 0.5
                else:
                    self.speedscale = 0
        if 85 <= self.angle <= 95:
            if self.times > 2:
                self.destroy()
        self.angle %= 360

class Load:
    def __init__(self, screen, x=0, y=0, r=50):
        self.screen = screen
        self.x = x
        self.y = y
        self.r = r
        self.init()
    def draw(self):
        self.screen.blit(self.loadsurface, (self.x, self.y))
    def init(self):
        self.r2 = 6
        self.loadsurface = pygame.Surface((self.r * 2 + self.r2 * 2, self.r * 2 + self.r2 * 2))
        self.loadpoints = []
        self.addtime = 0
        self.addable = True
    def update(self):
        self.loadsurface.fill((255, 255, 255))
        for loadpoint in self.loadpoints:
            loadpoint.update()
        if self.addable:
            if len(self.loadpoints) < 5:
                if pygame.time.get_ticks() - self.addtime >= 200:
                    self.loadpoints.append(LoadPoint(self))
                    self.addtime = pygame.time.get_ticks()
            else:
                self.addable = False
        else:
            if not self.loadpoints:
                if pygame.time.get_ticks() - self.addtime >= 500:
                    self.addable = True
