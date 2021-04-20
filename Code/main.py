from cmu_112_graphics import *
from PIL import ImageTk
import tkinter as tk
import string, random, time

def appStarted(app):
    # basic display
    app.topMargin = 80
    app.margin = 20

#################################################
# graphics
#################################################

def drawBasicScreen(app, canvas):
    canvas.create_rectangle(app.margin, app.topMargin,
        app.width - app.margin, app.height - app.margin, outline = 'black')

def redrawAll(app, canvas):
    drawBasicScreen(app, canvas)
    
#################################################
# main
#################################################
def main():
    runApp(width=1280, height=681)

if __name__ == '__main__':
    main()