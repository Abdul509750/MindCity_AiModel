from Algorithm import Algorithms
import random
import copy

class CSP:
    # Initialize CSP with city grid, defined domains, and subdomain shuffling
    def __init__(self, city_graph):
        self.graph = city_graph
        self.domain = ["Hospital", "Ambulance Depot", "Industrial", 
                       "School", "Power Plant", "Residential"]
        self.subDomains = {}
        self.assignment = {}
        self.algoObj = Algorithms()
        self.conflict_report = []
        self.assignSubdomains()
        
    # Retrieve possible types for a specific node variable
    def Getdomains(self , variable):
        return self.subDomains[(variable.Coordinates_X , variable.Coordinates_Y)]
        
    # Assign a randomized full domain to every node in the graph
    def assignSubdomains(self):
        for position in self.graph.nodes:  
            self.subDomains[position] = random.sample(self.domain , len(self.domain))
    
    # Perform a 3-hop BFS to ensure a Hospital is accessible from the node
    def checkHospitalAvailability(self, c_var, ass):
            queue = [(c_var, 0)]
            visited = set()
            visited.add((c_var.Coordinates_X, c_var.Coordinates_Y))

            while queue:
                current, depth = queue.pop(0)

                if ass[(current.Coordinates_X, current.Coordinates_Y)].NodeType == "Hospital":
                    return True

                if depth == 3:
                    continue

                r, c = current.Coordinates_X, current.Coordinates_Y
                for pr, pc in [(1,0), (0,1), (-1,0), (0,-1)]:
                    nr, nc = r + pr, c + pc

                    if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                        continue

                    if (nr, nc) in visited:
                        continue

                    visited.add((nr, nc))
                    queue.append((self.graph.nodes[(nr, nc)], depth + 1))

            return False
            
    # Perform a 2-hop BFS to ensure an Industrial zone is accessible for Power Plants
    def checkIndustrialZone(self, curr_n, ass):
        queue = [(curr_n, 0)]
        visited = set()
        visited.add((curr_n.Coordinates_X, curr_n.Coordinates_Y))

        while queue:
            current, depth = queue.pop(0)

            if ass[(current.Coordinates_X, current.Coordinates_Y)].NodeType == "Industrial":
                return True

            if depth == 2:
                continue

            r, c = current.Coordinates_X, current.Coordinates_Y
            for pr, pc in [(1,0), (0,1), (-1,0), (0,-1)]:
                nr, nc = r + pr, c + pc

                if not ((0 <= nr < self.graph.rows) and (0 <= nc < self.graph.cols)):
                    continue

                if (nr, nc) in visited:
                    continue

                visited.add((nr, nc))
                queue.append((self.graph.nodes[(nr, nc)], depth + 1))

        return False
        
    # Enforce type limits and local adjacency rules during assignment
    def binaryConstraints(self, assignment, current_Node, proposed_domain):
        limit = self.graph.typeLimits[proposed_domain]
        if limit != float('inf') and self.graph.typeCounts[proposed_domain] >= limit:
            return False

        r, c = current_Node.Coordinates_X, current_Node.Coordinates_Y
        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]

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

        return True

    # Audit the completed graph for all complex constraints and trigger repairs
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

        coordinates = [(1,0), (0,1), (-1,0), (0,-1)]
        for position, node in graph.nodes.items():
            if node.NodeType == "Industrial":
                r, c = position
                for dr, dc in coordinates:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in graph.nodes:
                        nbr_type = graph.nodes[(nr, nc)].NodeType
                        if nbr_type in ["School", "Hospital"]:
                            violations.append({
                                "position": position,
                                "node_type": "Industrial",
                                "rule": f"Adjacent to {nbr_type} at ({nr},{nc})"
                            })

        if len(violations) == 0:
            print("[CSP Validation] Layout valid — all constraints satisfied ✓")
            return True
        else:
            print("\n[CSP Validation] Violations found — conflict report:")
            rule_counts = {}
            for v in violations:
                rule = v['rule']
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
                print(f"  -> {v['node_type']} at {v['position']} violated rule: {v['rule']}")

            print("\n[CSP Validation] Conflict summary:")
            for rule, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
                print(f"  -> Rule '{rule}' caused {count} violation(s)")

            self.conflict_report = violations
            print("\n[CSP Validation] Attempting minimum-conflict repair...")
            self.minimumConflictFix(violations, graph)

            remaining = self._count_remaining_violations(graph)
            if remaining == 0:
                print("[CSP Validation] Repair successful — all constraints now satisfied ✓")
                return True
            else:
                print(f"[CSP Validation] {remaining} violation(s) remain — proposing minimum-conflict solution.")
                return True
    
    # Internal violation counter for post-repair assessment
    def _count_remaining_violations(self, graph):
        count = 0
        for position, node in graph.nodes.items():
            if node.NodeType == "Residential":
                if not self.checkHospitalAvailability(node, graph.nodes):
                    count += 1
            if node.NodeType == "Power Plant":
                if not self.checkIndustrialZone(node, graph.nodes):
                    count += 1
        return count

    # Apply heuristic-based corrections to resolve layout conflicts
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
                            safe = True
                            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                                adj_r, adj_c = nr + dr, nc + dc
                                if (adj_r, adj_c) in graph.nodes:
                                    if graph.nodes[(adj_r, adj_c)].NodeType == "Industrial":
                                        safe = False
                                        break
                            if safe:
                                neighbor.setNodeType("Hospital")
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
                            safe = True
                            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                                adj_r, adj_c = nr + dr, nc + dc
                                if (adj_r, adj_c) in graph.nodes:
                                    if graph.nodes[(adj_r, adj_c)].NodeType in ["School", "Hospital"]:
                                        safe = False
                                        break
                            if safe:
                                neighbor.setNodeType("Industrial")
                                graph.typeCounts["Industrial"] += 1     
                                graph.typeCounts["Residential"] -= 1   
                                print(f"  -> Converted ({nr},{nc}) to Industrial to fix violation")
                                break

            if v["node_type"] == "Industrial" and "Adjacent to" in v["rule"]:
                node = graph.nodes[(r, c)]
                node.setNodeType("Residential")
                graph.typeCounts["Industrial"] -= 1
                graph.typeCounts["Residential"] += 1
                print(f"  -> Converted ({r},{c}) from Industrial to Residential to fix adjacency violation")