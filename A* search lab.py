##converted demonstration from https://github.com/BaijayantaRoy/Medium-Article/blob/master/A_Star.ipynb
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
#This function return the path of the search

def appStarted(app):
    # basic display
    app.topMargin = 80
    app.margin = 20
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

def return_path(current_node,maze):
    path = []
    no_rows, no_columns = len(maze), len(maze[0])
    # here we create the initialized result maze with -1 in every position
    result = [[-1 for i in range(no_columns)] for j in range(no_rows)]
    current = current_node
    while current is not None:
        path.append(current.position)
        current = current.parent
    # Return reversed path as we need to show from start to end path
    path = path[::-1]
    start_value = 0
    # we update the path of start to end found by A-star saerch with every step incremented by 1
    for i in range(len(path)):
        result[path[i][0]][path[i][1]] = start_value
        start_value += 1
    return result

def h(x0,y0,x1,y1):
    # euclidean:
    # return math.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2))

    # manhattan
    # return abs(x0 - x1) + abs(y0 - y1)

    # Cost-based search - Djkistra's first algo
    return 0

def search(app, maze, cost, start, end): # main code
    # Create start and end node with initized values for g, h and f
    start_node = Node(None, tuple(start))
    start_node.g = start_node.h = start_node.f = 0 # is this needed?
    end_node = Node(None, tuple(end))
    end_node.g = end_node.h = end_node.f = 0 # is this needed?

    # Initialize both yet_to_visit and visited list
    # From here we will find the lowest cost node to expand next
    yet_to_visit_list = [] # 
    # in this list we will put all node those already explored so that we don't explore it again
    visited_list = [] 
    
    # Add the start node
    yet_to_visit_list.append(start_node)
    
    # Adding a stop condition to avoid infinite loop
    outer_iterations = 0
    max_iterations = (len(maze) // 2) ** 10

    # Search directions at a cell
    move  =  [[-1, 0 ], # go up
              [ 0, -1], # go left
              [ 1, 0 ], # go down
              [ 0, 1 ]] # go right

    #find maze has got how many rows and columns 
    no_rows, no_columns = len(maze), len(maze[0])
    
    # Loop until you find the end
    while len(yet_to_visit_list) > 0:
        # Every time any node is referred from yet_to_visit list, counter of limit operation incremented
        outer_iterations += 1    

        # Get the current node
        current_node = yet_to_visit_list[0] # yet_to_visit_list contains children??
        current_index = 0
        for index, item in enumerate(yet_to_visit_list): # choose the lowest f node, otherwise just do the 0th
            if item.f < current_node.f:
                current_node = item
                current_index = index
                
        # Return when too many iterations
        if outer_iterations > max_iterations:
            print ("giving up on pathfinding too many iterations")
            return return_path(current_node,maze)

        # Pop current node out off yet_to_visit list, add to visited list
        yet_to_visit_list.pop(current_index)
        visited_list.append(current_node)

        # test if goal is reached or not, if yes then return the path
        if current_node == end_node:
            return return_path(current_node,maze)

        # Generate children from all adjacent squares
        children = []
        for new_position in move: # move is global var !!
            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            # Make sure within maze boundary
            if (node_position[0] > (no_rows - 1) or 
                node_position[0] < 0 or 
                node_position[1] > (no_columns -1) or 
                node_position[1] < 0):
                continue
            # Make sure no obstacle
            if maze[node_position[0]][node_position[1]] != 0:
                continue
            # Create new node
            new_node = Node(current_node, node_position)
            # Append ever walkable into children list of the current node
            children.append(new_node)

        for child in children:# Loop through children
            # If child in visited list then skip this children
            if len([visited_child for visited_child in visited_list if visited_child == child]) > 0:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + cost # certain cost values
            # Calculate the h
            child.h = h(child.position[0],child.position[1],end_node.position[0],end_node.position[1])

            # If child is already in the yet_to_visit list with a lower g (cuz we've been around it in a prev step)
            if len([i for i in yet_to_visit_list if child == i and child.g > i.g]) > 0:
                continue # don't add it to the yet_to_visit list

            # Add the child to the yet_to_visit list (full)
            yet_to_visit_list.append(child)

def timerFired(app): # new added
    dirs = [(1,0), (0,-1), (-1,0), (0,1)]
    endR, endC = tuple(app.end)
    if time.time() - app.t0 >= 0.1:
        while True: # random imitation of target movement
            index = random.randint(0,3)
            dr, dc = dirs[index]
            endR = app.end[0] + dr
            endC = app.end[1] + dc
            if endR + endC >= 14:
                endR, endC = tuple(app.end)
                break
            if 0<=endR<len(app.maze) and 0<=endC<len(app.maze[0])\
            and (app.maze[endR][endC] == 0):
                break
        app.end = [endR, endC]
        app.t0 = time.time()
        app.path = search(app, app.maze, app.cost, app.start, app.end)

def redrawAll(app, canvas):
    path = search(app, app.maze, app.cost, app.start, app.end)
    for row in range(len(path)):
        for col in range(len(path[0])):
            x0,y0,x1,y1 = getCellBounds(app.margin, app.topMargin, row, col)
            if [row,col] == app.start:
                color = "green"
            elif [row,col] == app.end:
                color = "red"
            elif app.maze[row][col] == 1:
                color = "blue"
            elif path[row][col] == -1:
                color = "white"
            else:
                color = "black"
            
            canvas.create_rectangle(x0,y0,x1,y1,fill=color)

#################################################
# main
#################################################
runApp(width=1240, height=650)