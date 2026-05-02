import random

class my_AmbulanceReplacement:
    def __init__(self):
        self.graph = {}
        self.Population = []
        self.fitnessScores = {}
        self.POPULATION_SIZE = 20
        self.parent1 = []
        self.parent2 = []

        self.WEIGHTS = {
            "Hospital":       2,
            "Residential":    3,
            "School":         1,
            "Industrial":     1,
            "Power Plant":    1,
            "Ambulance Depot":0,
            "":               0
        }

        #  added (minimal)
        self.important_nodes = []
        self.distance_map = {}

    # --------------------------------------------------
    #  PREPROCESS (runs once, no heavy work later)
    # --------------------------------------------------
    def preprocess(self):
        for node in self.graph.nodes.values():
            if node.NodeType in ["Hospital", "Residential"]:
                self.important_nodes.append(node)

        for node in self.graph.nodes.values():
            self.distance_map[node] = []
            for imp in self.important_nodes:
                d = abs(node.Coordinates_X - imp.Coordinates_X) + abs(node.Coordinates_Y - imp.Coordinates_Y)
                self.distance_map[node].append((d, imp.NodeType))

    # --------------------------------------------------

    def calculateRowDensity(self, chromo):  
        FinalValue = 0
        for node in chromo:
            #  removed heavy row scan
            #  replaced with precomputed lookup
            for d, nodeType in self.distance_map[node]:
                weight = self.WEIGHTS.get(nodeType, 1)
                FinalValue += weight / (d + 1)
        return FinalValue

    def calculateColDensity(self, chromo):
        #  no longer needed heavy column scan
        return 0

    def populate(self):
        self.Population = []  #  reset bug fix
        all_nodes = list(self.graph.nodes.values())
        for _ in range(self.POPULATION_SIZE):
            chromosome = random.sample(all_nodes, 3)
            self.Population.append(chromosome)

    def calculateFitness(self):  
        self.fitnessScores = {}  #  reset
        for chromosome in self.Population:
            Fvalue = self.calculateRowDensity(chromosome) + self.calculateColDensity(chromosome)
            self.fitnessScores[tuple(chromosome)] = Fvalue

    def ParentSelection(self):
        #  sorted.list → fixed
        sorted_chromosomes = sorted(
            self.Population,
            key=lambda chromosome: self.fitnessScores.get(tuple(chromosome), 0),
            reverse=True  #  take best
        )

        self.parent1 = sorted_chromosomes[0][:]
        self.parent2 = sorted_chromosomes[1][:]

        return self.parent1, self.parent2
    
    def crossover(self):
        #  overwrite bug → fixed swap
        Node1 = self.parent1[2]
        Node2 = self.parent2[2]

        self.parent1[2] = Node2
        self.parent2[2] = Node1
    
    def Replacment(self):
        # minimal implementation (no fancy logic)
        sorted_pop = sorted(
            self.Population,
            key=lambda c: self.fitnessScores.get(tuple(c), 0)
        )

        sorted_pop[0] = self.parent1
        sorted_pop[1] = self.parent2

        self.Population = sorted_pop

    def mutate(self, chromosome):
        #  very light mutation (optional but important)
        idx = random.randint(0, 2)
        new_node = random.choice(list(self.graph.nodes.values()))
        chromosome[idx] = new_node

    def InitiateGA(self, city_graph):
        self.graph = city_graph

        # added once
        self.preprocess()

        self.populate()

        #  loop added (your idea: rows generations)
        for _ in range(self.graph.rows):
            self.calculateFitness()
            self.ParentSelection()
            self.crossover()

            # small mutation chance
            if random.random() < 0.2:
                self.mutate(self.parent1)
            if random.random() < 0.2:
                self.mutate(self.parent2)

            self.Replacment()

        # final best
        self.calculateFitness()
        best = max(self.Population, key=lambda c: self.fitnessScores.get(tuple(c), 0))

        return best