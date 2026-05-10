import heapq


class AstarEngine:
    def __init__(self):
        self.city_graph = None

    def _min_edge_cost(self, graph):
        m = None
        for c in graph.EdgesCost.values():
            if c > 0:
                if m is None or c < m:
                    m = c
        return m if m is not None else 1.0

    def _heuristic_to_goal(self, pos, goal_pos, min_w):
        """Admissible: min_w * Manhattan <= true shortest path on 4-neighbor grid if every step costs >= min_w."""
        dr = abs(pos[0] - goal_pos[0]) + abs(pos[1] - goal_pos[1])
        return min_w * dr

    def toFindPath(self, start, goal):
        """A* with lazy deletion: skip pop when g > best_g[pos]. Returns (path_nodes, cost) or (None, inf)."""
        graph = self.city_graph
        goal_pos = (goal.Coordinates_X, goal.Coordinates_Y)
        start_pos = (start.Coordinates_X, start.Coordinates_Y)
        min_w = self._min_edge_cost(graph)

        def h_fn(p):
            return self._heuristic_to_goal(p, goal_pos, min_w)

        open_heap = []
        heapq.heappush(open_heap, (h_fn(start_pos), 0.0, start_pos))
        best_g = {start_pos: 0.0}
        parent = {start_pos: None}

        while open_heap:
            f, g, pos = heapq.heappop(open_heap)
            if g > best_g.get(pos, float("inf")):
                continue
            if pos == goal_pos:
                coords = []
                p = pos
                while p is not None:
                    coords.append(p)
                    p = parent[p]
                coords.reverse()
                path_nodes = [graph.nodes[p] for p in coords]
                return path_nodes, g

            for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                npos = (pos[0] + dr, pos[1] + dc)
                if npos not in graph.nodes:
                    continue
                if not graph.nodes[npos].Accessibility_flag:
                    continue
                edge_key = (pos, npos)
                if edge_key not in graph.EdgesCost:
                    continue
                edge_cost = graph.EdgesCost[edge_key]
                new_g = g + edge_cost
                if new_g < best_g.get(npos, float("inf")):
                    best_g[npos] = new_g
                    parent[npos] = pos
                    heapq.heappush(open_heap, (new_g + h_fn(npos), new_g, npos))

        return None, float("inf")

    def FindPath(self, start, goal, graph):
        self.city_graph = graph
        return self.toFindPath(start, goal)

    def FindSequentialPath(self, start, targets, graph):
        """Visit targets in order. Stops at first unreachable segment."""
        self.city_graph = graph
        current = start
        full_path = [start]
        total_cost = 0.0
        segments = []

        for i, target in enumerate(targets):
            path, cost = self.toFindPath(current, target)

            if path is None:
                seg_info = {
                    "from": (current.Coordinates_X, current.Coordinates_Y),
                    "to": (target.Coordinates_X, target.Coordinates_Y),
                    "status": "UNREACHABLE",
                    "cost": float("inf"),
                    "index": i,
                }
                segments.append(seg_info)
                print(
                    f"  [A*] Segment {i + 1}: {seg_info['from']} -> {seg_info['to']} — UNREACHABLE"
                )
                return full_path, total_cost, segments

            full_path.extend(path[1:])
            total_cost += cost
            current = target

            seg_info = {
                "from": (path[0].Coordinates_X, path[0].Coordinates_Y),
                "to": (target.Coordinates_X, target.Coordinates_Y),
                "status": "OK",
                "cost": cost,
                "hops": len(path) - 1,
                "index": i,
            }
            segments.append(seg_info)
            print(
                f"  [A*] Segment {i + 1}: {seg_info['from']} -> {seg_info['to']} — "
                f"cost={cost:.2f}, hops={len(path) - 1}"
            )

        return full_path, total_cost, segments

    def DynamicReroute(self, current_node, remaining_targets, graph):
        print(
            f"  [A*] REROUTE from ({current_node.Coordinates_X},{current_node.Coordinates_Y}) — "
            f"{len(remaining_targets)} target(s) left."
        )
        return self.FindSequentialPath(current_node, remaining_targets, graph)
# things leaarned 
# A* lazy deletion!!!