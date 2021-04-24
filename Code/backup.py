from cmu_112_graphics import *
import time
#################################################
# helpers
#################################################
# from: https://www.cs.cmu.edu/~112/notes/notes-graphics.html
def rgbString(r, g, b): return f'#{r:02x}{g:02x}{b:02x}'
def getCellBounds(app, row, col):
    x1 = app.margin + col*50
    x2 = app.margin + (col+1)*50
    y1 = app.topMargin + row*50
    y2 = app.topMargin + (row+1)*50
    return x1, y1, x2, y2
#################################################
# create classes
#################################################
class Obstacle(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        # add self.grid = row, col
class Chest(Obstacle):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, x2, y2)
        closedImage = Image.open('closedChest.png')
        self.closedImage = closedImage.resize((50, 50))
        openedImage = Image.open('openedChest.png')
        self.openedImage = openedImage.resize((50, 50))
        self.cx = (x1+x2)/2
        self.cy = (y1+x2)/2
        self.percentage = 0
class PassableObs(Obstacle):
    def __init__(self, x1, y1, x2, y2, r, g, b):
        super().__init__(x1, y1, x2, y2)
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
    # create characters with init position
    app.charList = []
    app.killer = Killer(app.margin+(23*25-12.5), app.topMargin+(17*25-12.5))
    app.charList.append(app.killer)
    app.survA = Survivor(app.margin+(12*25-12.5), app.topMargin+(10*25-12.5))
    app.charList.append(app.survA)
    app.survB = Survivor(app.margin+(13*25-12.5), app.topMargin+(16*25-12.5))
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
    # wall at center
    app.center = Obstacle(app.margin + (22*25),
        app.topMargin + (12*25), app.margin + (26*25), app.topMargin + (14*25))
    app.obsList.append(app.center)
    # walls in area A (name has same order as quadrants)
    app.wallA1 = Obstacle(app.width-app.margin-450, app.height-app.margin-400,
        app.width-app.margin-400, app.height-app.margin-200)
    app.obsList.append(app.wallA1)
    app.wallA2 = Obstacle(app.width-app.margin-600, app.topMargin + 50,
        app.width-app.margin-300, app.topMargin+100)
    app.obsList.append(app.wallA2)
    app.wallA3 = Obstacle(app.width-app.margin-200, app.topMargin + 50,
        app.width-app.margin-150, app.topMargin+200)
    app.obsList.append(app.wallA3)
    # walls in area B
    app.wallB1 = Obstacle(app.margin+300, app.topMargin,
        app.margin+350, app.topMargin+50)
    app.obsList.append(app.wallB1)
    app.wallB2 = Obstacle(app.margin + 100, app.topMargin + 100,
        app.margin+350, app.topMargin + 150)
    app.obsList.append(app.wallB2)
    app.wallB3 = Obstacle(app.margin+500, app.topMargin+50,
        app.margin+550, app.topMargin+200)
    app.obsList.append(app.wallB3)
    # walls in area C
    app.wallC1 = Obstacle(app.margin+100, app.height-app.margin-150,
        app.margin+300, app.height-app.margin-100)
    app.obsList.append(app.wallC1)
    app.wallC2 = Obstacle(app.margin+350, app.height-app.margin-150,
        app.margin+450, app.height-app.margin-100)
    app.obsList.append(app.wallC2)
    app.wallC3 = Obstacle(app.margin+400, app.height-app.margin-350,
        app.margin+450, app.height-app.margin-150)
    app.obsList.append(app.wallC3)
    app.wallC4 = Obstacle(app.margin+150, app.height-app.margin-250,
        app.margin+200, app.height-app.margin-150)
    app.obsList.append(app.wallC4)
    app.wallC5 = Obstacle(app.margin, app.height-app.margin-350,
        app.margin+250, app.height-app.margin-300)
    app.obsList.append(app.wallC5)
    # walls in area D
    app.wallD1 = Obstacle(app.width-app.margin-300, app.height-app.margin-200,
        app.width-app.margin-250, app.height-app.margin-100)
    app.obsList.append(app.wallD1)
    app.wallD2 = Obstacle(app.width-app.margin-250, app.height-app.margin-50,
        app.width-app.margin-200, app.height-app.margin)
    app.obsList.append(app.wallD2)
    app.wallD3 = Obstacle(app.width-app.margin-300, app.height-app.margin-300,
        app.width-app.margin, app.height-app.margin-250)
    app.obsList.append(app.wallD3)
    app.wallD4 = Obstacle(app.width-app.margin-250, app.height-app.margin-200,
        app.width-app.margin-50, app.height-app.margin-150)
    app.obsList.append(app.wallD4)
    app.wallD5 = Obstacle(app.width-app.margin-400, app.height-app.margin-100,
        app.width-app.margin-350, app.height-app.margin)
    app.obsList.append(app.wallD5)
    # passable obstacles: jail, gate
    app.jail = PassableObs(app.width-app.margin-100, app.topMargin,
        app.width-app.margin, app.topMargin+100, 161, 66, 100)
    app.passableObs.append(app.jail)
    app.gate = PassableObs(app.margin+(20*25), app.height-app.margin-50,
        app.margin+(30*25), app.height-app.margin, 160, 191, 115)
    app.passableObs.append(app.gate)
    # chest: append in obsList
    app.chestPercentage = 0
    app.chestMessage = f'Chest Opening Process  {app.chestPercentage}/100%'
    app.chest1 = Chest(app.margin+50, app.topMargin+50,
        app.margin+100, app.topMargin+100)
    app.obsList.append(app.chest1)

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
    for obs in app.passableObs: # check if char in passable obstacle
        if inObstacle(app, obs, char.cx, char.cy, char) and (not obs.passable):
            char.cx -= dx
            char.cy -= dy
    if char.cx < char.rx + app.margin \
        or char.cx > app.width - char.rx - app.margin: # check x bounds
        char.cx -= dx
    elif char.cy < char.ry + app.topMargin \
        or char.cy > app.height - char.ry - app.margin: # check y bounds
        char.cy -= dy

def keyPressed(app, event):
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

def timerFired(app):
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
        else: # not miving --> only show first frame (idle char)
            char.spriteCounter = 0

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
            obs.x2, obs.y2, fill='grey')

def drawPassableObs(app, canvas):
    for obs in app.passableObs:
        canvas.create_rectangle(obs.x1, obs.y1,
            obs.x2, obs.y2, fill=obs.color)

def drawChests(app, canvas):
    # adapted from: https://www.cs.cmu.edu/~112/notes/notes-animations-part4.html#loadImageUsingUrl
    # chest 1
    if app.chest1.percentage >= 100:
        canvas.create_image(app.margin+app.chest1.cx,
            app.topMargin+app.chest1.cy,
            image=ImageTk.PhotoImage(app.chest1.openedImage))
    elif app.chest1.percentage < 100:
        canvas.create_image(app.margin+50+25,
            app.topMargin+50+25,
            image=ImageTk.PhotoImage(app.chest1.closedImage))
    

def drawBasicScreen(app, canvas):
    canvas.create_rectangle(app.margin, app.topMargin,
        app.width - app.margin, app.height - app.margin, outline = 'black')
    canvas.create_text(app.width//2, app.topMargin//2,
        text=app.mainMessage, font='Ariel 20') # main
    canvas.create_text(app.margin, app.topMargin//2, anchor='w',
        text=app.chestMessage, font='Ariel 20') # chest
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
    draw50Grids(app, canvas)

#################################################
# main
#################################################
runApp(width=1240, height=650)
# 575*1225 ==GRIDS==> 23*47 (row, col)
'''
Assets Cited:
https://penusbmic.itch.io/sci-fi-character-pack-12
https://maytch.itch.io/free-32x64-kanako-platformer-character-sprite-set
'''