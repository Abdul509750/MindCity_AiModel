import random

class LocationNode:
    # Initialize node with coordinates, type, risk, accessibility, and density
    def __init__(self, X=0.0, Y=0.0, NT="", RI=0, AF=True, PD=0):
        self.Coordinates_X = X
        self.Coordinates_Y = Y
        self.NodeType = NT
        self.RiskIndex = RI
        self.Accessibility_flag = AF
        self.PopulationDensity = PD
    
    # Assign node type and generate randomized population density based on category
    def setNodeType(self , NT):
        self.NodeType = NT
        if NT == "Residential":
            self.PopulationDensity = random.randint(500, 2000)
        elif NT == "School":
            self.PopulationDensity = random.randint(300, 800)
        elif NT == "Hospital":
            self.PopulationDensity = random.randint(100, 500)
        elif NT == "Industrial":
            self.PopulationDensity = random.randint(50, 200)
        elif NT == "Ambulance Depot" or NT == "Power Plant":
            self.PopulationDensity = random.randint(10, 50)
        else:
            self.PopulationDensity = 0

    # Update accessibility status
    def setAccessibility(self , booly):
        self.Accessibility_flag = booly

    # Update risk level index
    def setRiskIndex(self , RI):
        self.RiskIndex = RI

    # Output risk index to console
    def printNodes(self):
        print("---- Location Risk Index ---------")
        print(self.RiskIndex)

    # Required by heapq in A* — when two entries have equal f-costs,
    # Python compares the next tuple element (the node). Without this,
    # error occurs in comparison
    def __lt__(self, other):
        return (self.Coordinates_X, self.Coordinates_Y) < (other.Coordinates_X, other.Coordinates_Y)