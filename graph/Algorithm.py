import copy

class Algorithms:
    # Initialize search metrics for diagnostics
    def __init__(self):
        self.nodes_explored = 0   
        self.backtrack_count = 0  

    # Apply Minimum Remaining Values heuristic to select the next node
    def MRV(self, csp, graph):
        min_node = None
        min_size = float('inf')

        for position, node in graph.nodes.items():
            if node.NodeType == "":
                domain_size = len(csp.subDomains[position])
                if domain_size < min_size:
                    min_size = domain_size
                    min_node = node
        return min_node

    # Execute Forward Checking with local pruning and backtracking
    def ForwardChecking(self, csp, graph):
        node = self.MRV(csp, graph)

        if node is None:
            csp.validateFinalLayout(graph)
            return graph

        r, c = node.Coordinates_X, node.Coordinates_Y
        self.nodes_explored += 1

        neighbor_positions = [p for p in [(r+1, c), (r-1, c), (r, c+1), (r, c-1)] if p in graph.nodes]

        for domain in csp.subDomains[(r, c)]:
            if csp.binaryConstraints(graph.nodes, node, domain):

                graph.nodes[(r, c)].setNodeType(domain)
                graph.typeCounts[domain] += 1

                saved_domains = {pos: csp.subDomains[pos].copy() for pos in neighbor_positions}
                deadlock = False

                for pos in neighbor_positions:
                    nodey = graph.nodes[pos]
                    if nodey.NodeType != "":
                        continue

                    co_domain = [d for d in csp.subDomains[pos] if csp.binaryConstraints(graph.nodes, nodey, d)]

                    if len(co_domain) == 0:
                        deadlock = True
                        break

                    csp.subDomains[pos] = co_domain

                if not deadlock:
                    result = self.ForwardChecking(csp, graph)
                    if result is not None:
                        return result

                self.backtrack_count += 1
                graph.nodes[(r, c)].setNodeType("")
                graph.typeCounts[domain] -= 1
                for pos, saved in saved_domains.items():
                    csp.subDomains[pos] = saved

        if self.nodes_explored <= 5:
            self._diagnose_conflict(csp, graph)

        return None

    # Output diagnostic information when search fails at upper levels
    def _diagnose_conflict(self, csp, graph):
        unassigned = sum(1 for n in graph.nodes.values() if n.NodeType == "")
        print(f"\n[CSP Conflict Diagnosis]")
        print(f"  Nodes explored: {self.nodes_explored} | Backtracks: {self.backtrack_count}")
        print(f"  Unassigned: {unassigned} | Limits: {graph.typeLimits}")

        for pos in list(graph.nodes.keys())[:5]:
            if graph.nodes[pos].NodeType == "":
                valid = [d for d in csp.subDomains[pos] if csp.binaryConstraints(graph.nodes, graph.nodes[pos], d)]
                if len(valid) == 0:
                    print(f"  -> Node {pos} has NO valid values (Check adjacency/limits)")