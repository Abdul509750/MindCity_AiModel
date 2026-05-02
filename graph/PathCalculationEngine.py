#executing the challenge 4 

# structure of the edge cost is edgecost[(x,y),(a , b)] = 0.smthng

class AstarEngine:

    def __init__(self):
        self.heuristics = {} # storing heuritics
        self.city_graph = {} # local copy of the graph for easiness
    def ReturnManhatten(self , node , goal ):
        tuple1 = (node.Coordinates_X , node.Coordinates_Y)
        tuple2 = (goal.Coordinates_X , goal.Coordinates_Y)
        return abs(tuple2[0] - tuple1[0]) + abs(tuple2[1] - tuple1[1])
     
    def initializeHeuristics(self , goal): 
        # we will be calculating the manhatten distance heuristics
        for pos , node in self.city_graph.nodes.items():
            heuristic = self.ReturnManhatten(node , goal)
            self.heuristics[(pos)] = heuristic

    def toFindPath(self , start , goal):
        # we need a in built priority queue
        neighbourCoordinates = [(0,1) , (1,0) , (0, -1) , (-1 , 0)]
        #initiailize the priority queue
        


    def FindPath(self , start , goal , graph):  # event will be trigger in the GUI it will sent the signal to the Astar to return path
        self.city_graph = graph
        self.initializeHeuristics(goal)
        return self.toFindPath(start , goal)

