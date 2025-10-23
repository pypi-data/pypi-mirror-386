"""
Centrality-based anomaly detection.

Uses degree, betweenness, and closeness centrality to detect anomalous nodes.
"""

import time

import networkx as nx
import numpy as np

from argus_uav.detection import AnomalyDetector
from argus_uav.evaluation import DetectionResult
from argus_uav.utils.logging_config import get_logger

logger = get_logger(__name__)


class CentralityDetector(AnomalyDetector):
    """
    Detects anomalies using centrality metrics.

    Monitors:
    - Degree centrality: number of connections (high degree = suspicious)
    - Betweenness centrality: bridge nodes (unusual values = suspicious)
    - Closeness centrality: distance to other nodes

    Phantom UAVs often have unusual centrality patterns compared to
    legitimate UAVs in normal operation.
    """

    def __init__(self, name: str = "centrality", threshold: float = 2.0):
        """
        Initialize centrality detector.

        Args:
            name: Detector identifier
            threshold: Standard deviations for anomaly threshold
        """
        super().__init__(name)
        self.threshold = threshold

        # Baseline statistics
        self.mean_degree: float = 0.0
        self.std_degree: float = 0.0
        self.mean_betweenness: float = 0.0
        self.std_betweenness: float = 0.0
        self.mean_closeness: float = 0.0
        self.std_closeness: float = 0.0

    def train(self, clean_graphs: list[nx.Graph]) -> None:
        """
        Train detector on clean baseline graphs.

        Args:
            clean_graphs: Time series of graphs without attacks

        Effects:
            Computes and stores baseline centrality statistics
        """
        self.baseline_graphs = clean_graphs

        if not clean_graphs:
            logger.warning("No clean graphs provided for training")
            return

        # Collect centrality values across all baseline graphs
        all_degrees = []
        all_betweenness = []
        all_closeness = []

        for graph in clean_graphs:
            if len(graph.nodes()) == 0:
                continue

            # Degree centrality
            degree_cent = nx.degree_centrality(graph)
            all_degrees.extend(degree_cent.values())

            # Betweenness centrality
            betweenness_cent = nx.betweenness_centrality(graph)
            all_betweenness.extend(betweenness_cent.values())

            # Closeness centrality (only for connected components)
            if nx.is_connected(graph):
                closeness_cent = nx.closeness_centrality(graph)
                all_closeness.extend(closeness_cent.values())

        # Compute statistics
        if all_degrees:
            self.mean_degree = np.mean(all_degrees)
            self.std_degree = np.std(all_degrees)

        if all_betweenness:
            self.mean_betweenness = np.mean(all_betweenness)
            self.std_betweenness = np.std(all_betweenness)

        if all_closeness:
            self.mean_closeness = np.mean(all_closeness)
            self.std_closeness = np.std(all_closeness)

        logger.info(f"Centrality detector trained on {len(clean_graphs)} graphs")
        logger.debug(f"  Mean degree: {self.mean_degree:.4f} ± {self.std_degree:.4f}")
        logger.debug(
            f"  Mean betweenness: {self.mean_betweenness:.4f} ± {self.std_betweenness:.4f}"
        )

    def detect(self, graph: nx.Graph) -> DetectionResult:
        """
        Detect anomalies using centrality metrics.

        Args:
            graph: Current swarm graph to analyze

        Returns:
            DetectionResult with flagged UAVs and confidence scores
        """
        start_time = time.time()

        confidence_scores = {}
        anomalous_uav_ids = set()

        if len(graph.nodes()) == 0:
            detection_time = time.time() - start_time
            return DetectionResult(
                detector_name=self.name,
                timestamp=time.time(),
                anomalous_uav_ids=set(),
                confidence_scores={},
                ground_truth={},
                detection_time=detection_time,
            )

        # Compute current centrality metrics
        degree_cent = nx.degree_centrality(graph)
        betweenness_cent = nx.betweenness_centrality(graph)

        # Closeness only for connected components
        if nx.is_connected(graph):
            closeness_cent = nx.closeness_centrality(graph)
        else:
            # For disconnected graphs, compute per component
            closeness_cent = {}
            for component in nx.connected_components(graph):
                subgraph = graph.subgraph(component)
                if len(subgraph) > 1:
                    component_closeness = nx.closeness_centrality(subgraph)
                    closeness_cent.update(component_closeness)
                else:
                    # Single node component
                    closeness_cent[list(component)[0]] = 0.0

        # Compute anomaly scores for each node
        for node in graph.nodes():
            # Z-scores for each centrality metric
            degree_z = abs(degree_cent.get(node, 0) - self.mean_degree) / (
                self.std_degree + 1e-10
            )
            betweenness_z = abs(
                betweenness_cent.get(node, 0) - self.mean_betweenness
            ) / (self.std_betweenness + 1e-10)
            closeness_z = abs(closeness_cent.get(node, 0) - self.mean_closeness) / (
                self.std_closeness + 1e-10
            )

            # Combined score (weighted average)
            combined_score = 0.4 * degree_z + 0.4 * betweenness_z + 0.2 * closeness_z
            confidence_scores[node] = float(combined_score)

            # Flag if above threshold
            if combined_score > self.threshold:
                anomalous_uav_ids.add(node)

        # Get ground truth from graph node attributes if available
        ground_truth = {}
        for node in graph.nodes():
            node_data = graph.nodes[node]
            if "uav" in node_data:
                uav = node_data["uav"]
                ground_truth[node] = uav.is_legitimate
            else:
                ground_truth[node] = True

        detection_time = time.time() - start_time

        logger.debug(
            f"Centrality detection: {len(anomalous_uav_ids)} anomalies detected"
        )

        return DetectionResult(
            detector_name=self.name,
            timestamp=time.time(),
            anomalous_uav_ids=anomalous_uav_ids,
            confidence_scores=confidence_scores,
            ground_truth=ground_truth,
            detection_time=detection_time,
        )
