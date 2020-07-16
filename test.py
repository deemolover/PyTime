import pygame
from pygame.locals import *

from utils import *
from game import *
from control import *


class OwnerTester(ParticleOwnerBase):
    def __init__(self, identity):
        super(OwnerTester, self).__init__(identity)
        self.force = Vec2d()

    def getForce(self, particle):
        return self.force.copy()

    def setForce(self, force):
        self.force = force.copy()


def testVec2d():
    print("===testVec2d===")
    a = Vec2d((1, 2))
    b = Vec2d((3, 4))
    print(a, b, a*b, a.toTuple())
    x = a.copy()
    c = a+b
    d = a-b
    print(c, d)
    c = c/2
    d = d*2
    print(c, d)
    c = c/3
    c.toInt()
    print(c, c.length())
    print(a.dist(b), a.distManhattan(b))
    print("b is inside A(r=2): ", b.isInsideCircle(a, 2))
    print("b is inside A(r=3): ", b.isInsideCircle(a, 3))


def genParticle():
    owner = OwnerTester("tester")
    owner.setForce(Vec2d((1, 0)))
    data = {
        ParticleState.K_OWNER: owner,
        ParticleState.K_MASS: 1,
        ParticleState.K_ACC: Vec2d((1, 0)),
        ParticleState.K_VEL: Vec2d((1, 0)),
        ParticleState.K_POS: Vec2d((0, 0)),
    }
    return ParticleState(data=data)


def testParticleState():
    print("===testParticleState===")
    state = genParticle()
    print(state)
    for i in range(3):
        state = state.physicalStepCopy()
        print(state)


def testParticleGroup():
    print("===testParticleGroup===")
    state = genParticle()
    group = ParticleGroup()
    group.append(state)
    state = state.physicalStepCopy()
    group.append(state)
    state = state.physicalStepCopy()
    group.append(state)
    print("original:")
    for ele in group:
        print(ele)
    data = group.dump()
    nextGroup = group.physicalStepCopy()
    print("group gen by step:")
    for ele in nextGroup:
        print(ele)
    print("original group after the step:")
    for ele in group:
        print(ele)
    nextGroup.additiveLoad(data)
    print("data loaded:")
    for ele in nextGroup:
        print(ele)


def testParticleContainer():
    print("===testParticleContainer===")
    container = ParticleContainer(3)

    def printer():
        group = container.currentGroup()
        print("{0}:".format(len(group)))
        for ele in group:
            print(ele)

    print("init curr group of size ", end="")
    printer()

    container.backward(1)
    print("init back group of size ", end="")
    printer()

    state = genParticle()
    container.addNextParticle(state)
    state = state.physicalStepCopy()
    container.addNextParticle(state)
    container.updateToNext()
    print("added curr group of size ", end="")
    printer()

    state = state.physicalStepCopy()
    container.addNextParticle(state)
    state = state.physicalStepCopy()
    container.addNextParticle(state)
    container.updateToNext()
    print("added curr group of size ", end="")
    printer()

    container.backward(1)
    group = container.currentGroup()
    print("backward group of size ", end="")
    printer()

    container.flush()
    group = container.currentGroup()
    print("backward group of size ", end="")
    printer()


def testParticleFrameManager():
    print("===testParticleFrameManager===")
    manager = ParticleFrameManager()
    manager.createContainer((5, 0))
    manager.createContainer((1, 0))
    group = ParticleGroup()
    state = genParticle()
    group.append(state)
    state = state.physicalStepCopy()
    group.append(state)

    def getKey(particle):
        pos = particle.pos.copy()
        if pos.x < 3:
            return (1, 0)
        else:
            return (5, 0)
    manager.getKey = getKey
    manager.flushAndAddParticles(group)
    manager.detailPrinter()
    manager.step()
    manager.detailPrinter()
    manager.step()
    manager.detailPrinter()

    def getPeriod(key):
        return 1
    manager.backward(getPeriod)
    manager.detailPrinter()
    return manager


def testParticleManager():
    print("===testParticleManager===")
    rangeX = 4
    rangeY = 4
    manager = ParticleManager(worldRect=(rangeX, rangeY),
                              interval=(2, 2))

    owner = OwnerTester("tester")
    owner.setForce(Vec2d((1, 0)))
    particles = ParticleGroup()
    for i in range(0, rangeX, 2):
        for j in range(0, rangeY, 2):
            particles.append(
                ParticleState(
                    owner=owner,
                    pos=Vec2d((i, j)),
                )
            )
    manager.addParticlesToBuffer(particles)
    manager.commitParticles()
    print("original manager:")
    manager.detailPrinter()
    manager.step()
    print("stepped manager:")
    manager.detailPrinter()

    def getPeriod(key):
        if key[0] < 1 and key[1] < 1:
            return 1
        return 0
    manager.backward(getPeriod)
    print("backward printer")
    manager.detailPrinter()
    return manager


def testGameController():
    print("===testGameController===")

    screen = pygame.display.set_mode((640, 480), 0, 32)
    screen.fill((255, 255, 255))  # WHITE
    pygame.time.set_timer(UserEvent.PRINTER, 5000)
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


def testMain():
    testVec2d()
    testParticleState()
    testParticleGroup()
    testParticleContainer()
    testParticleFrameManager()
    testParticleManager()

    pygame.init()
    testGameController()

    return

    screen = pygame.display.set_mode(
        (ParticleRenderer.WIDTH,
         ParticleRenderer.HEIGHT),
        0, 32
    )


if __name__ == "__main__":
    testMain()
