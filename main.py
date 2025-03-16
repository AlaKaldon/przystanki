import pygame

from data_provider import DataProvider
from screen import Screen

# Inicjalizacja pygame
pygame.init()
data_provider = DataProvider()
screen = Screen(data_provider)

while screen.is_running():
    screen.draw()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            screen.stop()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            screen.select_suggestion(event)
        elif event.type == pygame.KEYDOWN:
            screen.process_user_input(event)
    screen.tick()

pygame.quit()
