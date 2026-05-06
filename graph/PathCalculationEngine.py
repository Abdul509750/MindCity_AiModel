import heapq

class AstarEngine:
    # Initialize heuristic and local graph storage
    def __init__(self):
        self.heuristics = {}
        self.city_graph = {}

    # Calculate Manhattan distance between two nodes
    def ReturnManhatten(self , node , goal ):
        tuple1 = (node.Coordinates_X , node.Coordinates_Y)
        tuple2 = (goal.Coordinates_X , goal.Coordinates_Y)
        return abs(tuple2[0] - tuple1[0]) + abs(tuple2[1] - tuple1[1])
     
    # Populate heuristics dictionary based on goal position
    def initializeHeuristics(self , goal): 
        for pos , node in self.city_graph.nodes.items():
            heuristic = self.ReturnManhatten(node , goal)
            self.heuristics[(pos)] = heuristic

    # Execute A* search respecting road blocks and accessibility flags
    def toFindPath(self, start, goal):
        goal_pos = (goal.Coordinates_X, goal.Coordinates_Y)
        open_list = []
        heapq.heappush(open_list, (0, 0, start, [start]))
        visited = set()

        while open_list:
            f, g, current, path = heapq.heappop(open_list)
            current_pos = (current.Coordinates_X, current.Coordinates_Y)

            if current_pos in visited:
                continue
            visited.add(current_pos)

            if current_pos == goal_pos:
                return path, g

            neighbourCoordinates = [(0,1), (1,0), (0,-1), (-1,0)]
            for dr, dc in neighbourCoordinates:
                nr, nc = current_pos[0] + dr, current_pos[1] + dc
                neighbor_pos = (nr, nc)

                if neighbor_pos not in self.city_graph.nodes:
                    continue
                if neighbor_pos in visited:
                    continue

                neighbor_node = self.city_graph.nodes[neighbor_pos]

                if not neighbor_node.Accessibility_flag:
                    continue

                edge_key = (current_pos, neighbor_pos)
                if edge_key not in self.city_graph.EdgesCost:
                    continue

                edge_cost = self.city_graph.EdgesCost[edge_key]
                g_new = g + edge_cost
                h_new = self.heuristics.get(neighbor_pos, 0)
                f_new = g_new + h_new

                heapq.heappush(open_list, (f_new, g_new, neighbor_node, path + [neighbor_node]))

        return None, float('inf')

    # Trigger A* pathfinding for a single target
    def FindPath(self , start , goal , graph):
        self.city_graph = graph
        self.initializeHeuristics(goal)
        return self.toFindPath(start , goal)

    # Route sequentially through a list of targets
    def FindSequentialPath(self, start, targets, graph):
        self.city_graph = graph
        current = start
        full_path = [start]
        total_cost = 0.0
        segments = []

        for i, target in enumerate(targets):
            self.initializeHeuristics(target)
            path, cost = self.toFindPath(current, target)

            if path is None:
                seg_info = {
                    "from": (current.Coordinates_X, current.Coordinates_Y),
                    "to": (target.Coordinates_X, target.Coordinates_Y),
                    "status": "UNREACHABLE",
                    "cost": float('inf')
                }
                segments.append(seg_info)
                print(f"  [A*] Segment {i+1}: {seg_info['from']} -> {seg_info['to']} — UNREACHABLE")
                continue

            full_path.extend(path[1:])
            total_cost += cost
            current = target

            seg_info = {
                "from": (path[0].Coordinates_X, path[0].Coordinates_Y),
                "to": (target.Coordinates_X, target.Coordinates_Y),
                "status": "OK",
                "cost": cost,
                "hops": len(path) - 1
            }
            segments.append(seg_info)
            print(f"  [A*] Segment {i+1}: {seg_info['from']} -> {seg_info['to']} — cost={cost:.2f}, hops={len(path)-1}")

        return full_path, total_cost, segments

    # Recalculate remaining path segments in response to environment changes
    def DynamicReroute(self, current_node, remaining_targets, graph):
        print(f"  [A*] REROUTING from ({current_node.Coordinates_X},{current_node.Coordinates_Y}) — {len(remaining_targets)} target(s) remaining.")
        return self.FindSequentialPath(current_node, remaining_targets, graph)