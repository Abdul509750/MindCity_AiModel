import copy

class Algorithms:
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

    def ForwardChecking(self, csp, graph):
        node = self.MRV(csp, graph)

        if node is None:
            csp.validateFinalLayout(graph)
            return graph

        r, c = node.Coordinates_X, node.Coordinates_Y

        # ✅ only get direct neighbors instead of all 100 nodes
        neighbor_positions = [
            (r+1, c), (r-1, c), (r, c+1), (r, c-1)
        ]
        neighbor_positions = [p for p in neighbor_positions if p in graph.nodes]

        for domain in csp.subDomains[(r, c)]:
            if csp.binaryConstraints(graph.nodes, node, domain):

                # assign
                graph.nodes[(r, c)].NodeType = domain
                graph.typeCounts[domain] += 1

                # ✅ only save neighbor domains not entire graph
                saved_domains = {
                    pos: csp.subDomains[pos].copy()
                    for pos in neighbor_positions
                }
                deadlock = False

                # ✅ prune only neighbors not all nodes
                for pos in neighbor_positions:
                    nodey = graph.nodes[pos]
                    if nodey.NodeType != "":
                        continue

                    co_domain = [
                        d for d in csp.subDomains[pos]
                        if csp.binaryConstraints(graph.nodes, nodey, d)
                    ]

                    if len(co_domain) == 0:
                        deadlock = True
                        break

                    csp.subDomains[pos] = co_domain

                if not deadlock:
                    result = self.ForwardChecking(csp, graph)
                    if result is not None:
                        return result

                # backtrack
                graph.nodes[(r, c)].NodeType = ""
                graph.typeCounts[domain] -= 1
                for pos, saved in saved_domains.items():
                    csp.subDomains[pos] = saved

        return None