

class LocationNode:
    def __init__(self, X=0.0, Y=0.0, NT="", RI=0, AF=True, PD=0):
        self.Coordinates_X = X
        self.Coordinates_Y = Y
        self.NodeType = NT
        self.RiskIndex = RI
        self.Accessibility_flag = AF
        self.PopulationDensity = PD
    
    def setNodeType(self , NT):
        self.NodeType = NT

    def setAccessibility(self , booly):
        self.Accessibility_flag = booly
  
    def setRiskIndex(self , RI):
        self.RiskIndex = RI
        