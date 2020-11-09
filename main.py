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
    frame_count = 0
    prev_time = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            controller.dispatchEvent(event)
        controller.update()
        pygame.display.update()
        frame_count += 1
        curr_time = pygame.time.get_ticks()
        if (curr_time - prev_time > 3000):
            print(frame_count*1000 / (curr_time-prev_time), " FPS")
            prev_time = curr_time
            frame_count = 0
        clock.tick(FPS)


if __name__ == "__main__":
    main()
