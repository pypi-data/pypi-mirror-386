<div align="center">
   <a href="https://github.com/Sang-Buster/Argus">
      <img src="https://raw.githubusercontent.com/Sang-Buster/Argus/refs/heads/main/assets/favicon.svg" width=20% alt="logo">
   </a>   
   <h1>Argus</h1>
   <a href="https://deepwiki.com/Sang-Buster/Argus"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
   <a href="https://pypi.org/project/argus_uav/"><img src="https://img.shields.io/pypi/v/argus_uav" alt="PyPI"></a>
   <a href="https://github.com/Sang-Buster/Argus/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Sang-Buster/Argus" alt="License"></a>
   <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
   <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
   <a href="https://github.com/Sang-Buster/Force-Fusion/commits/main"><img src="https://img.shields.io/github/last-commit/Sang-Buster/Argus" alt="Last Commit"></a>
   <h6 align="center"><small>A UAV Remote ID Spoofing Defense System.</small></h6>
   <p><b>#UAV Swarm Security &emsp; #Remote ID Spoofing &emsp; #Graph-Theoretic Modeling &emsp; #Cryptographic Defenses</b></p>
</div>

## Overview

Argus is a research framework for investigating UAV swarm vulnerabilities to Remote ID spoofing attacks. It combines graph-theoretic analysis with cryptographic defenses to detect and prevent:

- 🎭 **Phantom UAV Injection**: Non-existent UAVs broadcasting fake Remote ID messages
- 📍 **Position Falsification**: Legitimate UAVs reporting spoofed GPS coordinates
- 🔀 **Coordinated Attacks**: Multiple synchronized spoofers disrupting swarm consensus

### Key Features

- **Swarm Simulation**: Dynamic graph-based UAV network modeling with configurable parameters
- **Attack Injection**: Multiple spoofing scenarios with ground truth tracking
- **Detection Methods**:
  - Spectral analysis via Laplacian eigenvalues
  - Centrality-based anomaly detection
  - Machine learning with Node2Vec embeddings + isolation forests
  - Cryptographic verification with Ed25519 signatures (100% TPR, 0% FPR!)
- **Consensus Analysis**: Quantify attack impact on swarm coordination
- **Visualization**:
  - Publication-quality plots (ROC curves, heatmaps, comparisons) - 300 DPI PDF+PNG
  - **Live real-time animation** with PyQt5 - Watch UAVs move and attacks unfold!
  - Enhanced interactive visualization with detection overlay

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager

### From PyPI (Recommended)

```bash
# Install from PyPI
pip install argus_uav

# Verify installation
argus --help
```

### From Source (For Development)

```bash
# Clone the repository
git clone https://github.com/Sang-Buster/Argus.git
cd Argus

# Create virtual environment
uv v -p 3.10
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
argus --help
pytest tests/ -v
```

## Quick Start

### Interactive CLI (Recommended)

The easiest way to get started is with the interactive CLI:

```bash
# After installation, use the 'argus' command
argus

# Quick command-line usage
argus --attack phantom --detectors all --mode comparison

# See all options
argus --help
```

**See [CLI User Guide](docs/CLI.md) for complete documentation.**

The CLI provides:

- ✨ **Interactive mode** - guided experience for beginners
- 🎬 **Live visualization** - watch attacks and detection in real-time
- 📊 **Performance comparison** - automated benchmarking and plots
- 🎯 **All attacks & detectors** - test any combination of 3 attacks × 4 detection methods

### 1. Simulate a Clean UAV Swarm

```python
from argus_uav.core.swarm import Swarm
import numpy as np

# Create reproducible simulation
rng = np.random.default_rng(seed=42)
swarm = Swarm(
    num_uavs=20,
    comm_range=100.0,
    bounds=(1000, 1000, 200),
    rng=rng
)

# Run for 10 seconds
for t in range(10):
    swarm.step(dt=1.0)
    print(f"Time {t}s: {swarm.get_graph().number_of_edges()} links")
```

### 2. Inject and Detect Phantom UAVs

```python
from argus_uav.attacks.phantom_uav import PhantomInjector
from argus_uav.attacks import AttackScenario, AttackType
from argus_uav.detection.spectral import SpectralDetector

# Configure phantom attack
attack = AttackScenario(
    attack_type=AttackType.PHANTOM,
    start_time=5.0,
    duration=10.0,
    phantom_count=3
)

# Setup detection
detector = SpectralDetector()
detector.train([swarm.get_graph().copy() for _ in range(20)])

# Run with attack
injector = PhantomInjector()
for t in range(20):
    if attack.is_active(float(t)):
        injector.inject(swarm, attack, float(t))

    swarm.step(dt=1.0)
    result = detector.detect(swarm.get_graph())

    metrics = result.compute_metrics()
    print(f"TPR: {metrics['tpr']:.2%}, FPR: {metrics['fpr']:.2%}")
```

### 3. Compare All Detection Methods

```bash
# Run performance comparison with all detectors
argus --attack phantom --detectors all --mode comparison

# Live visualization with specific detectors
argus --attack coordinated --detectors spectral crypto --mode live

# Both live and comparison modes
argus --attack position --detectors centrality --mode both
```

## Project Structure

```
src/argus_uav/
├── core/              # Simulation engine (UAV, swarm, Remote ID)
├── attacks/           # Attack injection (phantom, position spoof, coordinated)
├── detection/         # Detection algorithms (spectral, centrality, ML)
├── crypto/            # Ed25519 signing and verification
├── consensus/         # Swarm consensus algorithms
├── evaluation/        # Metrics, visualizations, ROC curves
├── experiments/       # Experiment runner and configuration
└── utils/             # Random seeds, logging

tests/
├── unit/              # Unit tests for individual components
├── integration/       # End-to-end scenario tests
├── contract/          # Interface compliance tests
└── performance/       # Benchmark and profiling tests

examples/              # Example demonstrations and scripts
docs/                  # Documentation and examples
results/               # Experiment outputs (gitignored)
```

## Usage Examples

### Command-Line Options

```bash
# Interactive mode (recommended for beginners)
argus

# Quick demos
argus --attack phantom --detectors spectral --mode live
argus --attack position --detectors all --mode comparison
argus --attack coordinated --detectors crypto --mode both

# Custom swarm configuration
argus --attack phantom --detectors all --mode comparison \
    --num-uavs 50 --comm-range 150

# See all available options
argus --help
```

### Programmatic Usage

For advanced experiments with custom configurations, you can use the Python API directly. See the `examples/` directory for comprehensive demonstrations.

## Documentation

**📚 [Complete Documentation Index](docs/README.md)**

**Quick Links**:

- **[Quickstart Guide](docs/QUICKSTART.md)** - Get started in 10 minutes
- **[Project Status](docs/STATUS.md)** - Complete status & features
- **[Algorithm Details](docs/algorithm_details.md)** - Theory and implementation
- **[Data Formats](docs/data_formats.md)** - Specifications and schemas
- **[References](docs/references.md)** - 19 research paper citations

**Design Artifacts** (Spec Kit):

- [Specification](specs/001-uav-remote-id-defense/spec.md) - Requirements and user stories
- [Implementation Plan](specs/001-uav-remote-id-defense/plan.md) - Architecture decisions
- [Data Model](specs/001-uav-remote-id-defense/data-model.md) - Entity relationships

## Research Background

This project investigates defenses against Remote ID spoofing, a critical security challenge for UAV swarms. Remote ID is mandated by aviation authorities (FAA 14 CFR Part 89) but lacks authentication, making it vulnerable to falsified messages.

### Key Research Questions

1. Can graph-theoretic metrics detect topological anomalies from phantom UAVs?
2. How effective is machine learning (Node2Vec + isolation forests) vs pure graph analysis?
3. What is the performance overhead of Ed25519 cryptographic signing for real-time swarms?
4. How do spoofing attacks impact swarm consensus algorithms?

### Methodology

- **Simulation**: Software-only UAV swarm modeling (no hardware required)
- **Attack Scenarios**: Phantom injection, position falsification, coordinated spoofers
- **Detection**: Spectral analysis, centrality metrics, ML embeddings
- **Defense**: Ed25519 digital signatures for message authentication
- **Evaluation**: TPR, FPR, detection latency, consensus error

## Performance Benchmarks

Expected performance on modern laptop (8 cores, 16GB RAM):

| Operation                      | Time       |
| ------------------------------ | ---------- |
| Simulate 50 UAVs for 100 steps | ~5 seconds |
| Spectral detection (100 nodes) | ~40ms      |
| Node2Vec detection (100 nodes) | ~80ms      |
| Ed25519 signing                | ~0.05ms    |
| Ed25519 verification           | ~0.1ms     |

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=argus --cov-report=html

# Run specific test suites
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/performance/    # Performance benchmarks
```

## Contributing

This is a research project. Contributions are welcome! Areas of interest:

- Additional detection algorithms (GNNs, threshold signatures)
- Real-world Remote ID traffic datasets
- Hardware integration (RTL-SDR, physical UAVs)
- Scalability optimizations for larger swarms

## References

1. Peel, L., et al. (2015). "Detecting Change Points in Evolving Networks"
2. Olfati-Saber, R., & Murray, R. M. (2004). "Consensus Problems in Networks"
3. Grover, A., & Leskovec, J. (2016). "node2vec: Scalable Feature Learning"
4. Liu, F. T., et al. (2008). "Isolation Forest"
5. Bernstein, D. J., et al. (2012). "High-speed high-security signatures" (Ed25519)
