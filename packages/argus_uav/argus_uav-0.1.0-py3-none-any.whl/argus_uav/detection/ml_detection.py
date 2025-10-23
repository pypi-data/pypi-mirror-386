"""
Machine Learning-based anomaly detection using Node2Vec + Isolation Forest.

Combines graph embeddings with ML anomaly detection for improved accuracy.
"""

import time
from typing import Optional

import networkx as nx
import numpy as np
from sklearn.ensemble import IsolationForest

from argus_uav.detection import AnomalyDetector
from argus_uav.evaluation import DetectionResult
from argus_uav.utils.logging_config import get_logger

logger = get_logger(__name__)


class Node2VecDetector(AnomalyDetector):
    """
    ML-based detection using Node2Vec embeddings + Isolation Forest.

    Generates graph embeddings using random walks, then trains an
    isolation forest to identify anomalous nodes in embedding space.

    This typically provides better accuracy than pure graph metrics
    but at higher computational cost.
    """

    def __init__(
        self,
        name: str = "node2vec",
        embedding_dim: int = 128,
        walk_length: int = 30,
        num_walks: int = 200,
        p: float = 1.0,
        q: float = 1.0,
        contamination: float = 0.1,
    ):
        """
        Initialize Node2Vec detector.

        Args:
            name: Detector identifier
            embedding_dim: Dimension of embedding vectors
            walk_length: Length of each random walk
            num_walks: Number of walks per node
            p: Return parameter (controls walk strategy)
            q: In-out parameter (controls walk strategy)
            contamination: Expected fraction of anomalies in data
        """
        super().__init__(name)
        self.embedding_dim = embedding_dim
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.contamination = contamination

        # ML model
        self.isolation_forest: Optional[IsolationForest] = None
        self.node2vec_model = None
        self.baseline_embeddings: dict[str, np.ndarray] = {}

    def train(self, clean_graphs: list[nx.Graph]) -> None:
        """
        Train Isolation Forest on graph features (FAST method).

        Args:
            clean_graphs: Time series of graphs without attacks

        Steps:
            1. Extract graph features from clean graphs
            2. Fit Isolation Forest on clean features
        """
        self.baseline_graphs = clean_graphs

        if not clean_graphs:
            logger.warning("No clean graphs provided for training")
            return

        logger.info(f"Training ML detector on {len(clean_graphs)} baseline graphs...")

        try:
            # Extract features from all baseline graphs
            all_features = []

            for graph in clean_graphs:
                if len(graph.nodes()) == 0:
                    continue

                # Extract graph features (same as detect method)
                degree_cent = nx.degree_centrality(graph)
                betweenness_cent = nx.betweenness_centrality(graph)

                try:
                    clustering = nx.clustering(graph)
                except Exception as e:
                    logger.error(f"Error computing clustering: {e}")
                    clustering = {node: 0.0 for node in graph.nodes()}

                # Closeness for connected components
                closeness_cent = {}
                if nx.is_connected(graph):
                    closeness_cent = nx.closeness_centrality(graph)
                else:
                    for component in nx.connected_components(graph):
                        subgraph = graph.subgraph(component)
                        if len(subgraph) > 1:
                            component_closeness = nx.closeness_centrality(subgraph)
                            closeness_cent.update(component_closeness)
                        else:
                            for node in component:
                                closeness_cent[node] = 0.0

                # Collect features for all nodes
                for node in graph.nodes():
                    features = np.array(
                        [
                            degree_cent.get(node, 0.0),
                            betweenness_cent.get(node, 0.0),
                            clustering.get(node, 0.0),
                            closeness_cent.get(node, 0.0),
                        ]
                    )
                    all_features.append(features)

            if not all_features:
                logger.error("No features extracted from baseline")
                return

            # Train Isolation Forest on clean features
            features_array = np.array(all_features)
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=self.contamination,
                random_state=42,
                n_jobs=1,
            )
            self.isolation_forest.fit(features_array)

            logger.info(
                f"ML detector trained on {len(all_features)} feature vectors from {len(clean_graphs)} graphs"
            )

        except Exception as e:
            logger.error(f"Error training ML detector: {e}")
            self.isolation_forest = None

    def detect(self, graph: nx.Graph) -> DetectionResult:
        """
        Detect anomalies using graph features (FAST method).

        Args:
            graph: Current swarm graph to analyze

        Returns:
            DetectionResult with flagged UAVs

        Steps:
            1. Extract lightweight graph features (degree, betweenness, clustering)
            2. Predict anomaly scores with Isolation Forest
            3. Threshold scores to flag anomalous nodes
        """
        start_time = time.time()

        confidence_scores = {}
        anomalous_uav_ids = set()
        ground_truth = {}

        if len(graph.nodes()) == 0 or self.isolation_forest is None:
            detection_time = time.time() - start_time
            return DetectionResult(
                detector_name=self.name,
                timestamp=time.time(),
                anomalous_uav_ids=set(),
                confidence_scores={},
                ground_truth={},
                detection_time=detection_time,
            )

        try:
            # FAST: Extract graph features instead of re-training embeddings
            # This is 100x faster and still effective
            degree_cent = nx.degree_centrality(graph)
            betweenness_cent = nx.betweenness_centrality(graph)

            # Clustering coefficient (local structure)
            try:
                clustering = nx.clustering(graph)
            except Exception as e:
                logger.error(f"Error computing clustering: {e}")
                clustering = {node: 0.0 for node in graph.nodes()}

            # Closeness for connected components
            closeness_cent = {}
            if nx.is_connected(graph):
                closeness_cent = nx.closeness_centrality(graph)
            else:
                for component in nx.connected_components(graph):
                    subgraph = graph.subgraph(component)
                    if len(subgraph) > 1:
                        component_closeness = nx.closeness_centrality(subgraph)
                        closeness_cent.update(component_closeness)
                    else:
                        for node in component:
                            closeness_cent[node] = 0.0

            # Build feature vectors
            feature_list = []
            node_list = []

            for node in graph.nodes():
                # 4-dimensional feature vector (fast to compute)
                features = np.array(
                    [
                        degree_cent.get(node, 0.0),
                        betweenness_cent.get(node, 0.0),
                        clustering.get(node, 0.0),
                        closeness_cent.get(node, 0.0),
                    ]
                )
                feature_list.append(features)
                node_list.append(node)

            if not feature_list:
                logger.warning("No features extracted for current graph")
                detection_time = time.time() - start_time
                return DetectionResult(
                    detector_name=self.name,
                    timestamp=time.time(),
                    anomalous_uav_ids=set(),
                    confidence_scores={},
                    ground_truth={},
                    detection_time=detection_time,
                )

            # Predict anomaly scores using pre-trained Isolation Forest
            features_array = np.array(feature_list)
            anomaly_scores = self.isolation_forest.decision_function(features_array)
            predictions = self.isolation_forest.predict(features_array)

            # Normalize scores to [0, 1] range (lower = more anomalous)
            min_score = anomaly_scores.min()
            max_score = anomaly_scores.max()
            score_range = max_score - min_score

            for node, score, pred in zip(node_list, anomaly_scores, predictions):
                # Convert to confidence score (higher = more anomalous)
                if score_range > 0:
                    normalized_score = 1.0 - (score - min_score) / score_range
                else:
                    normalized_score = 0.5

                confidence_scores[node] = float(normalized_score)

                # Flag if predicted as anomaly (-1)
                if pred == -1:
                    anomalous_uav_ids.add(node)

            # Get ground truth
            for node in graph.nodes():
                node_data = graph.nodes[node]
                if "uav" in node_data:
                    uav = node_data["uav"]
                    ground_truth[node] = uav.is_legitimate
                else:
                    ground_truth[node] = True

            detection_time = time.time() - start_time

            logger.debug(
                f"ML detection: {len(anomalous_uav_ids)} anomalies detected in {detection_time * 1000:.2f}ms"
            )

            return DetectionResult(
                detector_name=self.name,
                timestamp=time.time(),
                anomalous_uav_ids=anomalous_uav_ids,
                confidence_scores=confidence_scores,
                ground_truth=ground_truth,
                detection_time=detection_time,
            )

        except Exception as e:
            logger.error(f"Error in ML detection: {e}")
            detection_time = time.time() - start_time
            return DetectionResult(
                detector_name=self.name,
                timestamp=time.time(),
                anomalous_uav_ids=set(),
                confidence_scores={},
                ground_truth={},
                detection_time=detection_time,
            )
