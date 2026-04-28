
from CityGraph import CityGraph
from Algorithm import Algorithms


class CSP:
    #now extract the variables and the domains 
   # each node will ne the variable and the type is domain
   #Residential, Hospital, School, Industrial, Power Plant, or Ambulance Depot
    def __init__(self, city_graph):
        self.graph = city_graph
        self.domain = ["Residential", "Hospital", "School",
                       "Industrial", "Power Plant", "Ambulance Depot"]
        self.subDomains = {}   # position -> list of possible types
        self.assignment = {}   # position -> assigned type
        self.algoObj = Algorithms()
        self.assignSubdomains()
        
    def Getdomains(self , variable):
        return self.subDomains[(variable.Coordinates_X , variable.Coordinates_Y)]
    def assignSubdomains(self):
        for position in self.graph.nodes:
            self.subDomains[position] = self.domain.copy()  # each node gets its OWN copy
        self.algoObj.ForwardChecking(self , self.graph)    
        print(position)
    
    
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
        r, c = current_Node.Coordinates_X, current_Node.Coordinates_Y

        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]

        if proposed_domain in ["Hospital", "School", "Industrial"]:
            for pr, pc in coordinates:
                nr, nc = pr + r, pc + c

                # boundary check
                if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                    continue

                # skip if neighbor not assigned yet
                if assignment[(nr , nc)].NodeType == "":
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
                    case _:
                        pass  # just skip unknown types

        elif proposed_domain == "Residential":
            return self.checkHospitalAvailability(current_Node, assignment)
        elif proposed_domain =="Power Plant":
            return self.checkIndustrialZone(current_Node , assignment)
        return True  #all constraints passed            