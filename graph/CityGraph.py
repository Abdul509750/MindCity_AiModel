from LocationNode import LocationNode
import random

class CityGraph:
    # Initialize grid dimensions, node storage, and urban planning limits
    def __init__(self, row, col):
        self.rows = row
        self.cols = col
        self.nodes = {} 
        self.EdgesCost = {} 
        self.event_log = []  
        self.total = row * col

        residential_estimate = int(self.total * 0.7)

        self.typeLimits = {
            "Residential":     float('inf'),
            "Hospital":        max(3, residential_estimate // 18),
            "School":          max(2, int(self.total * 0.08)),
            "Industrial":      max(3, int(self.total * 0.12)),
            "Power Plant":     max(1, int(self.total * 0.02)),
            "Ambulance Depot": 3
        }
        self.typeCounts = {
            "Residential":     0,
            "Hospital":        0,
            "School":          0,
            "Industrial":      0,
            "Power Plant":     0,
            "Ambulance Depot": 0
        }   
        self.initializeGraph()

    # Populate grid with LocationNodes and establish default adjacency costs
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

    # Remove bidirectional edge connectivity between two positions
    def block_road(self, pos_a, pos_b, reason="flooding"):
        removed = False
        if (pos_a, pos_b) in self.EdgesCost:
            del self.EdgesCost[(pos_a, pos_b)]
            removed = True
        if (pos_b, pos_a) in self.EdgesCost:
            del self.EdgesCost[(pos_b, pos_a)]
            removed = True

        if removed:
            msg = f"[EVENT] Road {pos_a} <-> {pos_b} BLOCKED due to {reason}."
            self.event_log.append(msg)
            print(msg)
        return removed

    # Re-establish bidirectional edge connectivity with a specified cost
    def unblock_road(self, pos_a, pos_b, cost=1.0):
        if pos_a in self.nodes and pos_b in self.nodes:
            self.EdgesCost[(pos_a, pos_b)] = cost
            self.EdgesCost[(pos_b, pos_a)] = cost
            msg = f"[EVENT] Road {pos_a} <-> {pos_b} RESTORED (cost={cost:.2f})."
            self.event_log.append(msg)
            print(msg)

    # Update weights for edges connecting two residential zones
    def apply_residential_edge_costs(self):
        for (u, v) in list(self.EdgesCost.keys()):
            node_u = self.nodes[u]
            node_v = self.nodes[v]
            if node_u.NodeType == "Residential" and node_v.NodeType == "Residential":
                self.EdgesCost[(u, v)] = 0.8

    # Record and display a simulation event
    def log_event(self, message):
        self.event_log.append(message)
        print(message)

    # Execute Genetic Algorithm for ambulance placement and swap node data
    def ReallocateAmbulance(self):
        from AmbulanceReplacment import my_AmbulanceReplacement
        new_Instance = my_AmbulanceReplacement()

        bestPositions = new_Instance.InitiateGA(self)

        old_ambulances = []
        for node in self.nodes.values():
            if node.NodeType == "Ambulance Depot":
                old_ambulances.append(node)

        for i in range(min(3, len(bestPositions))):
            src = bestPositions[i]      
            dest = old_ambulances[i]    

            temp = (dest.NodeType, dest.RiskIndex, dest.Accessibility_flag, dest.PopulationDensity)

            dest.NodeType = src.NodeType
            dest.RiskIndex = src.RiskIndex
            dest.Accessibility_flag = src.Accessibility_flag
            dest.PopulationDensity = src.PopulationDensity

            src.NodeType = temp[0]
            src.RiskIndex = temp[1]
            src.Accessibility_flag = temp[2]
            src.PopulationDensity = temp[3]

        self.log_event("[Challenge 3] Ambulance positions re-evaluated and updated.")
            
    # Trigger Forward Checking CSP to assign node types
    def applyCSP(self):
        from my_CSP import CSP
        from Algorithm import Algorithms
        csp = CSP(self)
        alg = Algorithms()
        result = alg.ForwardChecking(csp, self)
        if result is None:
            print("[ERROR] CSP failed — no valid layout found.")
        else:
            print("[CSP] City layout assigned successfully.")
            self.apply_residential_edge_costs()
        return result

    # Invoke RoadNetwork construction via Genetic Algorithm
    def assignCosts(self):
        from RoadNetwork import RoadNetwork
        rn = RoadNetwork(self)
        rn.build()
        return rn

    # Perform clustering and prediction to adjust road costs based on risk
    def applyRiskAnalysis(self):
        try:
            from ML_Models import RiskClusterer, CrimePredictor 
        except ImportError:
            print("[ERROR] ML_Models.py not found. Skipping Risk Analysis.")
            return

        print("\n" + "=" * 62)
        print("   Step 3 – Urban Risk Analysis (Challenge 5 – ML)")
        print("=" * 62)
        
        clusterer = RiskClusterer(self, k=3)
        clusters, features = clusterer.run_kmeans()
        
        predictor = CrimePredictor(self, features)
        predictor.generate_synthetic_data()
        predictor.train_and_predict_knn(k=5)
        
        self._apply_risk_multipliers()
        self.log_event("[Challenge 5: Integration] High-risk travel multipliers applied to EdgesCost.")

    # Apply weighted multipliers to EdgesCost based on destination RiskIndex
    def _apply_risk_multipliers(self):
        risk_weights = {
            "High": 1.5,
            "Medium": 1.2,
            "Low": 1.0
        }
        
        for edge in list(self.EdgesCost.keys()):
            u, v = edge
            node_v = self.nodes[v]
            if node_v.RiskIndex:
                multiplier = risk_weights.get(node_v.RiskIndex, 1.0)
                self.EdgesCost[edge] *= multiplier

    # Simulate environmental hazards by blocking random active edges
    def trigger_random_flood(self):
        active_edges = list(self.EdgesCost.keys())
        if not active_edges:
            return []

        num_to_block = random.randint(1, min(2, len(active_edges)))
        blocked = []
        for _ in range(num_to_block):
            if not active_edges:
                break
            edge = random.choice(active_edges)
            pos_a, pos_b = edge
            self.block_road(pos_a, pos_b, reason="flooding")
            blocked.append((pos_a, pos_b))
            active_edges = [e for e in active_edges
                           if e != (pos_a, pos_b) and e != (pos_b, pos_a)]
        return blocked

    # Display an ASCII representation of the current grid state
    def printGraph(self):
        TYPE_ABBR = {
            "Residential":     "RES",
            "Hospital":        "HSP",
            "School":          "SCH",
            "Industrial":      "IND",
            "Power Plant":     "PWR",
            "Ambulance Depot":"AMB",
            "":                "---",   
        }

        print(f"\n=== City Grid ({self.rows} x {self.cols}) ===\n")

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

    # Display all recorded simulation events
    def print_event_log(self):
        print("\n" + "=" * 62)
        print("  SIMULATION EVENT LOG")
        print("=" * 62)
        if not self.event_log:
            print("  (no events recorded)")
        for i, event in enumerate(self.event_log, 1):
            print(f"  {i:>3}. {event}")
        print("=" * 62 + "\n")

if __name__ == "__main__":
    graph = CityGraph(10, 10)   
    graph.applyCSP()          
    graph.printGraph()        
    graph.assignCosts()       
    graph.applyRiskAnalysis()
    graph.ReallocateAmbulance()
    print("\nAfter ambulance replacement--------------")
    graph.printGraph()
    graph.print_event_log()