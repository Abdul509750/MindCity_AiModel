# CityGraph.py
from LocationNode import LocationNode

class CityGraph:
    def __init__(self, row, col):
        self.rows = row
        self.cols = col
        self.nodes = {}
        self.EdgesCost = {}
        
        # quantity limits per type
        self.total = row * col

        residential_estimate = int(self.total * 0.7)

        self.typeLimits = {
            "Residential":    float('inf'),
            "Hospital":       max(3, residential_estimate // 18),
            "School":         max(2, int(self.total * 0.08)),
            "Industrial":     max(3, int(self.total * 0.12)),
            "Power Plant":    max(1, int(self.total * 0.02)),
            "Ambulance Depot": 3
        }
        self.typeCounts = {
            "Residential":    0,
            "Hospital":       0,
            "School":         0,
            "Industrial":     0,
            "Power Plant":    0,
            "Ambulance Depot":0
        }   
        self.initializeGraph()


    def initializeGraph(self):
        for r in range(self.rows):
            for c in range(self.cols):
                node = LocationNode(r, c)
                self.nodes[(r, c)] = node

        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]
        for r in range(self.rows):
            for c in range(self.cols):
                for cX, cY in coordinates:
                    nX, nY = r + cX, c + cY
                    if (nX, nY) in self.nodes:
                        self.EdgesCost[((r,c), (nX,nY))] = 1.0
    def ReallocateAmbulance(self):
        from AmbulanceReplacment import my_AmbulanceReplacement
        new_Instance = my_AmbulanceReplacement()

        bestPositions = new_Instance.InitiateGA(self)

        # Step 1: collect current ambulance nodes
        old_ambulances = []
        for node in self.nodes.values():
            if node.NodeType == "Ambulance Depot":
                old_ambulances.append(node)

        # Step 2: swap DATA (not objects)
        for i in range(min(3, len(bestPositions))):
            src = bestPositions[i]      # new optimal node
            dest = old_ambulances[i]    # current ambulance location

            # swap all attributes EXCEPT coordinates
            temp = (dest.NodeType, dest.RiskIndex, dest.Accessibility_flag, dest.PopulationDensity)

            dest.NodeType = src.NodeType
            dest.RiskIndex = src.RiskIndex
            dest.Accessibility_flag = src.Accessibility_flag
            dest.PopulationDensity = src.PopulationDensity

            src.NodeType = temp[0]
            src.RiskIndex = temp[1]
            src.Accessibility_flag = temp[2]
            src.PopulationDensity = temp[3]
            
    def applyCSP(self):
        """Run Challenge 1 — assign node types via CSP."""
        from my_CSP import CSP
        from Algorithm import Algorithms
        csp = CSP(self)
        alg = Algorithms()
        result = alg.ForwardChecking(csp, self)
        if result is None:
            print("[ERROR] CSP failed — no valid layout found.")
        else:
            print("[CSP] City layout assigned successfully.")
        return result

    def assignCosts(self):
        """Run Challenge 2 — build road network via GA."""
        from RoadNetwork import RoadNetwork
        rn = RoadNetwork(self)
        rn.build()
        return rn

    def printGraph(self):
        # readable abbreviations for each type
        TYPE_ABBR = {
            "Residential":    "RES",
            "Hospital":       "HSP",
            "School":         "SCH",
            "Industrial":     "IND",
            "Power Plant":    "PWR",
            "Ambulance Depot":"AMB",
            "":               "---",   # unassigned
        }

        print(f"\n=== City Grid ({self.rows} x {self.cols}) ===\n")

        # column headers
        header = "     " + "  ".join(f" C{c} " for c in range(self.cols))
        print(header)
        print("     " + "-----" * self.cols)

        for r in range(self.rows):
            row_str = f"R{r} | "
            for c in range(self.cols):
                nt = self.nodes[(r, c)].NodeType
                abbr = TYPE_ABBR.get(nt, "???")
                row_str += f"[{abbr}] "
            print(row_str)

        print()
        print("  Legend: RES=Residential  HSP=Hospital  SCH=School")
        print("          IND=Industrial   PWR=PowerPlant AMB=AmbulanceDepot")
        print()

if __name__ == "__main__":
    graph = CityGraph(10, 10)   # step 1: build empty grid
    graph.applyCSP()          # step 2: assign node types (Challenge 1)
    graph.printGraph()        # step 3: see the layout
    graph.assignCosts()       # step 4: build roads (Challenge 2)
    graph.ReallocateAmbulance()
    print("After ambulance replacemnt--------------")
    graph.printGraph()

# issue till now the recursion is causing the solution to undergo expensive computaion like 10x10 node means 100 nodes check this out