
from Algorithm import Algorithms
import random
import copy

class CSP:
    #now extract the variables and the domains 
   # each node will ne the variable and the type is domain
   #Residential, Hospital, School, Industrial, Power Plant, or Ambulance Depot
    def __init__(self, city_graph):
        self.graph = city_graph
        # In CSP.__init__
        self.domain = ["Hospital", "Ambulance Depot", "Industrial", 
               "School", "Power Plant", "Residential"]
        self.subDomains = {}   # position -> list of possible types
        self.assignment = {}   # position -> assigned type
        self.algoObj = Algorithms()
        self.assignSubdomains()
        
    def Getdomains(self , variable):
        return self.subDomains[(variable.Coordinates_X , variable.Coordinates_Y)]
    def assignSubdomains(self):
        for position in self.graph.nodes:  
            self.subDomains[position] = random.sample(self.domain , len(self.domain))
    
    
    """ • Industrial zones cannot be placed next to schools or hospitals
        • Every residential area must be within three road hops of at least one hospital
        • Power plants must be placed within 2 road hops of at least one Industrial zone, since they exist to
        supply power to industrial areas.
        • The configuration must be checked for mathematical validity; if no valid layout is possible given the
        grid size and rules, your system must identify which specific rule is causing the conflict and propose
        minimum conflict solution. """
    def checkHospitalAvailability(self, c_var, ass):
    # BFS limited to 3 hops to find a Hospital
            queue = [(c_var, 0)]        # (current_node, current_depth)
            visited = set()
            visited.add((c_var.Coordinates_X, c_var.Coordinates_Y))

            while queue:
                current, depth = queue.pop(0)

                # found a hospital within 3 hops 
                if ass[(current.Coordinates_X, current.Coordinates_Y)].NodeType == "Hospital":
                    return True

                # stop going deeper if already at 3 hops
                if depth == 3:
                    continue

                # explore neighbors
                r, c = current.Coordinates_X, current.Coordinates_Y
                for pr, pc in [(1,0), (0,1), (-1,0), (0,-1)]:
                    nr, nc = r + pr, c + pc

                    # boundary check
                    if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                        continue

                    # skip already visited
                    if (nr, nc) in visited:
                        continue

                    visited.add((nr, nc))
                    queue.append((self.graph.nodes[(nr, nc)], depth + 1))

            return False  # no hospital found within 3 hops
    def checkIndustrialZone(self, curr_n, ass):
        # BFS limited to 2 hops to find an Industrial zone
        queue = [(curr_n, 0)]
        visited = set()
        visited.add((curr_n.Coordinates_X, curr_n.Coordinates_Y))

        while queue:
            current, depth = queue.pop(0)

            # found industrial within 2 hops 
            if ass[(current.Coordinates_X, current.Coordinates_Y)].NodeType == "Industrial":
                return True

            # stop at 2 hops
            if depth == 2:
                continue

            # explore neighbors
            r, c = current.Coordinates_X, current.Coordinates_Y
            for pr, pc in [(1,0), (0,1), (-1,0), (0,-1)]:
                nr, nc = r + pr, c + pc

                if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                    continue

                if (nr, nc) in visited:
                    continue

                visited.add((nr, nc))
                queue.append((self.graph.nodes[(nr, nc)], depth + 1))

        return False  # no industrial found within 2 hops
    def binaryConstraints(self, assignment, current_Node, proposed_domain):
        # limit check
        limit = self.graph.typeLimits[proposed_domain]
        if limit != float('inf') and self.graph.typeCounts[proposed_domain] >= limit:
            return False

        r, c = current_Node.Coordinates_X, current_Node.Coordinates_Y
        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]

        # adjacency check only — no BFS during search
        if proposed_domain in ["Hospital", "School", "Industrial"]:
            for pr, pc in coordinates:
                nr, nc = pr + r, pc + c
                if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                    continue
                if assignment[(nr, nc)].NodeType == "":
                    continue
                neighbor_type = assignment[(nr, nc)].NodeType
                match proposed_domain:
                    case "Hospital":
                        if neighbor_type == "Industrial":
                            return False
                    case "School":
                        if neighbor_type == "Industrial":
                            return False
                    case "Industrial":
                        if neighbor_type in ["School", "Hospital"]:
                            return False

        return True  # ✅ hop checks deferred to validateFinalLayout
    

    def validateFinalLayout(self, graph):
        violations = []

        for position, node in graph.nodes.items():
            if node.NodeType == "Residential":
                if not self.checkHospitalAvailability(node, graph.nodes):
                    violations.append({
                        "position": position,
                        "node_type": "Residential",
                        "rule": "No Hospital within 3 hops"
                    })
            if node.NodeType == "Power Plant":
                if not self.checkIndustrialZone(node, graph.nodes):
                    violations.append({
                        "position": position,
                        "node_type": "Power Plant",
                        "rule": "No Industrial within 2 hops"
                    })

        if len(violations) == 0:
            print("Layout valid")
            return True
        else:
            print("Violations found:")
            for v in violations:
                print(f"  -> {v['node_type']} at {v['position']} violated rule: {v['rule']}")
            self.minimumConflictFix(violations, graph)
        return False

    def minimumConflictFix(self, violations, graph):
        for v in violations:
            r, c = v["position"]

            if v["node_type"] == "Residential":
                if self.graph.typeCounts["Hospital"] >= self.graph.typeLimits["Hospital"]:
                    print(f"  -> Cannot fix ({r},{c}) — Hospital limit reached")
                    continue
                for pr, pc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r + pr, c + pc
                    if (nr, nc) in graph.nodes:
                        neighbor = graph.nodes[(nr, nc)]
                        if neighbor.NodeType == "Residential":
                            neighbor.NodeType = "Hospital"
                            graph.typeCounts["Hospital"] += 1       
                            graph.typeCounts["Residential"] -= 1    
                            print(f"  -> Converted ({nr},{nc}) to Hospital to fix violation")
                            break

            if v["node_type"] == "Power Plant":
                if self.graph.typeCounts["Industrial"] >= self.graph.typeLimits["Industrial"]:
                    print(f"  -> Cannot fix ({r},{c}) — Industrial limit reached")
                    continue
                for pr, pc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r + pr, c + pc
                    if (nr, nc) in graph.nodes:
                        neighbor = graph.nodes[(nr, nc)]
                        if neighbor.NodeType == "Residential":
                            neighbor.NodeType = "Industrial"
                            graph.typeCounts["Industrial"] += 1     
                            graph.typeCounts["Residential"] -= 1   
                            print(f"  -> Converted ({nr},{nc}) to Industrial to fix violation")
                            break