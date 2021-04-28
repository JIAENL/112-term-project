from cmu_112_graphics import *
import time
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
        self.survAIsAround = False
        self.survAIsOpening = False
        self.opening = False
        self.isOpened = False
    def getMessage(self):
        return f'Opening Process  {self.percentage}/100%'
class PassableObs(Obstacle):
    def __init__(self, row, col, r, g, b):
        super().__init__(row, col)
        self.color = rgbString(r, g, b)
        self.passable = False
class Char(object):
    def __init__(self, cx, cy):
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
    def __init__(self, cx, cy):
        super().__init__(cx, cy)
        self.rx = 15 # width = 30
        self.ry = 21 # height = 42
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
    def __init__(self, cx, cy):
        super().__init__(cx, cy)
        self.rx = 10 # width = 20
        self.ry = 20 # height = 40
        self.isInjured = False
        self.isDying = False
        self.jailCount = 0
    def getHealthMessage(self):
        if self.isDying: return f'Status: Dying'
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
    # game booleans
    app.t0 = 0
    app.gateOpened = False
    app.gameOver = False
    app.escaped = False
    app.lost = False
    # create characters with init position
    app.charList = []
    app.killer = Killer(app.margin+(23*25-12.5), app.topMargin+(17*25-12.5))
    app.charList.append(app.killer)
    app.survA = Survivor(app.margin+(12*25-12.5), app.topMargin+(10*25-12.5))
    app.charList.append(app.survA)
    app.survB = Survivor(app.margin+(37*25-12.5), app.topMargin+(8*25-12.5))
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

def keyPressed(app, event):
    if app.gameOver: return
    # move survA direction key
    if event.key == 'Left' or event.key == 'Right' or event.key == 'Up'\
        or event.key == 'Down':
        app.survA.t0 = time.time() # record input time
        app.survA.isMoving = True
        if event.key == 'Left':
            move(app, app.survA, -app.survA.speed, 0)
            app.survA.isFacingRight = False
        elif event.key == 'Right':
            move(app, app.survA, app.survA.speed, 0)
            app.survA.isFacingRight = True
        elif event.key == 'Up':
            move(app, app.survA, 0, -app.survA.speed)
        elif event.key == 'Down':
            move(app, app.survA, 0, app.survA.speed)
    # move survB awsd
    if event.key.lower() == 'a' or event.key.lower() == 'd'\
        or event.key.lower() == 'w' or event.key.lower() == 's':
        app.survB.t0 = time.time() # record input time
        app.survB.isMoving = True
        if event.key.lower() == 'a':
            move(app, app.survB, -app.survB.speed, 0)
            app.survB.isFacingRight = False
        elif event.key.lower() == 'd':
            move(app, app.survB, app.survB.speed, 0)
            app.survB.isFacingRight = True
        elif event.key.lower() == 'w':
            move(app, app.survB, 0, -app.survB.speed)
        elif event.key.lower() == 's':
            move(app, app.survB, 0, app.survB.speed)
    # move killer jikl + space
    elif (event.key.lower() == 'j' or event.key.lower() == 'l' or\
        event.key.lower() == 'i' or event.key.lower() == 'k' or\
            event.key == 'Space') and app.killer.isAttacking == False:
        app.killer.t0 = time.time() # record input time
        app.killer.isMoving = True
        if event.key.lower() == 'j':
            move(app, app.killer, -app.killer.speed, 0)
            app.killer.isFacingRight = False
        elif event.key.lower() == 'l':
            move(app, app.killer, app.killer.speed, 0)
            app.killer.isFacingRight = True
        elif event.key.lower() == 'i':
            move(app, app.killer, 0, -app.killer.speed)
        elif event.key.lower() == 'k':
            move(app, app.killer, 0, app.killer.speed)
        elif event.key == 'Space':
            app.killer.isAttacking = True
            # app.killer.isMoving = False # attack animation speeds up a bit
    for chest in app.chestList: # doesn't distinguish
        if chest.survAIsAround and (event.key.lower() == 'f'):
            app.t0 = time.time()
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
    if app.chest1.isOpened or app.chest2.isOpened: # check game win
        app.mainMessage = 'The Gate Has Opened'
        app.gateOpened = True
        for gateCell in app.gate:
            gateCell.passable = True
            if rA == gateCell.row and cA == gateCell.col:
                app.gameOver = True
                app.escaped = True
                app.mainMessage = 'You Escaped!'
    elif not checkIfAround(rA, cA, app.chest1.row, app.chest1.col) and\
        not checkIfAround(rA, cA, app.chest2.row, app.chest2.col): # do for either chest
        app.chest1.survAIsAround = False
        app.chest1.survAIsOpening = False
        app.chest2.survAIsAround = False
        app.chest2.survAIsOpening = False
        app.mainMessage = 'Press Arrow Keys To Move'
    else: # open chest
        for chest in app.chestList: # do for evey chest
            if checkIfAround(rA, cA, chest.row, chest.col) and\
                not chest.survAIsOpening:
                chest.survAIsAround = True
                app.mainMessage = 'Press F to Open the Chest'
            elif chest.survAIsOpening and time.time()-app.t0 >= 0.5:
                app.t0 = time.time()
                chest.percentage += 5
                if chest.percentage >= 100:
                    chest.isOpened = True

def timerFired(app):
    if app.gameOver: return
    generateCharSprites(app) # animation
    chestsAndEscaping(app) # open chests and check for escape (win)

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
    for char in app.charList:
        drawChar(app, canvas, char)
    drawWalls(app, canvas)
    drawChests(app, canvas)
    # draw25Grids(app, canvas)
    # draw50Grids(app, canvas)

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