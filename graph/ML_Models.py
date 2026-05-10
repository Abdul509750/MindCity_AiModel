import random

class RiskClusterer:
    # Initialize with city graph and target cluster count
    def __init__(self, city_graph, k=3):
        self.graph = city_graph
        self.k = k  

    # Extract normalized population, industrial proximity, and type-based risk scores
    def _extract_and_normalize_features(self):
        industrial_zones = [pos for pos, node in self.graph.nodes.items() 
                            if node.NodeType == "Industrial"]
        if not industrial_zones:
            industrial_zones = [(0, 0)] 

        TYPE_SCORES = {
            "Industrial":      1.0,
            "Residential":     0.7,
            "School":          0.4,
            "Hospital":        0.3,
            "Power Plant":     0.5,
            "Ambulance Depot": 0.2,
            "":                0.0
        }

        distances = {}
        max_pop = 1
        max_dist = 1

        for pos, node in self.graph.nodes.items():
            r, c = pos
            min_dist = min(abs(r - ir) + abs(c - ic) for ir, ic in industrial_zones)
            distances[pos] = min_dist
            
            pop = getattr(node, 'PopulationDensity', 0)
            max_pop = max(max_pop, pop)
            max_dist = max(max_dist, min_dist)

        max_dist = max(max_dist, 1)

        features = {}
        for pos, node in self.graph.nodes.items():
            pop = getattr(node, 'PopulationDensity', 0)
            dist = distances[pos]
            type_score = TYPE_SCORES.get(node.NodeType, 0.0)
            features[pos] = (pop / max_pop, dist / max_dist, type_score)

        return features

    # Execute K-Means clustering in 3D feature space until convergence or max iterations
    def run_kmeans(self):
        features = self._extract_and_normalize_features()
        positions = list(features.keys())
        centroids = random.sample(list(features.values()), self.k)
        clusters = {}

        for iteration in range(100):
            new_clusters = {i: [] for i in range(self.k)}
            for pos in positions:
                feat = features[pos]
                best_i = min(range(self.k), key=lambda i: sum(
                    (feat[d] - centroids[i][d])**2 for d in range(len(feat))
                ))
                new_clusters[best_i].append(pos)

            if clusters == new_clusters:
                print(f"[Challenge 5: Unsupervised] K-Means converged at iteration {iteration+1}.")
                break
            clusters = new_clusters

            for i in range(self.k):
                if not clusters[i]:
                    continue
                n_dims = len(centroids[i])
                new_centroid = []
                for d in range(n_dims):
                    new_centroid.append(
                        sum(features[pos][d] for pos in clusters[i]) / len(clusters[i])
                    )
                centroids[i] = tuple(new_centroid)
        else:
            print(f"[Challenge 5: Unsupervised] K-Means completed 100 iterations (max).")

        for i in range(self.k):
            size = len(clusters.get(i, []))
            print(f"  Cluster {i}: {size} nodes")

        print(f"[Challenge 5: Unsupervised] K-Means produced {self.k} distinct demographic clusters.")
        return clusters, features

class CrimePredictor:
    # Initialize with graph and pre-computed features
    def __init__(self, graph, features):
        self.graph = graph
        self.features = features 
        self.dataset = {} 

    # Generate weighted risk labels using population, proximity, and type scores
    def generate_synthetic_data(self):
        for pos, feat in self.features.items():
            pop = feat[0] 
            dist = feat[1] 
            type_score = feat[2] 

            base_score = (pop * 0.4) + ((1.0 - dist) * 0.35) + (type_score * 0.25)
            score = base_score + random.uniform(-0.1, 0.1)
            
            if score > 0.65:
                self.dataset[pos] = "High"
            elif score > 0.35:
                self.dataset[pos] = "Medium"
            else:
                self.dataset[pos] = "Low"

        counts = {"High": 0, "Medium": 0, "Low": 0}
        for label in self.dataset.values():
            counts[label] += 1
        print(f"[Challenge 5: Synthesis] Synthetic crime data generated — "
              f"High: {counts['High']}, Medium: {counts['Medium']}, Low: {counts['Low']}")

    # Perform KNN classification and update node risk indices
    def train_and_predict_knn(self, k=5):
        predictions = {}
        correct = 0
        total = 0
        
        for pos_target, feat_target in self.features.items():
            distances = []
            for pos_train, feat_train in self.features.items():
                if pos_target == pos_train: 
                    continue
                feat_dist = sum(abs(feat_target[d] - feat_train[d]) 
                               for d in range(len(feat_target)))
                distances.append((feat_dist, self.dataset[pos_train]))
                
            distances.sort(key=lambda x: x[0])
            nearest_neighbors = distances[:k]
            
            votes = {"High": 0, "Medium": 0, "Low": 0}
            for _, label in nearest_neighbors:
                votes[label] += 1
                
            predicted_label = max(votes, key=votes.get)
            predictions[pos_target] = predicted_label
            self.graph.nodes[pos_target].setRiskIndex(predicted_label)

            if predicted_label == self.dataset[pos_target]:
                correct += 1
            total += 1
            
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"[Challenge 5: Supervised] KNN Classification complete. "
              f"Node risks updated. Accuracy: {accuracy:.1f}%")
        return predictions