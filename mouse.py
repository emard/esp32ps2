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
  wheel = 0
  if event.type == pygame.MOUSEBUTTONDOWN: # for wheel events
    if event.button == 4: # wheel UP
      wheel = -1
    if event.button == 5: # wheel DOWN
      wheel = 1
  print(pygame.mouse.get_rel(), wheel, pygame.mouse.get_pressed())
  