import random

class my_AmbulanceReplacement:
    # Initialize GA parameters and response weights for demand nodes
    def __init__(self):
        self.graph = {}
        self.Population = []
        self.fitnessScores = {}
        self.POPULATION_SIZE = 30
        self.NUM_GENERATIONS = 100 
        self.parent1 = []
        self.parent2 = []
        self.WEIGHTS = {
            "Hospital":       2,
            "Residential":    3,
            "School":         1,
            "Industrial":     1,
            "Power Plant":    1,
            "Ambulance Depot":0,
            "":                0
        }
        self.important_nodes = []
        self.distance_map = {}

    # Identify demand nodes and pre-calculate distances to optimize fitness loop
    def preprocess(self):
        for node in self.graph.nodes.values():
            if node.NodeType in ["Hospital", "Residential", "School"]:
                self.important_nodes.append(node)

        for node in self.graph.nodes.values():
            self.distance_map[node] = []
            for imp in self.important_nodes:
                d = abs(node.Coordinates_X - imp.Coordinates_X) + abs(node.Coordinates_Y - imp.Coordinates_Y)
                self.distance_map[node].append((d, imp.NodeType))

    # Calculate minimax fitness to minimize the worst-case response distance
    def calculateFitnessValue(self, chromo):
        worst_response = 0 

        for imp_node in self.important_nodes:
            best_dist = float('inf')
            for amb_node in chromo:
                d = (abs(imp_node.Coordinates_X - amb_node.Coordinates_X) +
                     abs(imp_node.Coordinates_Y - amb_node.Coordinates_Y))
                weight = self.WEIGHTS.get(imp_node.NodeType, 1)
                weighted_d = d * weight
                if weighted_d < best_dist:
                    best_dist = weighted_d

            if best_dist > worst_response:
                worst_response = best_dist

        coverage_bonus = self._coverage_score(chromo)
        return -worst_response + coverage_bonus * 0.01

    # Secondary objective to favor chromosomes with better overall proximity
    def _coverage_score(self, chromo):
        total = 0
        for amb_node in chromo:
            for node_data in self.distance_map.get(amb_node, []):
                d, nt = node_data
                total += self.WEIGHTS.get(nt, 1) / (d + 1)
        return total

    # Generate initial population from accessible nodes
    def populate(self):
        self.Population = []
        accessible_nodes = [n for n in self.graph.nodes.values() if n.Accessibility_flag]
        if len(accessible_nodes) < 3:
            accessible_nodes = list(self.graph.nodes.values())

        for _ in range(self.POPULATION_SIZE):
            chromosome = random.sample(accessible_nodes, 3)
            self.Population.append(chromosome)

    # Compute fitness for every chromosome in current population
    def calculateFitness(self):  
        self.fitnessScores = {}
        for chromosome in self.Population:
            self.fitnessScores[tuple(chromosome)] = self.calculateFitnessValue(chromosome)

    # Select top-performing individuals for reproduction
    def ParentSelection(self):
        sorted_chromosomes = sorted(
            self.Population,
            key=lambda chromosome: self.fitnessScores.get(tuple(chromosome), float('-inf')),
            reverse=True 
        )
        self.parent1 = sorted_chromosomes[0][:]
        self.parent2 = sorted_chromosomes[1][:]
        return self.parent1, self.parent2
    
    # Perform single-point crossover and resolve coordinate duplicates
    def crossover(self):
        Node1 = self.parent1[2]
        Node2 = self.parent2[2]
        self.parent1[2] = Node2
        self.parent2[2] = Node1
        self._fix_duplicates(self.parent1)
        self._fix_duplicates(self.parent2)

    # Ensure unique spatial positions within a single chromosome
    def _fix_duplicates(self, chromo):
        accessible = [n for n in self.graph.nodes.values() if n.Accessibility_flag]
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
    
    # Elitist replacement of the least fit individuals with new offspring
    def Replacment(self):
        sorted_pop = sorted(
            self.Population,
            key=lambda c: self.fitnessScores.get(tuple(c), float('-inf'))
        )
        sorted_pop[0] = self.parent1
        sorted_pop[1] = self.parent2
        self.Population = sorted_pop

    # Apply random perturbation to a chromosome node
    def mutate(self, chromosome):
        accessible = [n for n in self.graph.nodes.values() if n.Accessibility_flag]
        idx = random.randint(0, 2)
        for _ in range(50):
            new_node = random.choice(accessible)
            new_pos = (new_node.Coordinates_X, new_node.Coordinates_Y)
            existing = {(c.Coordinates_X, c.Coordinates_Y) for c in chromosome}
            if new_pos not in existing:
                chromosome[idx] = new_node
                break

    # Main GA entry point for ambulance reallocation
    def InitiateGA(self, city_graph):
        self.graph = city_graph
        self.preprocess()
        self.populate()

        for gen in range(self.NUM_GENERATIONS):
            self.calculateFitness()
            self.ParentSelection()
            self.crossover()

            if random.random() < 0.2:
                self.mutate(self.parent1)
            if random.random() < 0.2:
                self.mutate(self.parent2)

            self.Replacment()

        self.calculateFitness()
        best = max(self.Population, key=lambda c: self.fitnessScores.get(tuple(c), float('-inf')))
        
        worst_dist = -self.fitnessScores.get(tuple(best), 0)
        print(f"\n[Challenge 3] Ambulance Placement (GA) complete.")
        print(f"  Worst-case response distance: {worst_dist:.2f}")

        return best