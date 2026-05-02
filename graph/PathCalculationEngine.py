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

    def toFindPath(self, start, goal):
        import heapq

        neighbourCoordinates = [(0,1), (1,0), (0,-1), (-1,0)]

        # (f_cost, g_cost, current_node, path)
        open_list = []
        heapq.heappush(open_list, (0, 0, start, [start]))

        visited = set()

        while open_list:
            f, g, current, path = heapq.heappop(open_list)  # always pops lowest f

            current_pos = (current.Coordinates_X, current.Coordinates_Y)

            if current_pos in visited:
                continue
            visited.add(current_pos)

            # goal reached
            if current_pos == (goal.Coordinates_X, goal.Coordinates_Y):
                return path, g

            # expand neighbors
            for dr, dc in neighbourCoordinates:
                nr, nc = current_pos[0] + dr, current_pos[1] + dc
                neighbor_pos = (nr, nc)

                if neighbor_pos not in self.city_graph.nodes:
                    continue
                if neighbor_pos in visited:
                    continue

                # get edge cost
                edge_cost = self.city_graph.EdgesCost.get((current_pos, neighbor_pos), 1.0)

                neighbor_node = self.city_graph.nodes[neighbor_pos]

                g_new = g + edge_cost
                h_new = self.heuristics[neighbor_pos]
                f_new = g_new + h_new

                heapq.heappush(open_list, (f_new, g_new, neighbor_node, path + [neighbor_node]))

        return None, float('inf')  # no path found
            


    def FindPath(self , start , goal , graph):  # event will be trigger in the GUI it will sent the signal to the Astar to return path
        self.city_graph = graph
        self.initializeHeuristics(goal)
        return self.toFindPath(start , goal)

