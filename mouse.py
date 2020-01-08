#!/usr/bin/env python3

import pygame

pygame.init()
(width, height) = (320, 200)
screen = pygame.display.set_mode((width, height))
pygame.display.flip()
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

for i in range(150):
  pygame.event.wait()
  print(pygame.mouse.get_rel(), pygame.mouse.get_pressed())
  