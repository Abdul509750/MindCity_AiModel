class Algorithms:
    def MRV(self, csp):
        # find the unassigned node with the smallest subdomain
        min_node = None
        min_size = float('inf')

        for position, node in csp.graph.nodes.items():
            # only look at unassigned nodes
            if node.NodeType == "":
                domain_size = len(csp.subDomains[position])
                if domain_size < min_size:
                    min_size = domain_size
                    min_node = node

        return min_node  # node with fewest remaining options

    def ForwardChecking(self, csp, graph):
        # pick the most constrained node first using MRV
        node = self.MRV(csp)

        if node is None:
            return True  # all nodes assigned

        # try each type from its subdomain
        for proposed_type in csp.subDomains[(node.Coordinates_X, node.Coordinates_Y)]:
            if csp.binaryConstraints(graph.nodes, node, proposed_type):
                # assign it
                node.NodeType = proposed_type

                # recurse
                result = self.ForwardChecking(csp, graph)
                if result:
                    return True

                # backtrack
                node.NodeType = ""

        return False  # no valid assignment found


        # pruning/ forward checking is remainning / abhi backtrack bhi sai nhi dekhna