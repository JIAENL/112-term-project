##modified from: https://drive.google.com/drive/u/1/folders/1NejM7M_5jZhlm5ttsROhjGXZtNiCdnxV
from cmu_112_graphics import *
import time, random
class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.f = 0
    def __eq__(self, other):
        return self.position == other.position
def getCellBounds(margin, topMargin, row, col):
    x1 = margin + col*50
    x2 = margin + (col+1)*50
    y1 = topMargin + row*50
    y2 = topMargin + (row+1)*50
    return x1, y1, x2, y2

def appStarted(app):
    # basic display
    app.topMargin = 80
    app.margin = 20
    # search related
    app.start = [3, 3]
    app.end = [0,7]
    app.cost = 1
    app.path = [[]]
    app.t0 = time.time()
    app.maze =  [[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
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

def return_path(current_node,maze): # trace back the path
    path = []
    result = [[-1 for i in range(len(maze[0]))] for j in range(len(maze))] # -1 means not part of the path
    current = copy.deepcopy(current_node)
    while current is not None:
        path.append(current.position)
        current = current.parent
    path = path[::-1] # make it from start to end: [row,col], [row,col], ...
    return path

def h(x0,y0,x1,y1):
    return abs(x0 - x1) + abs(y0 - y1) # manhattan
    # if don't want to estimate, just return 0

def search(app, maze, cost, start, end): # main code
    start_node = Node(None, tuple(start))# Create start and end node
    end_node = Node(None, tuple(end))
    # initialize  wantToVisitList and visitedList
    wantToVisitList = [start_node] # all relavant childrens regardless of gen
    visitedList = [] # don't test again
    # add a stop condition to avoid infinite loop
    outerIterations = 0
    maxIterations = (len(maze) // 3) ** 10
    
    while len(wantToVisitList) > 0: # Loop until reach end
        outerIterations += 1
        if outerIterations > maxIterations: # iteration protection
            print ("giving up on pathfinding too many iterations")
            return return_path(current_node,maze)
        # current node = lowest f node, otherwise just choose the 0th
        current_node = wantToVisitList[0] 
        current_index = 0
        for index, item in enumerate(wantToVisitList):
            if item.f < current_node.f:
                current_node = item
                current_index = index
        # move current from wantToVisit to visited
        wantToVisitList.pop(current_index)
        visitedList.append(current_node)
        # if current is end, return path
        if current_node == end_node:
            return return_path(current_node,maze)

        # generate children node
        children = []
        dirs  =  [(1,0),(-1,0),(0,1),(0,-1)] # search directions: down up right left
        for direction in dirs:
            # Get node position
            newRC = (current_node.position[0] + direction[0], current_node.position[1] + direction[1])
            if (newRC[0] > (len(maze) - 1) or newRC[0] < 0 or 
                newRC[1] > (len(maze[0]) -1) or newRC[1] < 0): # not in bounds then pass
                continue
            if maze[newRC[0]][newRC[1]] != 0: # is obstacle then pass
                continue
            new_node = Node(current_node, newRC)# if ok then create the child as a node
            children.append(new_node)
        # calculate children's f
        for child in children:
            if child in visitedList: continue # skip visited child
            child.g = current_node.g + cost # past costs + cost of this step
            child.h = h(child.position[0],child.position[1],\
                end_node.position[0],end_node.position[1]) # estimate (h)
            if len([i for i in wantToVisitList if child == i and\
                child.g > i.g]) > 0:
                continue # if child in wantToVisitList and already has a lower g, don't add it to the wantToVisitList list
            wantToVisitList.append(child)

# def timerFired(app): # new added
#     dirs = [(1,0), (0,-1), (-1,0), (0,1)]
#     endR, endC = tuple(app.end)
#     if time.time() - app.t0 >= 0.1:
#         while True: # random imitation of target movement
#             index = random.randint(0,3)
#             dr, dc = dirs[index]
#             endR = app.end[0] + dr
#             endC = app.end[1] + dc
#             if endR + endC >= 14:
#                 endR, endC = tuple(app.end)
#                 break
#             if 0<=endR<len(app.maze) and 0<=endC<len(app.maze[0])\
#             and (app.maze[endR][endC] == 0):
#                 break
#         app.end = [endR, endC]
#         app.t0 = time.time()
#         app.path = search(app, app.maze, app.cost, app.start, app.end)
#         # app.start change to [rK, cK]
#         # app.end = target row, target col (when chasing)
#         # app.end = [8, 11]

# def redrawAll(app, canvas):
#     if len(app.path) == 0: return
#     for row in range(len(app.path)):
#         for col in range(len(app.path[0])):
#             x0,y0,x1,y1 = getCellBounds(app.margin, app.topMargin, row, col)
#             if [row,col] == app.start:
#                 color = "green"
#             elif [row,col] == app.end:
#                 color = "red"
#             elif app.maze[row][col] == 1: # later delete when move to main code
#                 color = "blue"
#             elif app.path[row][col] == -1:
#                 color = "white"
#             else:
#                 color = "black"
#             canvas.create_rectangle(x0,y0,x1,y1,fill=color)

#################################################
# main
#################################################
# runApp(width=1240, height=650)