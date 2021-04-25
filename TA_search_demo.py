##converted demonstration from https://github.com/BaijayantaRoy/Medium-Article/blob/master/A_Star.ipynb
import basic_graphics, math
class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0
    def __eq__(self, other):
        return self.position == other.position

#This function return the path of the search
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

    #euclidean:
    #return math.sqrt(((x0 - x1) ** 2) + ((y0 - y1) ** 2))

    #manhattan
    #return abs(x0 - x1) + abs(y0 - y1)

    #Cost-based search - Djkistra's first algo
    return 0

def search(maze, cost, start, end):
    # Create start and end node with initized values for g, h and f
    start_node = Node(None, tuple(start))
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, tuple(end))
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both yet_to_visit and visited list
    # in this list we will put all node that are yet_to_visit for exploration. 
    # From here we will find the lowest cost node to expand next
    yet_to_visit_list = []  
    # in this list we will put all node those already explored so that we don't explore it again
    visited_list = [] 
    
    # Add the start node
    yet_to_visit_list.append(start_node)
    
    # Adding a stop condition. This is to avoid any infinite loop and stop 
    # execution after some reasonable number of steps
    outer_iterations = 0
    max_iterations = (len(maze) // 2) ** 10

    # what squares do we search . serarch movement is left-right-top-bottom 
    #(4 movements) from every positon

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
        current_node = yet_to_visit_list[0]
        current_index = 0
        for index, item in enumerate(yet_to_visit_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index
                
        # if we hit this point return the path such as it may be no solution or 
        # computation cost is too high
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

        for new_position in move: 

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range (check if within maze boundary)
            if (node_position[0] > (no_rows - 1) or 
                node_position[0] < 0 or 
                node_position[1] > (no_columns -1) or 
                node_position[1] < 0):
                continue

            # Make sure walkable terrain
            if maze[node_position[0]][node_position[1]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:
            
            # Child is on the visited list (search entire visited list)
            if len([visited_child for visited_child in visited_list if visited_child == child]) > 0:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + cost
            
            #calculate the h
            child.h = h(child.position[0],child.position[1],end_node.position[0],end_node.position[1])

            # Child is already in the yet_to_visit list and g cost is already lower
            if len([i for i in yet_to_visit_list if child == i and child.g > i.g]) > 0:
                continue

            # Add the child to the yet_to_visit list
            yet_to_visit_list.append(child)

def getCellBounds(maze,row, col):
    width = 400
    height = 400
    cols = len(maze[0])
    rows = len(maze)
    cellWidth = width / cols
    cellHeight = height / rows

    x0 = col * cellWidth
    x1 = (col+1) * cellWidth
    y0 = row * cellHeight
    y1 = (row+1) * cellHeight

    return (x0, y0, x1, y1)

def draw(canvas, width, height):
    maze = [[0, 0, 0, 0, 0, 0, 1 ,0],
            [0, 0, 0, 1, 0, 0, 1 ,0],
            [0, 0, 0, 0, 0, 0, 1 ,0],
            [0, 1, 0, 0, 0, 0, 1 ,0],
            [0, 1, 0, 1, 1, 0, 1 ,0],
            [0, 1, 0, 0, 0, 0, 0 ,0]]
    
    start = [0, 0] # starting position
    end = [5,7] # ending position
    cost = 1 # cost per movement

    path = search(maze,cost, start, end)

    for row in range(len(path)):
        for col in range(len(path[0])):
            x0,y0,x1,y1 = getCellBounds(maze,row, col)
            if [row,col] == start:
                color = "green"
            elif [row,col] == end:
                color = "red"
            elif maze[row][col] == 1:
                color = "blue"
            elif path[row][col] == -1:
                color = "white"
            else:
                color = "black"
            
            canvas.create_rectangle(x0,y0,x1,y1,fill=color)

basic_graphics.run(width=400, height=400)