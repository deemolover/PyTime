from math import sin, cos, tan, sqrt

# size of buffer in one container
CONTAINER_MAX_LENGTH = 200
# time slice between two entries in buffer
# time slice down, accuracy up, cost of space up
# should be between 0 and 1
CONTAINER_TIME_SLICE = 1


def prettyStrDict(dictionary):
    return "{"+", ".join(["'"+str(key)+"': "+str(value) for (key, value) in dictionary.items()])+"}"


def optional(val, default, valCond):
    return val if valCond else default


def optional(val, default):
    return val if val != None else default


class Vec2d():
    def __init__(self, pos=(0, 0)):
        if len(pos) == 2:
            self.x = pos[0]
            self.y = pos[1]
        else:
            print("warning: invalid pos used in vec2d init")

    def __add__(self, other):
        if isinstance(other, Vec2d):
            return Vec2d((self.x+other.x, self.y+other.y))
        else:
            print("error: unsupported vec sum with ", other)

    def __sub__(self, other):
        if isinstance(other, Vec2d):
            return Vec2d((self.x-other.x, self.y-other.y))
        else:
            print("error: unsupported vec sub with ", other)

    def __mul__(self, other):
        if isinstance(other, Vec2d):
            return self.x*other.x + self.y*other.y
        elif isinstance(other, int) or isinstance(other, float):
            return Vec2d((self.x*other, self.y*other))
        else:
            print("error: unsupported vec mul with ", other)

    def __truediv__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vec2d((self.x / other, self.y / other))
        else:
            print("error: unsupported vec div with ", other)

    def __str__(self):
        return "Vec2d({0},{1})".format(self.x, self.y)

    def copy(self):
        return Vec2d(self.toTuple())

    def toInt(self):
        self.x = int(self.x)
        self.y = int(self.y)

    def toTuple(self):
        return (self.x, self.y)

    def length(self):
        return sqrt(self.x**2 + self.y**2)

    def dist(self, other):
        return (self - other).length()

    def distManhattan(self, other):
        return abs(self.x-other.x)+abs(self.y-other.y)

    def isInsideCircle(self, center, radius):
        return self.dist(center) <= radius

    def isInsideRect(self, boundA, boundB):
        x1, x2 = boundA.x, boundB.x
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = boundA.y, boundB.y
        y1, y2 = min(y1, y2), max(y1, y2)
        return x1 <= self.x and self.x <= x2 and y1 <= self.x and self.y <= y2


class ParticleOwnerBase():
    def __init__(self, identity):
        self.identity = identity

    def getForce(self, particle):
        '''
        return force for a ParticleState instance
        '''
        return Vec2d()

    def getColor(self, particle):
        '''
        for rendering
        '''
        return None

    def __str__(self):
        return "OWNER("+repr(self.identity)+")"


class ParticleState():
    DEFAULT_MASS = 1
    MAX_TIME_TO_LIVE = 100
    K_OWNER = "owner"
    K_MASS = "mass"
    K_ACC = "acc"
    K_VEL = "vel"
    K_POS = "pos"

    def __init__(self, **args):
        if "data" in args.keys():
            data = args["data"]
            self.owner = data.get(self.K_OWNER, None)  # ParticleOwnerBase
            self.mass = data.get(self.K_MASS, self.DEFAULT_MASS)  # value
            self.acc = data.get(self.K_ACC, Vec2d())  # Vec2d
            self.vel = data.get(self.K_VEL, Vec2d())  # Vec2d
            self.pos = data.get(self.K_POS, Vec2d())  # Vec2d
            return

        self.owner = args.get("owner")
        self.mass = args.get("mass", self.DEFAULT_MASS)
        self.acc = args.get("acc", Vec2d())
        self.vel = args.get("vel", Vec2d())
        self.pos = args.get("pos", Vec2d())

    def dump(self):
        data = {}
        data[self.K_OWNER] = self.owner
        data[self.K_MASS] = self.mass
        data[self.K_ACC] = self.acc
        data[self.K_VEL] = self.vel
        data[self.K_POS] = self.pos
        return data

    def __str__(self):
        return prettyStrDict(self.dump())

    def physicalStepCopy(self, step=1):
        '''
        return a copy of self with physical states stepped
        Now the step calc is linear. May be modified.
        '''
        force = Vec2d()
        if self.owner != None:
            force = self.owner.getForce(self)
        state = ParticleState(
            owner=self.owner,
            pos=self.pos+self.vel*step,
            mass=self.mass,
            acc=force/self.mass,
            vel=self.vel+force/self.mass*step
        )
        return state


class ParticleGroup(list):

    def physicalStepCopy(self, step=1):
        '''
        return a copy of all particles with states stepped
        '''
        group = ParticleGroup()
        for ele in self:
            group.append(ele.physicalStepCopy(step))
        return group

    def dump(self):
        '''
        dump to list of data generated by ParticleState.dump()
        '''
        data = []
        for ele in self:
            data.append(ele.dump())
        return data

    def additiveLoad(self, listdata):
        '''
        load from list of data generated by ParticleState.dump()
        '''
        for data in listdata:
            self.append(ParticleState(data=data))


class ParticleContainer():
    '''
    Container maintains history of particle group at one place
    '''

    def __init__(self, maxlength=None):
        self.maxLength = CONTAINER_MAX_LENGTH
        if maxlength != None:
            self.maxLength = maxlength
        self.timeSlice = CONTAINER_TIME_SLICE
        self.groups = []
        self.cptr = 0
        for i in range(self.maxLength):
            self.groups.append(ParticleGroup())
        self.nextGroup = ParticleGroup()

    def currentGroup(self):
        return self.groups[self.cptr]

    def addNextParticle(self, particle):
        self.nextGroup.append(particle)

    def updateToNext(self, period=1):
        delta = int(period / self.timeSlice)
        delta = min(delta, self.maxLength)
        for i in range(delta):
            self.cptr = (self.cptr + 1) % self.maxLength
            self.groups[self.cptr] = self.nextGroup
        self.nextGroup = ParticleGroup()

    def backward(self, period):
        delta = int(period / self.timeSlice)
        delta = min(delta, self.maxLength)
        for i in range(delta):
            self.groups[self.cptr] = ParticleGroup()
            self.cptr = (self.cptr - 1 + self.maxLength) % self.maxLength

    def flush(self):
        for i in range(self.maxLength):
            self.groups[i] = ParticleGroup()

    def detailPrinter(self):
        print("buffered group count: ", len(self.groups))
        group = self.currentGroup()
        print("current group size: {0}".format(len(group)))
        for ele in group:
            print(ele)


def findContainerKeyDefault(particle):
    return particle.pos.copy().toInt().toTuple()


class ParticleFrameManager():
    def __init__(self, getKey=None):
        self.group = ParticleGroup()
        self.containers = {}
        if getKey == None:
            self.getKey = findContainerKeyDefault
        else:
            self.getKey = getKey

    def createContainer(self, key):
        container = ParticleContainer()
        self.containers[key] = container
        return container

    def step(self, physical=True):
        '''
        step forward and distribute particles to containers
        '''
        if physical:
            self.group = self.group.physicalStepCopy()

        for particle in self.group:
            key = self.getKey(particle)
            if not key in self.containers.keys():
                # createContainer(key)
                continue
            self.containers[key].addNextParticle(particle)

        for container in self.containers.values():
            container.updateToNext()

    def backward(self, getPeriod):
        '''
        step backward according to the given function
        getPeriod(key) should return a period of int/float
        '''
        groupNext = ParticleGroup()
        for key, container in self.containers.items():
            period = getPeriod(key)
            if period > 0:
                container.backward(period)
            groupNext.extend(container.currentGroup())
        self.group = groupNext

    def flushAndAddParticles(self, particles):
        for container in self.containers.values():
            container.flush()
        self.group.extend(particles)
        self.step(physical=False)

    def detailPrinter(self):
        for key, container in self.containers.items():
            print(key, end=" ")
            container.detailPrinter()
