from cmu_112_graphics import *
import A_star_search as AS
import time, copy
#################################################
# helpers
#################################################
def rgbString(r, g, b): return f'#{r:02x}{g:02x}{b:02x}' # from: https://www.cs.cmu.edu/~112/notes/notes-graphics.html
def getCellBounds(margin, topMargin, row, col):
    x1 = margin + col*50
    x2 = margin + (col+1)*50
    y1 = topMargin + row*50
    y2 = topMargin + (row+1)*50
    return x1, y1, x2, y2
def getRowCol(margin, topMargin, x, y): # check boundary? nah
    col = (x - margin)//50
    row = (y - topMargin)//50
    return int(row), int(col)
def gridDist(r1, c1, r2, c2):
    return abs(r1-r2) + abs(c1-c2)
def checkIfAround(r1, c1, r2, c2):
    if gridDist(r1, c1, r2, c2) == 1: return True
    elif abs(r1-r2) == 1 and abs(c1-c2) == 1: return True
    return False
def checkInDist(r1, c1, r2, c2, dist):
    return gridDist(r1, c1, r2, c2) <= dist
def getFirstStep(route): # pop
    stepList = []
    for i in range(4):
        stepList.append(route[0])
    route.pop(0)
    return stepList
def absToRelPath(app, pathInRC):
    result = []
    for i in range(1, len(pathInRC)):
        r = pathInRC[i][0] - pathInRC[i-1][0]
        c = pathInRC[i][1] - pathInRC[i-1][1]
        result.append([r,c])
    return result
#################################################
# create classes
#################################################
class Obstacle(object):
    def __init__(self, row, col):
        self.row = row
        self.col = col
        x1, y1, x2, y2 = getCellBounds(20, 80, row, col)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
class Chest(Obstacle):
    def __init__(self, row, col):
        super().__init__(row, col)
        closedImage = Image.open('closedChest.png')
        self.closedImage = closedImage.resize((50, 50))
        openedImage = Image.open('openedChest.png')
        self.openedImage = openedImage.resize((50, 50))
        self.cx = (self.x1+self.x2)/2
        self.cy = (self.y1+self.x2)/2
        self.percentage = 0
        self.progPerSec = 5
        self.survAIsAround = False
        self.survAIsOpening = False
        self.survBIsOpening = False
        self.opening = False
        self.isOpened = False
    def getMessage(self):
        return f'Opening Process  {self.percentage}%'
class PassableObs(Obstacle):
    def __init__(self, row, col, r, g, b):
        super().__init__(row, col)
        self.color = rgbString(r, g, b)
        self.passable = False
class Char(object):
    def __init__(self, name, cx, cy):
        self.name = name
        self.cx = cx
        self.cy = cy
        self.speed = 12.5
        self.t0 = 0
        self.isMoving = False
        self.isAttacking = False # stay here cuz draw fcn loop thru char
        self.isFacingRight = True
    def makeSprites(self, file, x1, y1, x2, y2, numOfFrames, upDown, isKiller):
        spritestrip = Image.open(file)
        self.sprites = []
        for i in range(numOfFrames):
            if upDown: # y1 == y2, set x1 x2 manually
                sprite = spritestrip.crop((x1, y1*i, x2, y2*(i+1)))
            else: # x1 == x2, set y1 y2 manually
                sprite = spritestrip.crop((x1*i, y1, x2*(i+1), y2))
            if isKiller: # scale killer
                sprite = sprite.resize((60, 60))
            self.sprites.append(sprite)
        self.spriteCounter = 0
class Killer(Char):
    def __init__(self, name, cx, cy):
        super().__init__(name, cx, cy)
        self.rx = 15 # width = 30
        self.ry = 21 # height = 42
        self.detectDist = 5
        self.target = None
        self.isPatrolling = False
        self.isDraggin = False
        self.isPaused = False # brief pause after attack
        self.mutablePRoute = [(0,1), (0,1), (0,1), (0,1), (0,1),
                            (-1,0), (-1,0), (-1,0), (-1,0), (-1,0), (-1,0),
                            (0,-1), (0,-1), (0,-1), (0,-1), (0,-1),
                            (1,0), (1,0),
                            (0,-1), (0,-1),
                            (-1,0), (-1,0),
                            (0,-1), (0,-1),
                            (1,0),
                            (0,-1),
                            (1,0), (1,0), (1,0), (1,0), (1,0), (1,0),
                            (0,1), (0,1), (0,1), (0,1), (0,1),
                            (-1,0)]
    def makeAttackSprites(self, file, x1, y1, x2, y2, numOfFrames, upDown):
        # attack animation method only for killer
        spritestrip = Image.open(file)
        self.attackSprites = []
        for i in range(numOfFrames):
            if upDown:
                sprite = spritestrip.crop((x1, y1*i, x2, y2*(i+1)))
            else:
                sprite = spritestrip.crop((x1*i, y1, x2*(i+1), y2))
            sprite = sprite.resize((80, 60))
            self.attackSprites.append(sprite)
        self.attackSpriteCounter = 0
class Survivor(Char):
    def __init__(self, name, cx, cy):
        super().__init__(name, cx, cy)
        self.rx = 10 # width = 20
        self.ry = 20 # height = 40
        self.isInjured = False
        self.isDying = False
        self.isDead = False
        self.jailCount = 0
        self.inJail = False
    def getHealthMessage(self):
        if self.isDead: return 'Status: Dead'
        elif self.isDying: return 'Status: Dying'
        elif self.isInjured: return 'Status: Injured'
        else: return 'Status: Healthy'
    def getJailCountMessage(self):
        return f'Jail Count: {self.jailCount}/2'
#################################################
# start app
#################################################
def appStarted(app):
    # basic display
    app.topMargin = 80
    app.margin = 20
    app.mainMessage = 'Press Arrow Keys To Move'
    # game settings (partial)
    app.At0 = 0
    app.Bt0 = 0
    app.chaseT0 = 0
    app.dragT0 = 0
    app.patrolT0 = 0
    app.jailT0 = 0
    app.inJailTime = 2 # pop out after __ seconds
    app.pauseTimer = 0
    app.killerSearchInterval = 3
    # search related (vars used in A* lab)
    app.patrolRoute = [(0,1), (0,1), (0,1), (0,1), (0,1),
                       (-1,0), (-1,0), (-1,0), (-1,0), (-1,0), (-1,0),
                       (0,-1), (0,-1), (0,-1), (0,-1), (0,-1),
                       (1,0), (1,0),
                       (0,-1), (0,-1),
                       (-1,0), (-1,0),
                       (0,-1), (0,-1),
                       (1,0),
                       (0,-1),
                       (1,0), (1,0), (1,0), (1,0), (1,0), (1,0),
                       (0,1), (0,1), (0,1), (0,1), (0,1),
                       (-1,0)]
    app.map = [[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
               [0,1,0,0,0,0,0,0,0,0,1,0,1,1,1,1,1,1,0,0,1,0,1,1],
               [0,0,1,1,1,1,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0],
               [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0],
               [1,1,1,1,1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
               [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,1,1,1,1,1,1],
               [0,0,0,1,0,0,0,0,1,0,0,1,1,0,0,1,0,0,0,0,0,0,0,0],
               [0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0],
               [0,0,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
               [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
               [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,1,0,0,1,0,0,0,0]]
    app.start = []
    app.end = []
    app.cost = 1
    app.stepList = []
    # game booleans
    app.gateOpened = False
    app.gameOver = False
    app.escaped = False
    app.lost = False
    # create characters with init position
    app.charList = []
    app.killer = Killer('killer', app.margin+(23*25), app.topMargin+(17*25))
    app.charList.append(app.killer)
    app.survA = Survivor('survA', app.margin+(11*25), app.topMargin+(9*25))
    app.charList.append(app.survA)
    app.survB = Survivor('survB', app.margin+(37*25), app.topMargin+(7*25))
    app.charList.append(app.survB)
    # create walking animation sprite
    # parameters: x1, y1, x2, y2, frame, upDown, isKiller
    app.killer.makeSprites('move without FX.png',
        10, 26, 40, 26, 6, True, True)
    app.survA.makeSprites('blueKanakoRun.png',
        32, 15, 32, 64, 4, False, False)
    app.survB.makeSprites('yellowKanakoRun.png',
        32, 15, 32, 64, 4, False, False)
    # create attacking animation sprite
    app.killer.makeAttackSprites('shoot with FX.png',
        10, 26, 50, 26, 4, True)
    # create obstacles, parameters: x1, y1, x2, y2
    app.obsList = []
    app.passableObs = []
    # wall at center {row:(6) col: (11,12)}
    app.obsList += [Obstacle(6,11), Obstacle(6,12)]
    # walls in area A (name has same order as quadrants)
    #   A1 {row:(3,4,5,6) col: (15)}
    #   A2 {row:(1) col: (12,13,14,15,16,17)}
    #   A3 {row:(1,2,3) col:(20)} 
    app.obsList += [Obstacle(3,15),Obstacle(4,15),Obstacle(5,15),Obstacle(6,15)]
    app.obsList += [Obstacle(1,12),Obstacle(1,13),Obstacle(1,14),Obstacle(1,15),
        Obstacle(1,16),Obstacle(1,17)]
    app.obsList += [Obstacle(1,20),Obstacle(2,20),Obstacle(3,20)]
    # walls in area B
    #   B1 {row:(0) col:(6)} 
    #   B2 {row:(2) col:(2,3,4,5,6)}
    #   B3 {row:(1,2,3) col:(10)}
    app.obsList += [Obstacle(0,6)]
    app.obsList += [Obstacle(2,2),Obstacle(2,3),Obstacle(2,4),Obstacle(2,5),
        Obstacle(2,6)]
    app.obsList += [Obstacle(1,10),Obstacle(2,10),Obstacle(3,10)]
    # walls in area C
    #   C1 {row:(8) col:(2,3,4,5)} 
    #   C2 {row:(8) col:(7,8)} 
    #   C3 {row:(4,5,6,7) col:(8)} 
    #   C4 {row:(6,7,8) col:(3)} 
    #   C5 {row:(4) col:(0,1,2,3,4)} 
    app.obsList += [Obstacle(8,2),Obstacle(8,3),Obstacle(8,4),Obstacle(8,5)]
    app.obsList += [Obstacle(8,7),Obstacle(8,8)]
    app.obsList += [Obstacle(4,8),Obstacle(5,8),Obstacle(6,8),Obstacle(7,8)]
    app.obsList += [Obstacle(6,3),Obstacle(7,3),Obstacle(8,3)]
    app.obsList += [Obstacle(4,0),Obstacle(4,1),Obstacle(4,2),
        Obstacle(4,3),Obstacle(4,4)]
    # walls in area D
    #   D1 {row:(8) col:(18)} 
    #   D2 {row:(10) col:(19)} 
    #   D3 {row:(5) col:(18,19,20,21,22,23)} 
    #   D4 {row:(7) col:(18,19,20,21,22)} 
    #   D5 {row:(9,10) col:(16)} 
    app.obsList += [Obstacle(8,18)]
    app.obsList += [Obstacle(10,19)]
    app.obsList += [Obstacle(5,18),Obstacle(5,19),Obstacle(5,20),
        Obstacle(5,21),Obstacle(5,22),Obstacle(5,23)]
    app.obsList += [Obstacle(7,18),Obstacle(7,19),Obstacle(7,20),
        Obstacle(7,21),Obstacle(7,22)]
    app.obsList += [Obstacle(9,16),Obstacle(10,16)]
    # passable obstacles: 2d list [[jail], [gate]]
    app.jail = []
    app.gate = []
    #   jail {row:(0,1) col:(22,23) rgb:(161, 66, 100)} 
    #   gate {row:(10) col:(10,11,12,13,14) rgb:(160, 191, 115)}
    app.jail += [PassableObs(0,22, 161, 66, 100),
        PassableObs(0,23, 161, 66, 100),PassableObs(1,22, 161, 66, 100),
        PassableObs(1,23, 161, 66, 100)]
    app.gate += [PassableObs(10,10, 160, 191, 115),
        PassableObs(10,11, 160, 191, 115),PassableObs(10,12, 160, 191, 115),
        PassableObs(10,13, 160, 191, 115),PassableObs(10,14, 160, 191, 115)]
    app.passableObs += [app.jail, app.gate]
    # chest: append in obsList
    app.chest1 = Chest(1,1)
    app.chest2 = Chest(9,22)
    app.chestList = [app.chest1, app.chest2]
    app.obsList += [app.chest1, app.chest2]

def inObstacle(app, obs, x, y, char): # used in move fcn
    # change to obs.x1+char.rx <= x <= obs.x2-char.rx
    return (obs.x1 <= x <= obs.x2 or obs.x1 <= x - char.rx <= obs.x2 or\
        obs.x1 <= x + char.rx <= obs.x2) and (obs.y1 <= y <= obs.y2 or\
            obs.y1 <= y - char.ry <= obs.y2 or\
                obs.y1 <= y + char.ry <= obs.y2)

def move(app, char, dx, dy): # move when valid
    char.isMoving = True
    char.cx += dx
    char.cy += dy
    for obs in app.obsList: # check if char in normal obstacle
        if inObstacle(app, obs, char.cx, char.cy, char):
            char.cx -= dx
            char.cy -= dy
    for lst in app.passableObs: # check if char in passable obstacle (2d list)
        for obs in lst:
            if inObstacle(app,obs,char.cx,char.cy,char) and (not obs.passable):
                char.cx -= dx
                char.cy -= dy
    if char.cx < char.rx + app.margin \
        or char.cx > app.width - char.rx - app.margin: # check x bounds
        char.cx -= dx
    elif char.cy < char.ry + app.topMargin \
        or char.cy > app.height - char.ry - app.margin: # check y bounds
        char.cy -= dy
    if dx > 0: char.isFacingRight = True # for animation sprites
    elif dx < 0: char.isFacingRight = False

def cheatKeys(app, event):
    if event.key.lower() == 'r': # can restart and any time
        appStarted(app)
    if event.key == '1': # open gate by opening chest 1
        app.chest1.percentage = 100
    if event.key == '3': # teleport surv A to chest 1
        app.survA.cx = app.margin + 75
        app.survA.cy = app.topMargin + 125
    if event.key == '4': # teleport surv A to chest 2
        app.survA.cx = app.width - app.margin - 75 
        app.survA.cy = app.topMargin + 425
    if event.key == '5': # teleport surv B to chest 1
        app.survB.cx = app.margin + 75
        app.survB.cy = app.topMargin + 125
    if event.key == '6': # teleport surv B to chest 2
        app.survB.cx = app.width - app.margin - 75 
        app.survB.cy = app.topMargin + 425
    if event.key == 'j':
        app.survA.isDying = not app.survA.isDying

def keyPressed(app, event):
    cheatKeys(app, event)
    if app.gameOver: return
    # move survA direction key
    if (event.key == 'Left' or event.key == 'Right' or event.key == 'Up'\
        or event.key == 'Down') and not app.survA.isDying:
        app.survA.t0 = time.time() # record input time
        if event.key == 'Left':
            move(app, app.survA, -app.survA.speed, 0)
        elif event.key == 'Right':
            move(app, app.survA, app.survA.speed, 0)
        elif event.key == 'Up':
            move(app, app.survA, 0, -app.survA.speed)
        elif event.key == 'Down':
            move(app, app.survA, 0, app.survA.speed)
    # move survB awsd
    if event.key.lower() == 'a' or event.key.lower() == 'd'\
        or event.key.lower() == 'w' or event.key.lower() == 's':
        app.survB.t0 = time.time() # record input time
        if event.key.lower() == 'a':
            move(app, app.survB, -app.survB.speed, 0)
        elif event.key.lower() == 'd':
            move(app, app.survB, app.survB.speed, 0)
        elif event.key.lower() == 'w':
            move(app, app.survB, 0, -app.survB.speed)
        elif event.key.lower() == 's':
            move(app, app.survB, 0, app.survB.speed)
    # move killer jikl + space
    # elif (event.key.lower() == 'j' or event.key.lower() == 'l' or\
    #     event.key.lower() == 'i' or event.key.lower() == 'k' or\
    #         event.key == 'Space') and app.killer.isAttacking == False:
    #     app.killer.t0 = time.time() # record input time
    #     if event.key.lower() == 'j':
    #         move(app, app.killer, -app.killer.speed, 0)
    #     elif event.key.lower() == 'l':
    #         move(app, app.killer, app.killer.speed, 0)
    #     elif event.key.lower() == 'i':
    #         move(app, app.killer, 0, -app.killer.speed)
    #     elif event.key.lower() == 'k':
    #         move(app, app.killer, 0, app.killer.speed)
    #     elif event.key == 'Space':
    #         app.killer.isAttacking = True
    # survA opens chest
    for chest in app.chestList: # doesn't distinguish
        if chest.survAIsAround and (event.key.lower() == 'f'):
            app.At0 = time.time()
            chest.survAIsOpening = True
            app.mainMessage = 'Opening...'

def generateCharSprites(app):
    for char in app.charList:
        for obs in app.obsList: # if accidently enter obstacle then pop out
            if inObstacle(app, obs, char.cx, char.cy, char):
                char.cx = app.width - app.margin - 50
                char.cy = app.topMargin + 150
        # missing a part to get out of jail
        if char.isMoving: # no input for a while --> status = not moving
            char.spriteCounter = (1 + char.spriteCounter) % len(char.sprites)
            if time.time() - char.t0 >= 0.1:
                char.isMoving = False
        elif char.isAttacking: # only do animation once per attack
            char.attackSpriteCounter = (1 + char.attackSpriteCounter)
            if char.attackSpriteCounter >= len(char.attackSprites):
                char.isAttacking = False
                char.attackSpriteCounter = 0
        else: # not moving --> only show first frame (idle char)
            char.spriteCounter = 0

def chestsAndEscaping(app):
    rA, cA = getRowCol(app.margin, app.topMargin, app.survA.cx, app.survA.cy)
    rB, cB = getRowCol(app.margin, app.topMargin, app.survB.cx, app.survB.cy)
    if app.gateOpened:
        for gateCell in app.gate:
            if rA == gateCell.row and cA == gateCell.col:
                    app.gameOver = True
                    app.escaped = True
                    app.mainMessage = 'You Escaped!'
    else: # when gate not opened open chest and check if it's opened
        if not checkIfAround(rA, cA, app.chest1.row, app.chest1.col) and\
            not checkIfAround(rA, cA, app.chest2.row, app.chest2.col): # for surv A message
            app.chest1.survAIsAround = False
            app.chest1.survAIsOpening = False
            app.chest2.survAIsAround = False
            app.chest2.survAIsOpening = False
            app.mainMessage = 'Press Arrow Keys To Move'
        else: # surv A progress
            for chest in app.chestList:
                if checkIfAround(rA, cA, chest.row, chest.col) and\
                    not chest.survAIsOpening:
                    chest.survAIsAround = True
                    app.mainMessage = 'Press F to Open the Chest'
                elif chest.survAIsOpening and time.time()-app.At0 >= 0.5:
                    app.At0 = time.time()
                    chest.percentage += chest.progPerSec
        for chest in app.chestList: # surv B progress
            if checkIfAround(rB, cB, chest.row, chest.col) and\
                not chest.survBIsOpening: # around and not opening
                app.Bt0 = time.time()
                chest.survBIsOpening = True
            elif not checkIfAround(rB, cB, chest.row, chest.col): # not around
                chest.survBIsOpening = False
            elif chest.survBIsOpening and time.time()-app.Bt0 >= 0.5: # increase progress
                app.Bt0 = time.time()
                chest.percentage += chest.progPerSec
        for chest in app.chestList:# check chest percentage
            if chest.percentage >= 100: # open the gate
                        chest.percentage = 100
                        chest.isOpened = True
                        app.gateOpened = True
                        app.mainMessage = 'The Gate Has Opened'
                        for gateCell in app.gate: # make gate passable
                            gateCell.passable = True

def patrol(app):
    dr, dc = app.stepList.pop(0)
    move(app, app.killer, dc*app.killer.speed, dr*app.killer.speed)
    if len(app.stepList) == 0:
        if len(app.killer.mutablePRoute) == 0:
            app.killer.mutablePRoute = copy.deepcopy(app.patrolRoute) # second cycle
        app.stepList = getFirstStep(app.killer.mutablePRoute) # move to next cell

def chase(app):
    dr, dc = app.stepList.pop(0)
    move(app, app.killer, dc*app.killer.speed, dr*app.killer.speed)
    if len(app.stepList) == 0:
        if len(app.killer.mutablePRoute) == 0: # re-search
            rK, cK = getRowCol(app.margin, app.topMargin, app.killer.cx, app.killer.cy)
            rT, cT = getRowCol(app.margin, app.topMargin, app.killer.target.cx, app.killer.target.cy)
            if rK == rT and cK == cT: return # if finish chasing then return
            app.start = [rK, cK]
            app.end = [rT, cT]
            pathInRC = AS.search(app, app.map, app.cost, app.start, app.end)
            app.killer.mutablePRoute = absToRelPath(app, pathInRC)
        app.stepList = getFirstStep(app.killer.mutablePRoute) # move to next cell

def bringToJail(app):
    dr, dc = app.stepList.pop(0)
    move(app, app.killer, dc*app.killer.speed, dr*app.killer.speed)
    move(app, app.killer.target, dc*app.killer.speed, dr*app.killer.speed)
    if len(app.stepList) == 0:
        if len(app.killer.mutablePRoute) == 0: # arrived at jail
            app.killer.target.inJail = True
            app.killer.target.cx = app.width - app.margin - 50 # put char in jail
            app.killer.target.cy = app.topMargin + 50
            app.killer.target.jailCount += 1
            if app.killer.target.jailCount == 2 and app.killer.target.name == 'survA': # if survA in jail twice
                app.survA.isDead = True
                app.gameOver = True
                app.lost = True
                return
            elif app.killer.target.jailCount == 2: # surv B dies --> disappear
                app.survB.isDead = True
                app.charList.remove(app.survB)
                return
            app.killer.target.isDying = False
            app.jailT0 = time.time()
            app.killer.isDragging = False
            app.killer.target = None # find new target
            return
        app.stepList = getFirstStep(app.killer.mutablePRoute) # move to next cell

def killerAI(app):
    # if just after an attack, killer stops
    if app.killer.isPaused and time.time() - app.pauseTimer <= 3:
        return # killer pauses just after an attack
    elif app.killer.isPaused and time.time() - app.pauseTimer > 3:
        app.killer.isPaused = False
    
    rA, cA = getRowCol(app.margin, app.topMargin, app.survA.cx, app.survA.cy)
    rB, cB = getRowCol(app.margin, app.topMargin, app.survB.cx, app.survB.cy)
    rK, cK = getRowCol(app.margin, app.topMargin, app.killer.cx, app.killer.cy)
    # if no alive survivors around
    if (not checkInDist(rA, cA, rK, cK, app.killer.detectDist) and\
        not checkInDist(rB, cB, rK, cK, app.killer.detectDist)) or\
        (app.killer.isPatrolling and len(app.stepList) != 4) or\
        (not checkInDist(rB, cB, rK, cK, app.killer.detectDist) and app.survA.inJail) or\
        (not checkInDist(rA, cA, rK, cK, app.killer.detectDist) and app.survB.inJail):
        # 1. both not around
        # 2. is not at the center of a patrolling cell
        # 3. only A is around but in jail
        # 4. only B is around but in jail
        app.killer.target = None
        if app.killer.isPatrolling and time.time()-app.patrolT0 > 0.1\
            and not app.killer.isAttacking: # need to finish 4 steps before detecting target
            patrol(app) # take step of patrolling (1/4 cell)
        elif rK == 8 and cK == 11 and not app.killer.isPatrolling: # start patrolling
            app.patrolT0 = time.time()
            app.killer.isPatrolling = True
            app.killer.mutablePRoute = copy.deepcopy(app.patrolRoute) # initialize patrol route
            app.stepList = getFirstStep(app.killer.mutablePRoute)
        elif rK != 8 or cK != 11: # write this after chasing alg (move killer to start point)
            app.start = [rK, cK]
            app.end = [8, 11]
            # do search
            # next move = only take the first step
            # move killer along next move
    # if have survivors around and killer finished moving
    else:
        app.killer.isPatrolling = False
        if app.killer.target != None and app.killer.target.isDying: # have dying target
            if app.killer.isDragging and time.time() - app.dragT0 >= 0.1 and\
                not app.killer.isAttacking and len(app.stepList) != 0: # bring char to jail
                bringToJail(app)
        elif app.killer.target != None: # if have target that's not dying
            rT, cT = getRowCol(app.margin, app.topMargin, app.killer.target.cx, app.killer.target.cy)
            if checkInDist(rA, cA, rK, cK, app.killer.detectDist) and\
                checkInDist(rB, cB, rK, cK, app.killer.detectDist) and\
                len(app.stepList) == 4 and\
                (rK!=rA and rK!=rB and cK!=cA and cK!=cB): # both then re-select (not in same cell)
                app.killer.target = None
            elif rK == rT and cK == cT and len(app.stepList) == 0: # attack!!!
                app.killer.isAttacking = True 
                if not app.killer.target.isInjured:
                    app.killer.target.isInjured = True
                    app.killer.isPaused = True
                    app.pauseTimer = time.time()
                else:
                    app.killer.target.isInjured = False
                    app.killer.target.isDying = True
                    app.dragT0 = time.time()
                    app.killer.isDragging = True
                    app.end = [2, 23] # start making the way to jail
                    app.start = [rK, cK]
                    pathInRC = AS.search(app, app.map,
                        app.cost, app.start,app.end)
                    app.killer.mutablePRoute = absToRelPath(app, pathInRC) # make absolute path to relative
                    app.stepList = getFirstStep(app.killer.mutablePRoute)
                    print(app.killer.mutablePRoute)
            elif time.time() - app.chaseT0 >= 0.1: # chase!!!
                chase(app)
        
        elif app.killer.target == None: # no current target
            if checkInDist(rA, cA, rK, cK, app.killer.detectDist) and\
                checkInDist(rB, cB, rK, cK, app.killer.detectDist): # both
                if gridDist(rA, cA, rK, cK) <= gridDist(rB, cB, rK, cK) and\
                    not app.survA.inJail:
                    app.killer.target = app.survA
                    app.end = [rA, cA]
                elif gridDist(rA, cA, rK, cK) > gridDist(rB, cB, rK, cK) and\
                    not app.survB.inJail:
                    app.killer.target = app.survB
                    app.end = [rB, cB]
            elif checkInDist(rA, cA, rK, cK, app.killer.detectDist) and\
                not app.survA.inJail: # A around and not in jail
                app.killer.target = app.survA
                app.end = [rA, cA]
            elif checkInDist(rB, cB, rK, cK, app.killer.detectDist) and\
                not app.survB.inJail: # B around and not in jail
                app.killer.target = app.survB
                app.end = [rB, cB]
            app.chaseT0 = time.time()
            app.start = [rK, cK]
            pathInRC = AS.search(app, app.map, app.cost, app.start, app.end)
            app.killer.mutablePRoute = absToRelPath(app, pathInRC) # make absolute path to relative
            app.stepList = getFirstStep(app.killer.mutablePRoute)

def jailCountDown(app):
    if app.survA.inJail and time.time()-app.jailT0 >= app.inJailTime:
        app.survA.inJail = False
        app.survA.cx = app.width - app.margin - 125
        app.survA.cy = app.topMargin + 25
    elif app.survB.inJail and time.time()-app.jailT0 >= app.inJailTime:
        app.survB.inJail = False
        app.survB.cx = app.width - app.margin - 125
        app.survB.cy = app.topMargin + 25
    
def timerFired(app):
    if app.gameOver: return
    jailCountDown(app)
    generateCharSprites(app) # animation
    chestsAndEscaping(app) # open chests and check for escape (win)
    killerAI(app)

#################################################
# graphics
#################################################
def drawChar(app, canvas, char):
    # adapted from: https://www.cs.cmu.edu/~112/notes/notes-animations-part4.html#loadImageUsingUrl
    if char.isFacingRight:
        if char.isAttacking:
            sprite = char.attackSprites[char.attackSpriteCounter]
            canvas.create_image(char.cx, char.cy,
                image=ImageTk.PhotoImage(sprite))
        else:
            sprite = char.sprites[char.spriteCounter]
            canvas.create_image(char.cx, char.cy,
                image=ImageTk.PhotoImage(sprite))
    else:
        if char.isAttacking:
            sprite = char.attackSprites[char.attackSpriteCounter].\
                transpose(Image.FLIP_LEFT_RIGHT)
            canvas.create_image(char.cx, char.cy,
                image=ImageTk.PhotoImage(sprite))
        else:
            sprite = char.sprites[char.spriteCounter].\
                transpose(Image.FLIP_LEFT_RIGHT)
            canvas.create_image(char.cx, char.cy,
                image=ImageTk.PhotoImage(sprite))

def drawWalls(app, canvas):
    for obs in app.obsList:
        canvas.create_rectangle(obs.x1, obs.y1,
            obs.x2, obs.y2, fill='grey', outline='grey')

def drawPassableObs(app, canvas):
    for lst in app.passableObs:
        for obs in lst:
            canvas.create_rectangle(obs.x1, obs.y1,
                obs.x2, obs.y2, fill=obs.color, outline=obs.color)

def drawChests(app, canvas):
    # adapted from: https://www.cs.cmu.edu/~112/notes/notes-animations-part4.html#loadImageUsingUrl
    for chest in app.chestList:
        if chest.percentage >= 100:
            canvas.create_image(app.margin+25+chest.col*50,
                app.topMargin+25+chest.row*50,
                image=ImageTk.PhotoImage(chest.openedImage))
        elif chest.percentage < 100:
            canvas.create_image(app.margin+25+chest.col*50,
                app.topMargin+25+chest.row*50,
                image=ImageTk.PhotoImage(chest.closedImage))

def drawBasicScreen(app, canvas):
    # main message and screen
    canvas.create_rectangle(app.margin, app.topMargin,
        app.width - app.margin, app.height - app.margin, outline = 'black')
    canvas.create_text(app.width//2, app.topMargin//2,
            text=app.mainMessage, font='Ariel 20')
    # chest info
    canvas.create_text(app.margin, app.topMargin//4, anchor='w',
        text=f'Chest 1 {app.chest1.getMessage()}', font='Ariel 20') # chest 1
    canvas.create_text(app.margin, app.topMargin*(3/4), anchor='w',
        text=f'Chest 2 {app.chest2.getMessage()}', font='Ariel 20') # chest 2
    # survivor A status
    canvas.create_text(app.width-13*app.margin,app.topMargin//4,
        anchor='e', text='P1', font='Ariel 15') 
    canvas.create_text(app.width-11*app.margin,app.topMargin*(2/4),
        anchor='e', text=app.survA.getHealthMessage(), font='Ariel 15') 
    canvas.create_text(app.width-11*app.margin,app.topMargin*(3/4),
        anchor='e', text=app.survA.getJailCountMessage(), font='Ariel 15') 
    # survivor B status
    canvas.create_text(app.width-3*app.margin,app.topMargin//4,
        anchor='e', text='P2', font='Ariel 15') 
    canvas.create_text(app.width-1*app.margin,app.topMargin*(2/4),
        anchor='e', text=app.survB.getHealthMessage(), font='Ariel 15') 
    canvas.create_text(app.width-1*app.margin,app.topMargin*(3/4),
        anchor='e', text=app.survB.getJailCountMessage(), font='Ariel 15') 

def draw25Grids(app, canvas):
    for row in range(23):
        for col in range(49):
            canvas.create_rectangle(app.margin+col*25,
                app.topMargin+row*25, app.margin+(col+1)*25,
                app.topMargin+(row+1)*25)

def draw50Grids(app, canvas):
    for row in range(11):
        for col in range(24):
            canvas.create_rectangle(app.margin+col*50,
                app.topMargin+row*50, app.margin+(col+1)*50,
                app.topMargin+(row+1)*50)

def redrawAll(app, canvas):
    drawBasicScreen(app, canvas)
    drawPassableObs(app, canvas)
    drawWalls(app, canvas)
    for char in app.charList:
        drawChar(app, canvas, char)
    drawChests(app, canvas)
    # need a draw path fcn

    # draw25Grids(app, canvas)
    draw50Grids(app, canvas)

#################################################
# main
#################################################
runApp(width=1240, height=650)
# 550*1200 ==GRIDS==> 11*24 (row, col)
'''
Assets Cited:
https://penusbmic.itch.io/sci-fi-character-pack-12
https://maytch.itch.io/free-32x64-kanako-platformer-character-sprite-set
'''