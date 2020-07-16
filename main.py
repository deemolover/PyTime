import pygame
from pygame.locals import *

from utils import *
from game import *


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    # set title
    pygame.display.set_caption("time")
    # load image
    #background = pygame.image.load("pics/bg3.png").convert()
    clock = pygame.time.Clock()
    #m_x, m_y = pygame.mouse.get_pos()

    # main loop
    while True:
        # acquire event from stack
        for event in pygame.event.get():
            # QUIT event
            if event.type == QUIT:
                exit()
            if event.type == MOUSEBUTTONDOWN:
                print("mouse pressed")

        screen.fill(white)
        # render image
        x = (WIDTH - background.get_width())/2
        y = (HEIGHT - background.get_height())/2
        screen.blit(background, (x, y))

        # update
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
