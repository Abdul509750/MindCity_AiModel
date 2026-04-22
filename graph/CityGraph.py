from graph.LocationNode import LocationNode
from graph.CSP import Csp
class CityGraph:
    # grid of 30x30
    def __init__(self , row , col):
           self.row = row
           self.col = col
           Graph = {}  # cost(r , c) -> node
           EdgesCost = {} # node1 , node2 ->cost
           self.initializeGraph()
    
    def initializeGraph(self):
         
         for r in self.row:
              for c in self.col:
                  node = LocationNode(r,c)
                  self.Graph[(r,c)] = node

         coordinates = [(1,0),(0,1),(-1,0),(0,-1)]

         for r in self.row:
              for c in self.col:
                   for cX , cY in coordinates:
                        nX , nY = r + cX , c + cY
                        if (nX , nY) in self.Graph:
                             self.EdgesCost[(r,c) , (nX , nY)] = 1.0

