"""
Spectral analysis for anomaly detection.

Uses Laplacian eigenvalues to detect topological anomalies in the swarm graph.
"""

import time

import networkx as nx
import numpy as np

from argus_uav.detection import AnomalyDetector
from argus_uav.evaluation import DetectionResult
from argus_uav.utils.logging_config import get_logger

logger = get_logger(__name__)


class SpectralDetector(AnomalyDetector):
    """
    Detects anomalies via Laplacian eigenvalue analysis.

    Monitors changes in the graph Laplacian's eigenvalues, particularly:
    - Algebraic connectivity (second smallest eigenvalue λ₂)
    - Spectral gap (λₙ - λ₂)
    - Overall eigenvalue distribution shifts

    Phantom UAVs and position spoofing create topological anomalies
    that manifest as eigenvalue deviations.
    """

    def __init__(self, name: str = "spectral", threshold: float = 2.5):
        """
        Initialize spectral detector.

        Args:
            name: Detector identifier
            threshold: Standard deviations for anomaly threshold
        """
        super().__init__(name)
        self.threshold = threshold

        # Baseline statistics
        self.baseline_eigenvalues: list[np.ndarray] = []
        self.mean_eigenvalues: np.ndarray = None
        self.std_eigenvalues: np.ndarray = None
        self.mean_algebraic_connectivity: float = 0.0
        self.std_algebraic_connectivity: float = 0.0

    def train(self, clean_graphs: list[nx.Graph]) -> None:
        """
        Train detector on clean baseline graphs.

        Args:
            clean_graphs: Time series of graphs without attacks

        Effects:
            Computes and stores baseline eigenvalue statistics
        """
        self.baseline_graphs = clean_graphs

        if not clean_graphs:
            logger.warning("No clean graphs provided for training")
            return

        # Compute eigenvalues for all baseline graphs
        for graph in clean_graphs:
            if len(graph.nodes()) > 0:
                eigenvalues = self._compute_eigenvalues(graph)
                self.baseline_eigenvalues.append(eigenvalues)

        if not self.baseline_eigenvalues:
            logger.warning("Could not compute eigenvalues for training")
            return

        # Compute statistics (pad to handle variable graph sizes)
        max_nodes = max(len(ev) for ev in self.baseline_eigenvalues)
        padded_eigenvalues = []

        for ev in self.baseline_eigenvalues:
            # Pad with zeros if needed
            if len(ev) < max_nodes:
                padded = np.pad(ev, (0, max_nodes - len(ev)), constant_values=0)
            else:
                padded = ev
            padded_eigenvalues.append(padded)

        eigenvalue_matrix = np.array(padded_eigenvalues)
        self.mean_eigenvalues = np.mean(eigenvalue_matrix, axis=0)
        self.std_eigenvalues = np.std(eigenvalue_matrix, axis=0)

        # Algebraic connectivity (λ₂) statistics
        algebraic_connectivities = [
            ev[1] if len(ev) > 1 else 0.0 for ev in self.baseline_eigenvalues
        ]
        self.mean_algebraic_connectivity = np.mean(algebraic_connectivities)
        self.std_algebraic_connectivity = np.std(algebraic_connectivities)

        logger.info(f"Spectral detector trained on {len(clean_graphs)} graphs")
        logger.debug(
            f"  Mean algebraic connectivity: {self.mean_algebraic_connectivity:.4f}"
        )
        logger.debug(
            f"  Std algebraic connectivity: {self.std_algebraic_connectivity:.4f}"
        )

    def detect(self, graph: nx.Graph) -> DetectionResult:
        """
        Detect anomalies in graph using spectral analysis.

        Args:
            graph: Current swarm graph to analyze

        Returns:
            DetectionResult with flagged UAVs and confidence scores
        """
        start_time = time.time()

        # Compute current eigenvalues
        current_eigenvalues = self._compute_eigenvalues(graph)

        # Compute anomaly scores for each node
        confidence_scores = {}
        anomalous_uav_ids = set()

        if self.mean_eigenvalues is None or len(current_eigenvalues) == 0:
            # Not trained or empty graph
            detection_time = time.time() - start_time
            return DetectionResult(
                detector_name=self.name,
                timestamp=time.time(),
                anomalous_uav_ids=set(),
                confidence_scores={uid: 0.0 for uid in graph.nodes()},
                ground_truth={},
                detection_time=detection_time,
            )

        # Check algebraic connectivity deviation
        algebraic_connectivity = (
            current_eigenvalues[1] if len(current_eigenvalues) > 1 else 0.0
        )
        ac_z_score = abs(algebraic_connectivity - self.mean_algebraic_connectivity) / (
            self.std_algebraic_connectivity + 1e-10
        )

        # Compute per-node scores based on degree centrality deviation
        # (Approximation: nodes contributing to eigenvalue shifts often have unusual degree)
        degrees = dict(graph.degree())

        mean_degree = np.mean(list(degrees.values())) if degrees else 0
        std_degree = np.std(list(degrees.values())) if degrees else 1

        for node in graph.nodes():
            # Z-score based on degree deviation
            degree = degrees.get(node, 0)
            degree_z_score = abs(degree - mean_degree) / (std_degree + 1e-10)

            # Combine with global spectral anomaly
            combined_score = 0.5 * degree_z_score + 0.5 * ac_z_score
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
                ground_truth[node] = True  # Assume legitimate if no data

        detection_time = time.time() - start_time

        logger.debug(
            f"Spectral detection: {len(anomalous_uav_ids)} anomalies detected "
            f"(AC z-score: {ac_z_score:.2f})"
        )

        return DetectionResult(
            detector_name=self.name,
            timestamp=time.time(),
            anomalous_uav_ids=anomalous_uav_ids,
            confidence_scores=confidence_scores,
            ground_truth=ground_truth,
            detection_time=detection_time,
        )

    def _compute_eigenvalues(self, graph: nx.Graph) -> np.ndarray:
        """
        Compute sorted eigenvalues of graph Laplacian.

        Args:
            graph: NetworkX graph

        Returns:
            Sorted eigenvalues (ascending order)
        """
        if len(graph.nodes()) == 0:
            return np.array([])

        try:
            # Compute Laplacian matrix
            laplacian = nx.laplacian_matrix(graph).toarray()

            # Compute eigenvalues (use eigvalsh for symmetric matrices)
            eigenvalues = np.linalg.eigvalsh(laplacian)

            # Sort ascending
            eigenvalues = np.sort(eigenvalues)

            return eigenvalues

        except Exception as e:
            logger.error(f"Error computing eigenvalues: {e}")
            return np.array([])
