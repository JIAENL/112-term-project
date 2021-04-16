# This demos sprites using Pillow/PIL images
# See here for more details:
# https://pillow.readthedocs.io/en/stable/reference/Image.html

# This uses a spritestrip from this tutorial:
# https://www.codeandweb.com/texturepacker/tutorials/how-to-create-a-sprite-sheet

from cmu_112_graphics import *
import time
### create classes ###
class Obstacle(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

### app starts ###
def appStarted(app):
    # char
    app.charRX = 15
    app.charRY = 20
    # movement
    app.cx = app.width//2
    app.cy = app.height//2
    app.right = True
    app.speed = 15
    app.isMoving = False
    app.t0 = 0
    app.isAttacking = False
    # walking
    spritestrip = Image.open('blueKanakoRun.png')
    app.sprites = [ ]
    for i in range(4):
        sprite = spritestrip.crop((32*i, 0, 32*(i+1), 60))
        # sprite = sprite.resize((60, 60))
        app.sprites.append(sprite)
    app.spriteCounter = 0
    # attacking
    spritestrip = Image.open('shoot with FX.png')
    app.attackSprites = [ ]
    for i in range(4):
        sprite = spritestrip.crop((10, 26*i, 50, 26*(i+1)))
        sprite = sprite.resize((80, 60))
        app.attackSprites.append(sprite)
    app.attackSpriteCounter = 0
    # create obstacles
    app.obstacles = []
    app.wall1 = Obstacle(50, 70, 200, 150)
    app.obstacles.append(app.wall1)
    app.wall2 = Obstacle(350, 100, 400, 400)
    app.obstacles.append(app.wall2)

def inObstacle(app, obs, x, y):
    return (obs.x1 <= x <= obs.x2 or obs.x1 <= x-app.charRX <= obs.x2 or\
        obs.x1 <= x+app.charRX <= obs.x2) and (obs.y1 <= y <= obs.y2 or\
            obs.y1 <= y-app.charRY <= obs.y2 or\
                obs.y1 <= y+app.charRY <= obs.y2)

def move(app, dx, dy):
    app.cx += dx
    app.cy += dy
    for obs in app.obstacles:
        if inObstacle(app, obs, app.cx, app.cy):
            app.cx -= dx
            app.cy -= dy
    if app.cx < 20 or app.cx > app.width - 20:
        app.cx -= dx
    elif app.cy < 20 or app.cy > app.height - 20:
        app.cy -= dy

def keyPressed(app, event):
    app.t0 = time.time()
    app.isMoving = True
    if event.key == 'Left':
        move(app, -app.speed, 0)
        app.right = False
    elif event.key == 'Right':
        move(app, app.speed, 0)
        app.right = True
    elif event.key == 'Up':
        move(app, 0, -app.speed)
    elif event.key == 'Down':
        move(app, 0, app.speed)
    elif event.key == 'Space':
        app.isAttacking = True

def timerFired(app):
    if app.isMoving:
        app.spriteCounter = (1 + app.spriteCounter) % len(app.sprites)
        if time.time() - app.t0 >= 0.1:
            app.isMoving = False
    elif app.isAttacking:
        app.attackSpriteCounter = (1 + app.attackSpriteCounter)
        if app.attackSpriteCounter >= len(app.attackSprites):
            app.isAttacking = False
            app.attackSpriteCounter = 0
    else:
        app.spriteCounter = 0

def drawPerson(app, canvas):
    if app.right:
        if app.isAttacking:
            sprite = app.attackSprites[app.attackSpriteCounter]
            canvas.create_image(app.cx, app.cy,
                image=ImageTk.PhotoImage(sprite))
        else:
            sprite = app.sprites[app.spriteCounter]
            canvas.create_image(app.cx, app.cy,
                image=ImageTk.PhotoImage(sprite))
    else:
        if app.isAttacking:
            sprite = app.attackSprites[app.attackSpriteCounter].\
                transpose(Image.FLIP_LEFT_RIGHT)
            canvas.create_image(app.cx, app.cy,
                image=ImageTk.PhotoImage(sprite))
        else:
            sprite = app.sprites[app.spriteCounter].\
                transpose(Image.FLIP_LEFT_RIGHT)
            canvas.create_image(app.cx, app.cy,
                image=ImageTk.PhotoImage(sprite))

def drawWalls(app, canvas):
    for obs in app.obstacles:
        canvas.create_rectangle(obs.x1, obs.y1,
            obs.x2, obs.y2,)

def redrawAll(app, canvas):
    drawPerson(app, canvas)
    drawWalls(app, canvas)

runApp(width=500, height=500)