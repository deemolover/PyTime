import pygame
from pygame.locals import *

from utils import *
from game import *
from control import *


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480), 0, 32)
    # set title
    pygame.display.set_caption("time")
    controller = GameController(screen)
    FPS = controller.FPS
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            controller.dispatchEvent(event)
        controller.update()
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
