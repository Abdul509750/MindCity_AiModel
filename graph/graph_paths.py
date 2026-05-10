"""Short travel costs on CityGraph.EdgesCost (Dijkstra)."""
import heapq


def min_cost_from_sources(graph, source_positions):
    """
    Multi-source Dijkstra: for each cell, cheapest cost to reach any source.
    source_positions: iterable of (row, col). Uses current EdgesCost (risk included).
    """
    dist = {}
    pq = []
    for s in source_positions:
        if s not in graph.nodes:
            continue
        if not graph.nodes[s].Accessibility_flag:
            continue
        dist[s] = 0.0
        heapq.heappush(pq, (0.0, s))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            v = (u[0] + dr, u[1] + dc)
            if v not in graph.nodes or not graph.nodes[v].Accessibility_flag:
                continue
            if (u, v) not in graph.EdgesCost:
                continue
            nd = d + graph.EdgesCost[(u, v)]
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def shortest_path_cost(graph, start_pos, goal_pos):
    """One pair; same rules as routing elsewhere."""
    if start_pos == goal_pos:
        return 0.0
    return min_cost_from_sources(graph, [start_pos]).get(goal_pos, float("inf"))
