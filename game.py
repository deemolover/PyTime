from collections import defaultdict
from sys import exit

import pygame
from pygame.locals import *

from math import sin, cos, tan, atan
from math import sqrt

from utils import *

SCREEN_HEIGHT = 480
SCREEN_WIDTH = 640


class ParticleManager():
    '''
    Particle manager. Manage containers of particles.
    key & position of particles is based on world coordinate.
    '''

    def __init__(self,
                 worldRect=(640, 480),
                 interval=(1, 1)
                 ):
        self.frame = ParticleFrameManager()
        self.rangeX, self.rangeY = worldRect
        self.interX, self.interY = interval
        for i in range(0, self.rangeX, self.interX):
            for j in range(0, self.rangeY, self.interY):
                self.frame.createContainer((i, j))
        self.frame.getKey = self.getKey
        self.particlesBuffer = []

        self.statics = defaultdict(int)

    def addParticlesToBuffer(self, particles):
        self.particlesBuffer.extend(particles)

    def commitParticles(self):
        self.frame.flushAndAddParticles(self.particlesBuffer)
        self.particlesBuffer = []

    def updateStatics(self):
        self.statics.clear()
        for particle in self.frame.group:
            self.statics[particle.owner.identity] += 1

    def particleCountOf(self, owner):
        ''' now we can get ask for number of particles! '''
        return self.statics[owner.identity]

    def step(self):
        ''' delegate for frame '''
        self.frame.step()
        self.updateStatics()

    def backward(self, getPeriod):
        '''
        delegate for frame
        getPeriod(key) should return a period of int/float
        '''
        self.frame.backward(getPeriod)
        self.updateStatics()

    def getKey(self, particle):
        pos = particle.pos
        return (self.interX*int(pos.x / self.interX),
                self.interY*int(pos.y / self.interY))

    def detailPrinter(self):
        print("manager: ", self.statics)
        for i in range(0, self.rangeX, self.interX):
            for j in range(0, self.rangeY, self.interY):
                key = (i, j)
                print(key, end=" ")
                self.frame.containers[key].detailPrinter()

    def simplePrinter(self):
        print("manager: ", self.statics)


class ParticleRenderer():
    '''
    Particle renderer, renders particles to pygame surface.
    Renders based on screen coordinate.
    Need to translate coordinate in manager to screen
    '''

    def __init__(self, manager):
        self.pixels = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # self.pixels = pygame.PixelArray(self.pixels)
        self.manager = manager
        self.scaleX = SCREEN_WIDTH / self.manager.rangeX
        self.scaleY = SCREEN_HEIGHT / self.manager.rangeY

    def fromWorldToScreen(self, vec):
        return (vec.x*self.scaleX, vec.y*self.scaleY)

    def render(self):
        self.pixels.fill((255, 255, 255, 0))
        for particle in self.manager.frame.group:
            pos = particle.pos.toTuple()
            pos = (int(pos[0]), int(pos[1]))
            radius = int(3)
            pygame.draw.circle(
                self.pixels,
                particle.owner.getColor(particle),
                pos,
                radius,
                0)  # radius
            # self.pixels[pos] = particle.owner.getColor(particle)
        # return self.pixels.surface
        return self.pixels


class PlayerSkillBase():
    def __init__(self, identity, player):
        self.identity = identity
        self.player = player

    def isActive(self):
        return True

    def getPlayer(self):
        return self.player

    def getPeriod(self, key):
        return 0


class Player(ParticleOwnerBase):
    def __init__(self, identity, manager, owner, color, loc):
        '''
        identity: PLAYER ID
        manager: particle manager
        owner: here it is the game controller
        color: COLOR for the PLAYER's particles
        loc: initial location of the PLAYER
        '''
        super(Player, self).__init__(identity)

        self.manager = manager
        self.owner = owner

        self.forceCoef = 0.1
        self.radius = 10
        self.gravity = 2.0
        self.friction = 1.2
        self.color = color
        self.core = ParticleState(
            owner=owner,
            pos=Vec2d(loc))

        self.skills = {}  # PlayerSkillBase()

    def getForce(self, particle):
        ''' override '''
        vec = self.core.pos - particle.pos
        dist = vec.length()
        coef = self.forceCoef * \
            atan(dist / self.radius - self.gravity * particle.mass)
        force = vec * coef
        force = force - particle.vel*self.friction
        return force

    def getColor(self, particle):
        ''' override '''
        return self.color

    def step(self):
        ''' do physical calculations '''
        self.core = self.core.physicalStepCopy()

    def loadSkill(self, direction, skill):
        self.skills[direction] = skill

    def command(self, direction):
        '''
        do something when events like keyboard inputs take place
        mainly for using skills
        '''
        # TODO: implement CD time (necessary!)
        skill = self.skills.get(direction)
        if skill == None:
            return 1  # 1 for direction not found
        if skill.isActive():
            self.manager.backward(skill.getPeriod)
        return 0  # 0 for success

    def detailPrinter(self):
        print("player ", self.identity, " core:", self.core)
