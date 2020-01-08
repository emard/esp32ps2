#!/usr/bin/env python3

import pygame

pygame.init()
(width, height) = (320, 200)
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption(u'Mouse events - any key to quit')
pygame.display.flip()
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

while(True):
  event = pygame.event.wait()
  if event.type == pygame.KEYDOWN:
    print("QUIT")
    break
  print(pygame.mouse.get_rel(), pygame.mouse.get_pressed())
  