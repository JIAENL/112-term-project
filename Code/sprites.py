# This demos sprites using Pillow/PIL images
# See here for more details:
# https://pillow.readthedocs.io/en/stable/reference/Image.html

# This uses a spritestrip from this tutorial:
# https://www.codeandweb.com/texturepacker/tutorials/how-to-create-a-sprite-sheet

from cmu_112_graphics import *
import time
#################################################
# create classes
#################################################
class Obstacle(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
class Char(object):
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.speed = 15
        self.t0 = 0
        self.isMoving = False
        self.isAttacking = False # should stay here
        self.isFacingRight = True
    def makeSprites(self, file, x1, y1, x2, y2, numOfFrames, upDown, isKiller):
        spritestrip = Image.open(file)
        self.sprites = []
        for i in range(numOfFrames):
            if upDown: # y1 == y2
                sprite = spritestrip.crop((x1, y1*i, x2, y2*(i+1)))
            else: # x1 == x2
                sprite = spritestrip.crop((x1*i, y1, x2*(i+1), y2))
            if isKiller: # scale killer
                sprite = sprite.resize((60, 60))
            self.sprites.append(sprite)
        self.spriteCounter = 0
class Killer(Char):
    def __init__(self, cx, cy):
        super().__init__(cx, cy)
        self.rx = 15
        self.ry = 20
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
        self.rx = 10
        self.ry = 20
        self.isInjured = False
        self.isDying = False

#################################################
# start app
#################################################
def appStarted(app):
    # create characters
    app.charList = []
    app.killer = Killer(app.width//2, app.height//2)
    app.charList.append(app.killer)
    app.survA = Survivor(app.width//4, app.height*(2/3))
    app.charList.append(app.survA)
    app.survB = Survivor(app.width//3, app.height*(2/3))
    app.charList.append(app.survB)
    # create walking animation sprite
    app.killer.makeSprites('move without FX.png',
        10, 26, 40, 26, 6, True, True)
    app.survA.makeSprites('blueKanakoRun.png',
        32, 15, 32, 64, 4, False, False)
    app.survB.makeSprites('yellowKanakoRun.png',
        32, 15, 32, 64, 4, False, False)
    # create attacking animation sprite
    app.killer.makeAttackSprites('shoot with FX.png',
        10, 26, 50, 26, 4, True)
    # create obstacles
    app.obsList = []
    app.wall1 = Obstacle(50, 70, 200, 150)
    app.obsList.append(app.wall1)
    app.wall2 = Obstacle(350, 100, 400, 400)
    app.obsList.append(app.wall2)

def inObstacle(app, obs, x, y, char): # is char in obstacle
    return (obs.x1 <= x <= obs.x2 or obs.x1 <= x-char.rx <= obs.x2 or\
        obs.x1 <= x+char.rx <= obs.x2) and (obs.y1 <= y <= obs.y2 or\
            obs.y1 <= y-char.ry <= obs.y2 or\
                obs.y1 <= y+char.ry <= obs.y2)

def move(app, char, dx, dy): # move when valid
    char.cx += dx
    char.cy += dy
    for obs in app.obsList:
        if inObstacle(app, obs, char.cx, char.cy, char):
            char.cx -= dx
            char.cy -= dy
    if char.cx < 20 or char.cx > app.width - 20:
        char.cx -= dx
    elif char.cy < 20 or char.cy > app.height - 20:
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
    elif event.key.lower() == 'j' or event.key.lower() == 'l' or\
        event.key.lower() == 'i' or event.key.lower() == 'k' or\
            event.key == 'Space':
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

def timerFired(app):
    for char in app.charList:
        if char.isMoving: # no input for a while --> status = not moving
            char.spriteCounter = (1 + char.spriteCounter) % len(char.sprites)
            if time.time() - char.t0 >= 0.1:
                char.isMoving = False
        elif char.isAttacking: # do animation once per attack
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
            obs.x2, obs.y2,)

def redrawAll(app, canvas):
    for char in app.charList:
        drawChar(app, canvas, char)
    drawWalls(app, canvas)

#################################################
# main
#################################################
runApp(width=500, height=500)