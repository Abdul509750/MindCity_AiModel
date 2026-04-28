"""
Challenge 2 – Road Network Optimisation via Genetic Algorithm
==============================================================

PROBLEM
-------
Given a city grid whose node types have already been assigned (by the CSP
solver in Challenge 1), determine which roads to build so that:
  1. ALL locations are connected (spanning network).
  2. Total road cost is MINIMISED.
  3. SAFETY CONSTRAINT: there are at least TWO completely independent
     (edge-disjoint) routes between the Primary Hospital and the
     Ambulance Depot, so that if any single road fails an alternative
     path always remains.

WHY A GENETIC ALGORITHM?
------------------------
The number of possible subsets of edges grows exponentially with grid size
(2^|E| subsets).  Exhaustive search is intractable for any non-trivial grid.
A Genetic Algorithm (GA) is well suited here because:
  • It explores a large, combinatorial search space via a *population* of
    candidate solutions evolving in parallel, making it far less likely to
    get trapped in a local optimum tihan Hill Climbing.
  • Selection pressure drives the population toward low-cost networks.
  • The safety penalty steers the GA away from solutions that violate the
    redundancy constraint without requiring hard constraint enforcement.

REPRESENTATION
--------------
  Chromosome : a binary list of length |E| (all candidate edges, canonical
               order).  A '1' means the road is built; '0' means it is not.

FITNESS FUNCTION
----------------
  fitness(chromosome) =
      1 / (total_road_cost
           + DISCONNECTED_PENALTY   [if graph is not fully connected]
           + SAFETY_PENALTY         [if Hospital ↔ Depot have < 2 edge-disjoint paths])

  Lower cost  →  higher fitness  →  more likely to survive and reproduce.

GA OPERATORS
------------
  Selection   : Tournament selection (k=3).
  Crossover   : Two-point crossover.
  Mutation    : Bit-flip with probability p_mutation per gene.
  Elitism     : Top-N elite individuals copied unchanged each generation.
"""

import random
import copy
from collections import defaultdict, deque


# ═══════════════════════════════════════════════════════════════════════════
#  Utility – Union-Find (used only internally in the connectivity check)
# ═══════════════════════════════════════════════════════════════════════════
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

    def connected(self, a, b):
        return self.find(a) == self.find(b)

    def all_connected(self, elements):
        root = self.find(next(iter(elements)))
        return all(self.find(e) == root for e in elements)


# ═══════════════════════════════════════════════════════════════════════════
#  RoadNetwork  –  the GA solver for Challenge 2
# ═══════════════════════════════════════════════════════════════════════════
class RoadNetwork:
    """
    Genetic Algorithm road-network optimiser.

    Parameters
    ----------
    city_graph : CityGraph
        Fully node-typed city graph produced by the Challenge-1 CSP solver.
    population_size : int
        Number of chromosomes in each generation.
    generations : int
        Number of GA generations to run.
    p_crossover : float
        Probability of performing crossover for a selected pair.
    p_mutation : float
        Per-gene (per-edge) bit-flip probability.
    elite_count : int
        Number of top individuals preserved unchanged each generation.
    tournament_k : int
        Tournament size for selection.
    disconnected_penalty : float
        Cost added to a chromosome whose road set does not connect all nodes.
    safety_penalty : float
        Cost added when Hospital ↔ Ambulance Depot lack 2 independent routes.
    """

    # ── edge-cost multipliers based on the endpoint node types ──────────────
    _EDGE_COST_TABLE = {
        frozenset({"Hospital",        "Ambulance Depot"}): 0.5,  # emergency lane
        frozenset({"Hospital",        "Residential"}):     0.8,
        frozenset({"Ambulance Depot", "Residential"}):     0.8,
        frozenset({"Industrial",      "Residential"}):     1.5,  # unwanted mix
        frozenset({"Power Plant",     "Residential"}):     1.4,
        frozenset({"Industrial",      "Power Plant"}):     0.6,  # natural pair
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
        self.graph               = city_graph
        self.pop_size            = population_size
        self.generations         = generations
        self.p_crossover         = p_crossover
        self.p_mutation          = p_mutation
        self.elite_count         = elite_count
        self.tournament_k        = tournament_k
        self.disconnected_penalty = disconnected_penalty
        self.safety_penalty      = safety_penalty

        # ── derived data built during setup ──
        self.all_nodes        = list(city_graph.nodes.keys())
        self.canonical_edges  = []   # [(u, v, cost), ...] unique canonical edges
        self.hospital_pos     = None
        self.ambulance_pos    = None

        # ── results ──
        self.best_chromosome  = None
        self.best_fitness     = -float('inf')
        self.best_cost        = float('inf')
        self.built_roads      = []   # list of (u, v, cost) in final network
        self.total_cost       = 0.0
        self.safety_satisfied = False

        self._setup()

    # ───────────────────────────────────────────────────────────────────────
    #  Setup helpers
    # ───────────────────────────────────────────────────────────────────────
    def _setup(self):
        """Deduplicate edges, assign semantic costs, locate critical nodes."""
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
            # update the graph's EdgesCost in both directions
            self.graph.EdgesCost[(u, v)] = cost
            self.graph.EdgesCost[(v, u)] = cost

        # Locate Hospital and Ambulance Depot
        for pos, node in nodes.items():
            if node.NodeType == "Hospital":
                self.hospital_pos = pos
            elif node.NodeType == "Ambulance Depot":
                self.ambulance_pos = pos

    # ───────────────────────────────────────────────────────────────────────
    #  Public entry point
    # ───────────────────────────────────────────────────────────────────────
    def build(self):
        """Run the GA and print the final road-network report."""
        if not self.canonical_edges:
            print("[RoadNetwork] No edges found in graph – nothing to optimise.")
            return

        print(f"[GA] Starting – {len(self.all_nodes)} nodes, "
              f"{len(self.canonical_edges)} candidate edges, "
              f"{self.pop_size} chromosomes, {self.generations} generations.")

        # ── 1. Initialise population ──────────────────────────────────────
        population = [self._random_chromosome() for _ in range(self.pop_size)]

        # ── 2. Evolve ─────────────────────────────────────────────────────
        for gen in range(1, self.generations + 1):
            # Evaluate fitness for every chromosome
            scored = [(self._fitness(ch), ch) for ch in population]
            scored.sort(key=lambda x: x[0], reverse=True)   # highest fitness first

            # Track global best
            if scored[0][0] > self.best_fitness:
                self.best_fitness    = scored[0][0]
                self.best_chromosome = scored[0][1][:]

            # Log progress every 50 generations
            if gen % 50 == 0 or gen == 1:
                cost = self._total_cost(self.best_chromosome)
                safe = self._has_two_independent_paths(self.best_chromosome)
                print(f"  Gen {gen:>4}: best cost = {cost:.2f}  "
                      f"safety = {'✓' if safe else '✗'}")

            # Elitism: keep top individuals unchanged
            elite   = [ch for _, ch in scored[:self.elite_count]]
            parents = [ch for _, ch in scored]

            # Build next generation
            next_pop = elite[:]
            while len(next_pop) < self.pop_size:
                p1 = self._tournament_select(parents, scored)
                p2 = self._tournament_select(parents, scored)
                c1, c2 = self._crossover(p1, p2)
                c1 = self._mutate(c1)
                c2 = self._mutate(c2)
                next_pop.append(c1)
                if len(next_pop) < self.pop_size:
                    next_pop.append(c2)

            population = next_pop

        # ── 3. Extract result from best chromosome ────────────────────────
        self._decode_result()
        self._report()

    # ───────────────────────────────────────────────────────────────────────
    #  Chromosome helpers
    # ───────────────────────────────────────────────────────────────────────
    def _random_chromosome(self):
        """
        Produce an initial chromosome that guarantees connectivity by first
        building a random spanning tree (shuffled Kruskal), then optionally
        adding extra edges with probability 0.15 to seed path redundancy.
        """
        n_edges = len(self.canonical_edges)
        chromosome = [0] * n_edges

        # Random spanning tree via shuffled Kruskal
        shuffled_idx = list(range(n_edges))
        random.shuffle(shuffled_idx)
        uf = _UnionFind(self.all_nodes)
        for i in shuffled_idx:
            u, v, _ = self.canonical_edges[i]
            if uf.union(u, v):
                chromosome[i] = 1

        # Randomly add a few extra edges to encourage redundancy
        for i in range(n_edges):
            if chromosome[i] == 0 and random.random() < 0.15:
                chromosome[i] = 1

        return chromosome

    # ── Fitness ─────────────────────────────────────────────────────────────
    def _fitness(self, chromosome):
        """
        fitness = 1 / (road_cost + penalties)

        Penalties:
          • disconnected_penalty  – added once if the selected edges do NOT
                                    form a connected spanning network.
          • safety_penalty        – added once if Hospital ↔ Ambulance Depot
                                    do not have ≥ 2 edge-disjoint paths.
        """
        cost    = self._total_cost(chromosome)
        penalty = 0.0

        if not self._is_connected(chromosome):
            penalty += self.disconnected_penalty

        if self.hospital_pos and self.ambulance_pos:
            if not self._has_two_independent_paths(chromosome):
                penalty += self.safety_penalty

        return 1.0 / (cost + penalty + 1e-9)   # +epsilon to avoid /0

    def _total_cost(self, chromosome):
        return sum(
            self.canonical_edges[i][2]
            for i in range(len(chromosome))
            if chromosome[i] == 1
        )

    # ── Connectivity check (Union-Find) ──────────────────────────────────
    def _is_connected(self, chromosome):
        uf = _UnionFind(self.all_nodes)
        for i, bit in enumerate(chromosome):
            if bit:
                u, v, _ = self.canonical_edges[i]
                uf.union(u, v)
        return uf.all_connected(self.all_nodes)

    # ── Safety check: ≥2 edge-disjoint paths (max-flow = 2 via BFS/DFS) ──
    def _has_two_independent_paths(self, chromosome):
        """
        Check whether Hospital and Ambulance Depot are connected by at least
        two edge-disjoint paths using a simple unit-capacity max-flow
        (Edmonds-Karp).  Returns True iff max-flow ≥ 2.
        """
        if self.hospital_pos is None or self.ambulance_pos is None:
            return True   # constraint not applicable

        src = self.hospital_pos
        dst = self.ambulance_pos

        # Build a residual adjacency: node → {neighbour: remaining_capacity}
        # Each selected edge has unit capacity in each direction.
        residual = defaultdict(lambda: defaultdict(int))
        for i, bit in enumerate(chromosome):
            if bit:
                u, v, _ = self.canonical_edges[i]
                residual[u][v] += 1
                residual[v][u] += 1

        # Run BFS-augment twice (we only need to confirm flow ≥ 2)
        flow = 0
        for _ in range(2):
            # BFS to find an augmenting path
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

            if not found:
                break   # no more augmenting paths

            # Trace path and update residual capacities
            node = dst
            while node != src:
                prev = parent[node]
                residual[prev][node] -= 1
                residual[node][prev] += 1
                node = prev
            flow += 1

        return flow >= 2

    # ── GA operators ─────────────────────────────────────────────────────
    def _tournament_select(self, population, scored):
        """Tournament selection: pick k random individuals, return the best."""
        contestants = random.sample(range(len(population)), min(self.tournament_k, len(population)))
        best_idx    = max(contestants, key=lambda i: scored[i][0])
        return population[best_idx][:]

    def _crossover(self, p1, p2):
        """Two-point crossover."""
        if random.random() > self.p_crossover or len(p1) < 3:
            return p1[:], p2[:]
        n  = len(p1)
        i1 = random.randint(0, n - 2)
        i2 = random.randint(i1 + 1, n - 1)
        c1 = p1[:i1] + p2[i1:i2] + p1[i2:]
        c2 = p2[:i1] + p1[i1:i2] + p2[i2:]
        return c1, c2

    def _mutate(self, chromosome):
        """Bit-flip mutation at rate p_mutation per gene."""
        return [
            1 - bit if random.random() < self.p_mutation else bit
            for bit in chromosome
        ]

    # ── Decode best chromosome into road list ─────────────────────────────
    def _decode_result(self):
        ch = self.best_chromosome
        self.built_roads = [
            (self.canonical_edges[i][0], self.canonical_edges[i][1], self.canonical_edges[i][2])
            for i in range(len(ch)) if ch[i] == 1
        ]
        self.total_cost       = sum(r[2] for r in self.built_roads)
        self.safety_satisfied = self._has_two_independent_paths(ch)

    # ── Final report ──────────────────────────────────────────────────────
    def _report(self):
        print("\n" + "=" * 62)
        print("   CHALLENGE 2 – Road Network Optimisation (GA) Report")
        print("=" * 62)
        print(f"  Algorithm         : Genetic Algorithm")
        print(f"  Total nodes       : {len(self.all_nodes)}")
        print(f"  Candidate edges   : {len(self.canonical_edges)}")
        print(f"  Roads built       : {len(self.built_roads)}")
        print(f"  Total road cost   : {self.total_cost:.2f}")

        connected = self._is_connected(self.best_chromosome)
        print(f"  Fully connected   : {'✓ YES' if connected else '✗ NO'}")

        if self.hospital_pos and self.ambulance_pos:
            status = "✓ SATISFIED" if self.safety_satisfied else "✗ VIOLATED"
            print(f"  Safety constraint : {status}")
            print(f"  Hospital position : {self.hospital_pos}")
            print(f"  Ambulance Depot   : {self.ambulance_pos}")
        else:
            print("  Safety constraint : N/A (Hospital or Ambulance Depot not found)")

        print(f"\n  Built roads (sorted by cost):")
        print("  " + "-" * 50)
        nodes = self.graph.nodes
        for u, v, cost in sorted(self.built_roads, key=lambda r: r[2]):
            type_u = nodes[u].NodeType or "?"
            type_v = nodes[v].NodeType or "?"
            print(f"  {u}[{type_u}]  ↔  {v}[{type_v}]   cost={cost:.2f}")
        print("=" * 62 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
#  Standalone test  –  run directly:  python RoadNetwork.py
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    from CityGraph import CityGraph
    from my_CSP       import CSP
    from Algorithm import Algorithms

    # ── Step 1: Build city layout (Challenge 1 – CSP) ────────────────────
    print("=" * 62)
    print("  Step 1 – Building city layout via CSP (Challenge 1)")
    print("=" * 62)
    g   = CityGraph(4, 4)
    csp = CSP(g)
    alg = Algorithms()

    solution = alg.ForwardChecking(csp, g)
    if solution is None:
        print("[ERROR] CSP could not find a valid city layout.")
        sys.exit(1)

    print("\nCity layout (node types assigned by CSP):")
    for r in range(g.rows):
        row_str = " | ".join(
            f"{g.nodes[(r, c)].NodeType[:4]:>4}" for c in range(g.cols)
        )
        print(f"  Row {r}: {row_str}")

    # ── Step 2: Build road network (Challenge 2 – GA) ────────────────────
    print("\n" + "=" * 62)
    print("  Step 2 – Road network optimisation (Challenge 2 – GA)")
    print("=" * 62 + "\n")

    rn = RoadNetwork(
        g,
        population_size=80,
        generations=200,
        p_mutation=0.02,
        elite_count=5,
    )
    rn.build()
