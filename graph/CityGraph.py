from LocationNode import LocationNode
from RoadNetwork import RoadNetwork
class CityGraph:
    def __init__(self, row, col):
        self.rows = row
        self.cols = col
        self.nodes = {}      # (r, c) -> node
        self.EdgesCost = {}  # (node1, node2) -> cost
        self.initializeGraph()

    def initializeGraph(self):
        # create all nodes
        for r in range(self.rows):       
            for c in range(self.cols):   
                node = LocationNode(r, c)
                self.nodes[(r, c)] = node

        # create edges
        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]
        for r in range(self.rows):       
            for c in range(self.cols):   
                for cX, cY in coordinates:
                    nX, nY = r + cX, c + cY
                    if (nX, nY) in self.nodes:
                        self.EdgesCost[((r,c), (nX,nY))] = 1.0

    def assignCosts(self):
        rn = RoadNetwork(self)
        rn.build()
        return rn