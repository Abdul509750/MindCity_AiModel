import random

from graph_paths import min_cost_from_sources


class my_AmbulanceReplacement:
    def __init__(self):
        self.graph = None
        self.Population = []
        self.fitnessScores = {}
        self.POPULATION_SIZE = 30
        self.NUM_GENERATIONS = 100
        self.parent1 = []
        self.parent2 = []
        self.demand_nodes = []

    def preprocess(self):
        self.demand_nodes = [
            n for n in self.graph.nodes.values()
            if n.NodeType in ("Residential", "School")
        ]

    def calculateFitnessValue(self, chromo):
        sources = [(n.Coordinates_X, n.Coordinates_Y) for n in chromo]
        dist = min_cost_from_sources(self.graph, sources)
        worst = 0.0
        for imp in self.demand_nodes:
            pos = (imp.Coordinates_X, imp.Coordinates_Y)
            d = dist.get(pos, float("inf"))
            if d == float("inf"):
                return -1e9
            worst = max(worst, d)
        return -worst

    def _candidate_cells(self):
        out = [
            n for n in self.graph.nodes.values()
            if n.Accessibility_flag and n.NodeType not in ("Hospital", "Ambulance Depot")
        ]
        return out if len(out) >= 3 else [n for n in self.graph.nodes.values() if n.Accessibility_flag]

    def populate(self):
        self.Population = []
        accessible_nodes = self._candidate_cells()
        if len(accessible_nodes) < 3:
            accessible_nodes = list(self.graph.nodes.values())

        for _ in range(self.POPULATION_SIZE):
            chromosome = random.sample(accessible_nodes, 3)
            self.Population.append(chromosome)

    def calculateFitness(self):
        self.fitnessScores = {}
        for chromosome in self.Population:
            self.fitnessScores[tuple(chromosome)] = self.calculateFitnessValue(chromosome)

    def ParentSelection(self):
        sorted_chromosomes = sorted(
            self.Population,
            key=lambda chromosome: self.fitnessScores.get(tuple(chromosome), float("-inf")),
            reverse=True,
        )
        self.parent1 = sorted_chromosomes[0][:]
        self.parent2 = sorted_chromosomes[1][:]
        return self.parent1, self.parent2

    def crossover(self):
        Node1 = self.parent1[2]
        Node2 = self.parent2[2]
        self.parent1[2] = Node2
        self.parent2[2] = Node1
        self._fix_duplicates(self.parent1)
        self._fix_duplicates(self.parent2)

    def _fix_duplicates(self, chromo):
        accessible = self._candidate_cells()
        seen = set()
        for i in range(len(chromo)):
            pos = (chromo[i].Coordinates_X, chromo[i].Coordinates_Y)
            if pos in seen:
                for _ in range(50):
                    replacement = random.choice(accessible)
                    rpos = (replacement.Coordinates_X, replacement.Coordinates_Y)
                    if rpos not in seen:
                        chromo[i] = replacement
                        pos = rpos
                        break
            seen.add(pos)

    def Replacment(self):
        sorted_pop = sorted(
            self.Population,
            key=lambda c: self.fitnessScores.get(tuple(c), float("-inf")),
        )
        sorted_pop[0] = self.parent1
        sorted_pop[1] = self.parent2
        self.Population = sorted_pop

    def mutate(self, chromosome):
        accessible = self._candidate_cells()
        idx = random.randint(0, 2)
        for _ in range(50):
            new_node = random.choice(accessible)
            new_pos = (new_node.Coordinates_X, new_node.Coordinates_Y)
            existing = {(c.Coordinates_X, c.Coordinates_Y) for c in chromosome}
            if new_pos not in existing:
                chromosome[idx] = new_node
                break

    def InitiateGA(self, city_graph):
        self.graph = city_graph
        self.preprocess()
        self.populate()

        for _ in range(self.NUM_GENERATIONS):
            self.calculateFitness()
            self.ParentSelection()
            self.crossover()

            if random.random() < 0.2:
                self.mutate(self.parent1)
            if random.random() < 0.2:
                self.mutate(self.parent2)

            self.Replacment()

        self.calculateFitness()
        best = max(self.Population, key=lambda c: self.fitnessScores.get(tuple(c), float("-inf")))
        fit = self.fitnessScores.get(tuple(best), 0)
        worst_cost = -fit if fit > -1e8 else float("inf")
        print("\n[Challenge 3] Ambulance Placement (GA) complete.")
        print(f"  Worst-case path cost (Residential/School): {worst_cost:.2f}")

        return best
