import random
import copy
from collections import defaultdict, deque

class _UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank   = {e: 0  for e in elements}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True

    def all_connected(self, elements):
        root = self.find(next(iter(elements)))
        return all(self.find(e) == root for e in elements)

class RoadNetwork:
    _EDGE_COST_TABLE = {
        frozenset({"Hospital",        "Ambulance Depot"}): 0.5,
        frozenset({"Hospital",        "Residential"}):     0.8,
        frozenset({"Ambulance Depot", "Residential"}):     0.8,
        frozenset({"Industrial",      "Residential"}):     1.5,
        frozenset({"Power Plant",      "Residential"}):     1.4,
        frozenset({"Industrial",      "Power Plant"}):     0.6,
        frozenset({"School",          "Residential"}):     0.7,
    }
    _DEFAULT_EDGE_COST = 1.0

    def __init__(
        self,
        city_graph,
        population_size=80,
        generations=200,
        p_crossover=0.8,
        p_mutation=0.02,
        elite_count=5,
        tournament_k=3,
        disconnected_penalty=500.0,
        safety_penalty=300.0,
    ):
        self.graph                = city_graph
        self.pop_size             = population_size
        self.generations          = generations
        self.p_crossover          = p_crossover
        self.p_mutation           = p_mutation
        self.elite_count          = elite_count
        self.tournament_k         = tournament_k
        self.disconnected_penalty = disconnected_penalty
        self.safety_penalty       = safety_penalty

        self.all_nodes        = list(city_graph.nodes.keys())
        self.canonical_edges  = []
        self.hospital_pos     = None
        self.ambulance_pos    = None

        self.best_chromosome  = None
        self.best_fitness     = -float('inf')
        self.built_roads      = []
        self.total_cost       = 0.0
        self.safety_satisfied = False

        self._setup()

    # Consolidate edges and identify critical infrastructure nodes
    def _setup(self):
        seen = set()
        nodes = self.graph.nodes

        for (u, v) in self.graph.EdgesCost:
            key = (min(u, v), max(u, v))
            if key in seen:
                continue
            seen.add(key)

            type_u = nodes[u].NodeType or "Unknown"
            type_v = nodes[v].NodeType or "Unknown"
            fkey   = frozenset({type_u, type_v})
            cost   = self._EDGE_COST_TABLE.get(fkey, self._DEFAULT_EDGE_COST)

            self.canonical_edges.append((key[0], key[1], cost))
            self.graph.EdgesCost[(u, v)] = cost
            self.graph.EdgesCost[(v, u)] = cost

        best_hosp_pop = -1
        best_amb_pop  = -1
        for pos, node in nodes.items():
            if node.NodeType == "Hospital":
                if node.PopulationDensity > best_hosp_pop:
                    best_hosp_pop = node.PopulationDensity
                    self.hospital_pos = pos
            elif node.NodeType == "Ambulance Depot":
                if node.PopulationDensity > best_amb_pop:
                    best_amb_pop = node.PopulationDensity
                    self.ambulance_pos = pos

    # Execute GA optimization loop
    def build(self):
        if not self.canonical_edges:
            print("[RoadNetwork] No edges found in graph.")
            return

        print(f"[GA] Starting – {len(self.all_nodes)} nodes, {len(self.canonical_edges)} edges.")
        population = [self._random_chromosome() for _ in range(self.pop_size)]

        for gen in range(1, self.generations + 1):
            scored = [(self._fitness(ch), ch) for ch in population]
            scored.sort(key=lambda x: x[0], reverse=True)

            if scored[0][0] > self.best_fitness:
                self.best_fitness    = scored[0][0]
                self.best_chromosome = scored[0][1][:]

            if gen % 50 == 0 or gen == 1:
                cost = self._total_cost(self.best_chromosome)
                safe = self._has_two_independent_paths(self.best_chromosome)
                print(f"  Gen {gen:>4}: best cost = {cost:.2f}  safety = {'YES' if safe else 'NO'}")

            elite   = [ch for _, ch in scored[:self.elite_count]]
            parents = [ch for _, ch in scored]
            next_pop = elite[:]

            while len(next_pop) < self.pop_size:
                p1 = self._tournament_select(parents, scored)
                p2 = self._tournament_select(parents, scored)
                c1, c2 = self._crossover(p1, p2)
                next_pop.append(self._mutate(c1))
                if len(next_pop) < self.pop_size:
                    next_pop.append(self._mutate(c2))

            population = next_pop

        self._decode_result()
        self._report()

    # Generate chromosome using randomized spanning tree
    def _random_chromosome(self):
        n_edges = len(self.canonical_edges)
        chromosome = [0] * n_edges
        shuffled_idx = list(range(n_edges))
        random.shuffle(shuffled_idx)
        uf = _UnionFind(self.all_nodes)

        for i in shuffled_idx:
            u, v, _ = self.canonical_edges[i]
            if uf.union(u, v):
                chromosome[i] = 1

        for i in range(n_edges):
            if chromosome[i] == 0 and random.random() < 0.15:
                chromosome[i] = 1
        return chromosome

    # Calculate inverse objective function with connectivity and safety penalties
    def _fitness(self, chromosome):
        cost    = self._total_cost(chromosome)
        penalty = 0.0
        if not self._is_connected(chromosome):
            penalty += self.disconnected_penalty
        if self.hospital_pos and self.ambulance_pos:
            if not self._has_two_independent_paths(chromosome):
                penalty += self.safety_penalty
        return 1.0 / (cost + penalty + 1e-9)

    def _total_cost(self, chromosome):
        return sum(self.canonical_edges[i][2] for i in range(len(chromosome)) if chromosome[i] == 1)

    def _is_connected(self, chromosome):
        uf = _UnionFind(self.all_nodes)
        for i, bit in enumerate(chromosome):
            if bit:
                u, v, _ = self.canonical_edges[i]
                uf.union(u, v)
        return uf.all_connected(self.all_nodes)

    # Verify edge-disjoint path redundancy between key nodes
    def _has_two_independent_paths(self, chromosome):
        if self.hospital_pos is None or self.ambulance_pos is None:
            return True
        src, dst = self.hospital_pos, self.ambulance_pos
        residual = defaultdict(lambda: defaultdict(int))
        for i, bit in enumerate(chromosome):
            if bit:
                u, v, _ = self.canonical_edges[i]
                residual[u][v] += 1
                residual[v][u] += 1

        flow = 0
        for _ in range(2):
            parent = {src: None}
            queue  = deque([src])
            found  = False
            while queue and not found:
                node = queue.popleft()
                for nbr, cap in residual[node].items():
                    if cap > 0 and nbr not in parent:
                        parent[nbr] = node
                        if nbr == dst:
                            found = True
                            break
                        queue.append(nbr)
            if not found: break
            node = dst
            while node != src:
                prev = parent[node]
                residual[prev][node] -= 1
                residual[node][prev] += 1
                node = prev
            flow += 1
        return flow >= 2

    def _tournament_select(self, population, scored):
        contestants = random.sample(range(len(population)), min(self.tournament_k, len(population)))
        best_idx    = max(contestants, key=lambda i: scored[i][0])
        return population[best_idx][:]

    def _crossover(self, p1, p2):
        if random.random() > self.p_crossover or len(p1) < 3:
            return p1[:], p2[:]
        i1 = random.randint(0, len(p1) - 2)
        i2 = random.randint(i1 + 1, len(p1) - 1)
        return p1[:i1] + p2[i1:i2] + p1[i2:], p2[:i1] + p1[i1:i2] + p2[i2:]

    def _mutate(self, chromosome):
        return [1 - bit if random.random() < self.p_mutation else bit for bit in chromosome]

    # Map best chromosome back to graph edge costs
    def _decode_result(self):
        ch = self.best_chromosome
        self.built_roads = [(self.canonical_edges[i][0], self.canonical_edges[i][1], self.canonical_edges[i][2])
                            for i in range(len(ch)) if ch[i] == 1]
        self.total_cost = sum(r[2] for r in self.built_roads)
        self.safety_satisfied = self._has_two_independent_paths(ch)

        built_set = set()
        for u, v, _ in self.built_roads:
            built_set.add((u, v))
            built_set.add((v, u))

        for edge_key in list(self.graph.EdgesCost.keys()):
            if edge_key not in built_set:
                del self.graph.EdgesCost[edge_key]

        for u, v, cost in self.built_roads:
            self.graph.EdgesCost[(u, v)] = cost
            self.graph.EdgesCost[(v, u)] = cost

    def _report(self):
        print("\n" + "=" * 62)
        print("    CHALLENGE 2 – Road Network Optimisation (GA) Report")
        print("=" * 62)
        print(f"  Total nodes       : {len(self.all_nodes)}")
        print(f"  Roads built       : {len(self.built_roads)}")
        print(f"  Total road cost   : {self.total_cost:.2f}")
        print(f"  Fully connected   : {'YES' if self._is_connected(self.best_chromosome) else 'NO'}")
        print(f"  Safety constraint : {'SATISFIED' if self.safety_satisfied else 'VIOLATED'}")
        print("=" * 62 + "\n")

if __name__ == "__main__":
    from CityGraph import CityGraph
    from my_CSP import CSP
    from Algorithm import Algorithms

    g = CityGraph(4, 4)
    csp = CSP(g)
    alg = Algorithms()
    if alg.ForwardChecking(csp, g):
        rn = RoadNetwork(g)
        rn.build()