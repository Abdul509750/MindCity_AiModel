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

        # all nodes assigned 
        if node is None:
            return graph

        for domain in csp.Getdomains(node):
            if csp.binaryConstraints(graph.nodes, node, domain):

                # assign
                graph.nodes[(node.Coordinates_X, node.Coordinates_Y)].NodeType = domain
                saved_domains = copy.deepcopy(csp.subDomains)
                deadlock = False

                # forward checking — prune neighbors
                for position, nodey in graph.nodes.items():
                    if nodey.NodeType != "":  # skip already assigned
                        continue

                    co_domain = []  #  reset for each node
                    for domaini in csp.Getdomains(nodey):
                        if csp.binaryConstraints(graph.nodes, nodey, domaini):
                            co_domain.append(domaini)

                    if len(co_domain) == 0:
                        deadlock = True  # dead end
                        break

                    csp.subDomains[(nodey.Coordinates_X, nodey.Coordinates_Y)] = co_domain

                if not deadlock:
                    result = self.ForwardChecking(csp, graph)
                    if result is not None:
                        return result  # solution found

                # backtrack 
                graph.nodes[(node.Coordinates_X, node.Coordinates_Y)].NodeType = ""
                csp.subDomains = saved_domains

        return None  # no valid assignment found