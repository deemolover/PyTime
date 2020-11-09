import os

import pygame
from pygame.locals import *

from utils import *
from game import *
from math import sqrt

CONTROLLER_UPDATE_FPS = 40
WORLD_HEIGHT = 480
WORLD_WIDTH = 640
HEIGHT_INTERVAL = 10
WIDTH_INTERVAL = 10


def blitCentering(dest, image, pos):
    x, y = pos
    x = x - image.get_width()/2
    y = y - image.get_height()/2
    dest.blit(image, (x, y))


class ResourcePack():
    # TODO: implement auto loading from resource directory
    def __init__(self):
        self.resources = {}

    def loadImage(self, name, **args):
        '''
        param:
        directory - folder the image file is in(default: "resources")
        filename - image filename(default: combine name & extension)
        extension - image file format(default: "png")
        '''
        directory = args.get("directory", "resources")
        extension = args.get("extension", "png")
        filename = args.get("filename", name + "." + extension)
        self.resources[name] = pygame.image.load(
            os.path.join(directory, filename))

    def getImage(self, name):
        return self.resources.get(name)


class LayerTag():
    BACKGROUND = 0
    GAMEOBJECT = 4
    PLAYER = 8
    EFFECT = 16
    UI = 32


class LayerManager():
    def __init__(self, rect=None):
        if rect == None:
            self.rect = ((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.layers = {}
        self.renderedLayers = {}
        self.maxOrder = 8
        self.layerOrder = [
            LayerTag.BACKGROUND,
            LayerTag.GAMEOBJECT,
            LayerTag.PLAYER,
            LayerTag.EFFECT,
            LayerTag.UI
        ]

    def getSurface(self, layerTag, orderInLayer=0, flushed=False):
        '''
        will (definitely) get a surface
        if the order is out of range(-maxOrder/2, maxOrder/2),
        it will be reset to nearest bound
        flushed - flush the returned surface
        '''
        layer = self.layers.get(layerTag)
        result = None
        orderInLayer = int(orderInLayer)
        orderInLayer += self.maxOrder // 2
        if orderInLayer < 0:
            orderInLayer = 0
        elif orderInLayer >= self.maxOrder:
            orderInLayer = self.maxOrder-1
        if layer != None:
            if layer[orderInLayer] != None:
                result = layer[orderInLayer]
            else:
                surface = pygame.Surface(self.rect).convert_alpha()
                layer[orderInLayer] = surface
                result = surface
        else:
            self.renderedLayers[layerTag] = pygame.Surface(
                self.rect).convert_alpha()
            self.layers[layerTag] = [None] * self.maxOrder
            surface = pygame.Surface(self.rect).convert_alpha()
            self.layers[layerTag][orderInLayer] = surface
            result = surface
        if flushed == True:
            result.fill(0)
        return result

    def tryRenderLayer(self, layerTag, target=None):
        '''
        try to pile up surfaces in speficied layer
        return None if no such layer exists
        param:
        target - specify a target surface to render on(additively)
        '''
        if layerTag in self.layers.keys():
            if target == None:
                target = self.renderedLayers[layerTag]
                target.fill(0)
            for surface in self.layers[layerTag]:
                if surface == None:
                    continue

                target.blit(surface, (0, 0))
            return target
        else:
            return None

    def renderLayers(self, target, layerList=None, flushed=True):
        '''
        render layers to target according to layerList
        layer with smaller index in the list will be rendered earlier
        (that is, at the bottom of target / further from viewer)
        param:
        layerList - list of layer tags(use default if not provided)
        flushed - if true, target will be flushed before rendering
        '''
        if layerList == None:
            layerList = self.layerOrder
        if flushed:
            target.fill(0)
        for tag in layerList:
            self.tryRenderLayer(tag, target)


class RingSkill(PlayerSkillBase):
    def __init__(self, player):
        # TODO use identity to manage skills, or get rid of it
        identity = "RingSkill"
        super(RingSkill, self).__init__(identity, player)
        self.skillPeriod = 50
        self.cooldownTimer = 0
        self.cooldownPeriod = 115

        self.renderTimer = 0
        self.renderPeriod = 120

        self.innerRad = 20
        self.outerRad = 100
        self.usedPoint = None

        self.color = (255, 255, 0, 50)  # YELLOW

    def step(self):
        ''' override '''
        if self.cooldownTimer > 0:
            self.cooldownTimer -= 1

    def renderSkill(self, surface):
        if self.renderTimer > 0:
            radius = int(self.outerRad)
            width = int(self.outerRad - self.innerRad)
            color = None
            pos = self.usedPoint
            pos = (int(pos[0]), int(pos[1]))
            pygame.draw.circle(
                surface,
                self.color,
                pos,
                radius,
                width
            )
            self.renderTimer -= 1

    def isActive(self):
        return self.cooldownTimer == 0

    def useSkillOn(self, manager):
        if self.cooldownTimer > 0:
            return Result.SKILL_UNAVAILABLE
        else:
            self.usedPoint = self.player.core.pos.toTuple()
            manager.backward(self._getPeriod)
            self.cooldownTimer = self.cooldownPeriod
            self.renderTimer = self.renderPeriod
        return Result.SUCCEED

    def _getPeriod(self, key):
        pos = self.usedPoint
        dist = abs(pos[0]-key[0])+abs(pos[1]-key[1])
        if dist < self.outerRad and dist > self.innerRad:
            return self.skillPeriod
        else:
            return 0


class UserEvent():
    PRINTER = pygame.USEREVENT + 1


class GameController():

    class PlayerData(ParticleOwnerBase):
        def __init__(self, identity, manager, owner,
                     color, loc, mapMove, mapAttack, commands):

            super(GameController.PlayerData, self).__init__(identity+"data")

            self.friction = 0.4

            self.identity = identity
            self.mapMove = mapMove      # dict{key, force}
            self.mapAttack = mapAttack  # dict{key, direction}
            self.owner = owner

            self.force = (0, 0)
            self.keyDown = None
            self.attDown = None

            self.player = Player(
                identity=self.identity,
                manager=manager,
                owner=self,
                color=color,
                loc=loc
            )

            for direction, skillBuilder in commands.items():
                self.player.loadSkill(direction, skillBuilder(self.player))

        def spawnParticles(self):
            particles = ParticleGroup()
            for i in range(-4, 5):
                mass = 1 + i / 20
                particles.append(ParticleState(
                    owner=self.player,
                    mass=mass,
                    pos=self.player.core.pos
                ))
            self.player.manager.addParticlesToBuffer(particles)

        def getForce(self, particle):
            ''' override '''
            return Vec2d(self.force)-particle.vel*self.friction

        def parseEvent(self, event):
            res = 0  # succeed
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                if event.key in self.mapMove.keys():
                    if event.type == pygame.KEYDOWN:
                        self.keyDown = event.key
                        self.force = self.mapMove[event.key]
                        print("PLAYER {0} received DOWN MOVE event, response: {1}".format(
                            self.identity, self.force))
                    else:  # KEYUP
                        if self.keyDown == event.key:
                            self.keyDown = None
                            self.force = (0, 0)
                        print("PLAYER {0} received UP MOVE event, response: {1}".format(
                            self.identity, self.force))
                elif event.key in self.mapAttack.keys():
                    if event.type == pygame.KEYDOWN and self.attDown == None:
                        self.attDown = event.key
                        res = self.player.command(self.mapAttack[event.key])
                        print("PLAYER {0} received DOWN ATT event, response: {1}".format(
                            self.identity, res))
                    else:  # KEYUP
                        if self.attDown == event.key:
                            self.attDown = None
                        print("PLAYER {0} received UP ATT event, response: {1}".format(
                            self.identity, self.force))
            elif event.type == UserEvent.PRINTER:
                self.player.detailPrinter()
            return res

        def renderPlayer(self, surface):
            pos = self.player.core.pos.toTuple()
            image = self.owner.resources.getImage("player")
            blitCentering(surface, image, pos)

        def renderSkills(self, surface):
            for skill in self.player.getSkills():
                skill.renderSkill(surface)

    def __init__(self, screen):
        self.screen = screen
        self.layers = LayerManager()

        self.resources = ResourcePack()
        self.resources.loadImage("player")

        self.FPS = CONTROLLER_UPDATE_FPS
        self.worldRect = (WORLD_WIDTH, WORLD_HEIGHT)
        self.interval = (WIDTH_INTERVAL, HEIGHT_INTERVAL)

        self.manager = ParticleManager(self.worldRect, self.interval)
        self.renderer = ParticleRenderer(self.manager)

        self.AID = "playerA"
        self.BID = "playerB"

        self.players = {}
        self.players[self.AID] = self.PlayerData(
            manager=self.manager,
            owner=self,
            identity=self.AID,
            color=(255, 0, 0),
            loc=(50, 50),
            mapMove={
                pygame.K_RIGHT: (1, 0),
                pygame.K_LEFT:  (-1, 0),
                pygame.K_UP:    (0, -1),
                pygame.K_DOWN:  (0, 1)
            },
            mapAttack={
                pygame.K_BACKSLASH: 1
            },
            commands={
                1: RingSkill
            }
        )

        self.players[self.BID] = self.PlayerData(
            manager=self.manager,
            owner=self,
            identity=self.BID,
            color=(0, 0, 255),
            loc=(self.worldRect[0]-50, self.worldRect[1]-50),
            mapMove={
                pygame.K_d:  (1, 0),
                pygame.K_a:  (-1, 0),
                pygame.K_w:  (0, -1),
                pygame.K_s:  (0, 1)
            },
            mapAttack={
                pygame.K_SPACE: 1
            },
            commands={
                1: RingSkill
            }
        )

        # TODO: generate some particles for these players
        for data in self.players.values():
            data.spawnParticles()
        self.manager.commitParticles()

    def dispatchEvent(self, event):
        ''' dispatch pygame event '''
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            for data in self.players.values():
                data.parseEvent(event)
        elif event.type == UserEvent.PRINTER:
            print("=== time interrupt ===")
            self.manager.simplePrinter()
            for data in self.players.values():
                data.parseEvent(event)

    def update(self):
        ''' called from pygame cycle '''
        for data in self.players.values():
            data.player.step()
        self.manager.step()

        self.layers.getSurface(
            LayerTag.BACKGROUND,
        ).fill((200, 200, 200))  # WHITE BACKGROUND

        surface = self.renderer.render()
        self.layers.getSurface(
            LayerTag.GAMEOBJECT,
            flushed=True
        ).blit(surface, (0, 0))

        surface = self.layers.getSurface(
            LayerTag.PLAYER,
            flushed=True
        )
        for data in self.players.values():
            data.renderPlayer(surface)

        surface = self.layers.getSurface(
            LayerTag.EFFECT,
            flushed=True
        )
        for data in self.players.values():
            data.renderSkills(surface)

        self.layers.renderLayers(self.screen, flushed=True)
