#!/usr/bin/env python3
"""
Argus - UAV Swarm Security CLI

Main interactive command-line interface for running experiments,
visualizations, and comparisons of different attacks and detection methods.
"""

import argparse
from pathlib import Path
from typing import List, Optional

import matplotlib

matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Patch

from argus_uav.attacks import AttackScenario, AttackType
from argus_uav.attacks.coordinated import CoordinatedInjector
from argus_uav.attacks.phantom_uav import PhantomInjector
from argus_uav.attacks.position_spoof import PositionFalsifier
from argus_uav.core.swarm import Swarm
from argus_uav.detection.centrality import CentralityDetector
from argus_uav.detection.crypto_detector import CryptoDetector
from argus_uav.detection.ml_detection import Node2VecDetector
from argus_uav.detection.spectral import SpectralDetector
from argus_uav.evaluation.metrics import MetricsCalculator


# ANSI color codes for terminal
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_banner():
    """Print ASCII art banner."""
    banner = f"""{Colors.OKBLUE}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗             ║
    ║    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝             ║
    ║    ███████║██████╔╝██║  ███╗██║   ██║███████╗             ║
    ║    ██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║             ║
    ║    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║             ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝             ║
    ║                                                           ║
    ║         UAV Swarm Security Testing Framework              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    {Colors.ENDC}"""
    print(banner)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def get_user_choice(prompt: str, options: List[str], default: int = 0) -> int:
    """Get user choice from a list of options."""
    print(f"{Colors.OKCYAN}{prompt}{Colors.ENDC}")
    for i, option in enumerate(options, 1):
        print(f"  {Colors.OKGREEN}{i}.{Colors.ENDC} {option}")

    while True:
        try:
            choice = input(
                f"\n{Colors.WARNING}Enter choice (1-{len(options)}) [default: {default + 1}]: {Colors.ENDC}"
            ).strip()
            if not choice:
                return default
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(options):
                return choice_num
            else:
                print(
                    f"{Colors.FAIL}Invalid choice. Please enter a number between 1 and {len(options)}.{Colors.ENDC}"
                )
        except ValueError:
            print(f"{Colors.FAIL}Invalid input. Please enter a number.{Colors.ENDC}")


def select_attack() -> tuple[AttackType, dict]:
    """Interactive attack selection."""
    print_section("ATTACK SELECTION")

    attack_options = [
        "Phantom UAV Attack (inject fake UAVs)",
        "Position Falsification Attack (spoof UAV locations)",
        "Coordinated Attack (multiple compromised UAVs)",
    ]

    choice = get_user_choice("Select attack type:", attack_options)

    # Attack-specific configuration
    attack_config = {}

    if choice == 0:  # Phantom
        attack_type = AttackType.PHANTOM
        print(
            f"\n{Colors.OKCYAN}Number of phantom UAVs to inject (1-10) [default: 5]: {Colors.ENDC}",
            end="",
        )
        count = input().strip()
        attack_config["phantom_count"] = int(count) if count else 5

    elif choice == 1:  # Position
        attack_type = AttackType.POSITION_FALSIFICATION
        print(
            f"\n{Colors.OKCYAN}Position offset magnitude in meters (1-100) [default: 50]: {Colors.ENDC}",
            end="",
        )
        mag = input().strip()
        attack_config["falsification_magnitude"] = float(mag) if mag else 50.0

    else:  # Coordinated
        attack_type = AttackType.COORDINATED
        print(
            f"\n{Colors.OKCYAN}Number of compromised UAVs (1-10) [default: 5]: {Colors.ENDC}",
            end="",
        )
        count = input().strip()
        attack_config["target_count"] = int(count) if count else 5

    # Common timing parameters
    print(
        f"\n{Colors.OKCYAN}Attack start time in seconds [default: 10]: {Colors.ENDC}",
        end="",
    )
    start = input().strip()
    attack_config["start_time"] = float(start) if start else 10.0

    print(
        f"\n{Colors.OKCYAN}Attack duration in seconds [default: 20]: {Colors.ENDC}",
        end="",
    )
    duration = input().strip()
    attack_config["duration"] = float(duration) if duration else 20.0

    return attack_type, attack_config


def select_detectors() -> List[str]:
    """Interactive detector selection."""
    print_section("DETECTION METHOD SELECTION")

    detector_options = [
        "Spectral Detection (eigenvalue analysis)",
        "Centrality Detection (betweenness/degree analysis)",
        "Cryptographic Detection (signature verification)",
        "ML Detection (trained classifier)",
        "All Methods (comparison mode)",
        "None (just show attack)",
    ]

    choice = get_user_choice("Select detection method(s):", detector_options)

    if choice == 4:  # All
        return ["spectral", "centrality", "crypto", "ml"]
    elif choice == 5:  # None
        return []
    else:
        detector_map = ["spectral", "centrality", "crypto", "ml"]
        return [detector_map[choice]]


def select_mode() -> str:
    """Select execution mode."""
    print_section("EXECUTION MODE")

    mode_options = [
        "Live Visualization (real-time animated display)",
        "Performance Comparison (generate metrics and plots)",
        "Both (live viz + save results)",
    ]

    choice = get_user_choice("Select execution mode:", mode_options)
    mode_map = ["live", "comparison", "both"]
    return mode_map[choice]


def run_live_visualization(
    attack_type: AttackType,
    attack_config: dict,
    detector_names: List[str],
    swarm_config: dict,
):
    """Run live animated visualization."""
    print_section("LIVE VISUALIZATION")

    print(
        f"{Colors.OKGREEN}Initializing swarm with {swarm_config['num_uavs']} UAVs...{Colors.ENDC}"
    )

    # Create swarm with crypto if crypto detector selected
    enable_crypto = "crypto" in detector_names
    rng = np.random.default_rng(seed=42)
    swarm = Swarm(
        num_uavs=swarm_config["num_uavs"],
        comm_range=swarm_config["comm_range"],
        bounds=swarm_config["bounds"],
        rng=rng,
        enable_crypto=enable_crypto,
    )

    # Setup attack scenario
    scenario = AttackScenario(
        attack_type=attack_type,
        start_time=attack_config["start_time"],
        duration=attack_config["duration"],
        phantom_count=attack_config.get("phantom_count", 0),
        falsification_magnitude=attack_config.get("falsification_magnitude", 0.0),
    )

    # Select injector
    if attack_type == AttackType.PHANTOM:
        injector = PhantomInjector()
    elif attack_type == AttackType.POSITION_FALSIFICATION:
        injector = PositionFalsifier()
    else:
        injector = CoordinatedInjector()

    # Train detectors
    detectors = {}
    if detector_names:
        print(f"\n{Colors.OKGREEN}Training detectors on baseline data...{Colors.ENDC}")
        # Step simulation to let UAVs generate messages before collecting baseline
        baseline = []
        for _ in range(20):
            swarm.step(dt=1.0)
            baseline.append(swarm.get_graph().copy())

        if "spectral" in detector_names:
            detectors["spectral"] = SpectralDetector(
                threshold=4.0
            )  # Further increased for lower FPR
            detectors["spectral"].train(baseline)
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Spectral trained")

        if "centrality" in detector_names:
            detectors["centrality"] = CentralityDetector(threshold=3.0)  # Good as is
            detectors["centrality"].train(baseline)
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Centrality trained")

        if "crypto" in detector_names:
            detectors["crypto"] = CryptoDetector()
            detectors["crypto"].train(baseline)
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Crypto trained")

        if "ml" in detector_names:
            detectors["ml"] = Node2VecDetector(contamination=0.05)
            detectors["ml"].train(baseline)
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} ML trained")

        # Reset swarm to t=0 for clean attack timing
        # Exception: For crypto, keep same swarm (needs same UAVs/keys)
        if "crypto" not in detector_names:
            swarm = Swarm(
                num_uavs=swarm_config["num_uavs"],
                comm_range=swarm_config["comm_range"],
                bounds=swarm_config["bounds"],
                rng=np.random.default_rng(seed=42),
                enable_crypto=enable_crypto,
            )
        else:
            # For crypto, just reset simulation time
            swarm.simulation_time = 0.0

    print(f"\n{Colors.OKGREEN}Starting visualization...{Colors.ENDC}")
    print(f"\n{Colors.OKCYAN}Color Legend:{Colors.ENDC}")
    print("  🟢 Green circle = Legitimate UAV")
    if enable_crypto:
        print("  🔵 Blue circle = Legitimate UAV (crypto enabled)")
    print("  🔴 Red X = Malicious/Phantom UAV")
    if detectors:
        print("  ⚠️  Yellow outline = Flagged by detector")

    print(f"\n{Colors.OKCYAN}Timeline:{Colors.ENDC}")
    print(f"   • t=0-{scenario.start_time}s:  Normal operation")
    print(
        f"   • t={scenario.start_time}-{scenario.start_time + scenario.duration}s: {attack_type.value.upper()} ATTACK"
    )
    print(f"   • t={scenario.start_time + scenario.duration}s+:   Attack removed")
    print(
        f"\n{Colors.WARNING}   ⚠️  Close window when finished viewing (or wait for auto-close){Colors.ENDC}"
    )
    print(
        f"{Colors.WARNING}   Animation runs until t={int(scenario.start_time + scenario.duration + 30)}s{Colors.ENDC}\n"
    )

    # Create figure
    fig, (ax_main, ax_stats) = plt.subplots(1, 2, figsize=(16, 8))

    # Data tracking
    time_history = []
    edge_history = []
    malicious_count_history = []
    detection_count_history = []

    attack_injected = False
    attack_removed = False

    def update(frame):
        nonlocal attack_injected, attack_removed

        current_time = swarm.simulation_time

        # Inject attack
        if scenario.is_active(current_time) and not attack_injected:
            injector.inject(swarm, scenario, current_time)
            attack_injected = True
            print(
                f"\n{Colors.FAIL}⚠️  {attack_type.value.upper()} attack injected at t={current_time:.1f}s!{Colors.ENDC}"
            )

        # Remove attack
        if (
            not scenario.is_active(current_time)
            and attack_injected
            and not attack_removed
        ):
            if hasattr(injector, "remove_phantoms"):
                injector.remove_phantoms(swarm)
            elif hasattr(injector, "remove_attack"):
                injector.remove_attack(swarm)
            attack_removed = True
            print(
                f"\n{Colors.OKGREEN}✓ Attack removed at t={current_time:.1f}s{Colors.ENDC}"
            )

        # Run detection
        detected_uavs = set()
        if detectors:
            graph = swarm.get_graph()
            for detector in detectors.values():
                result = detector.detect(graph)
                detected_uavs.update(result.anomalous_uav_ids)

        # Clear and redraw
        ax_main.clear()
        ax_main.set_xlim(0, swarm.bounds[0])
        ax_main.set_ylim(0, swarm.bounds[1])
        ax_main.set_xlabel("X Position (meters)", fontsize=11)
        ax_main.set_ylabel("Y Position (meters)", fontsize=11)
        ax_main.set_title(
            f"UAV Swarm - {attack_type.value.title()} Attack",
            fontsize=13,
            fontweight="bold",
        )
        ax_main.grid(True, alpha=0.3)
        ax_main.set_aspect("equal")

        # Draw communication links
        for u, v in swarm.graph.edges():
            uav_u = swarm.uavs[u]
            uav_v = swarm.uavs[v]
            ax_main.plot(
                [uav_u.position[0], uav_v.position[0]],
                [uav_u.position[1], uav_v.position[1]],
                "gray",
                alpha=0.2,
                linewidth=0.5,
            )

        # Draw UAVs
        for uav_id, uav in swarm.uavs.items():
            x, y = uav.position[0], uav.position[1]

            # Determine color and marker
            if not uav.is_legitimate:
                color = "red"
                marker = "X"
                size = 200
                edge_color = "darkred"
            elif uav.public_key is not None:
                color = "blue"
                marker = "o"
                size = 100
                edge_color = "darkblue"
            else:
                color = "green"
                marker = "o"
                size = 100
                edge_color = "darkgreen"

            # Add yellow outline if detected
            if uav_id in detected_uavs:
                edge_color = "yellow"
                linewidth = 3
            else:
                linewidth = 1.5

            ax_main.scatter(
                x,
                y,
                c=color,
                marker=marker,
                s=size,
                alpha=0.9,
                edgecolors=edge_color,
                linewidth=linewidth,
                zorder=10,
            )

            # Label malicious/detected UAVs
            if not uav.is_legitimate or uav_id in detected_uavs:
                ax_main.text(
                    x,
                    y + 25,
                    uav_id[:8],  # Shorten ID for display
                    fontsize=7,
                    ha="center",
                    fontweight="bold" if not uav.is_legitimate else "normal",
                )

        # Update statistics
        stats = swarm.get_statistics()
        time_history.append(current_time)
        edge_history.append(stats["num_edges"])
        num_malicious = sum(1 for u in swarm.uavs.values() if not u.is_legitimate)
        malicious_count_history.append(num_malicious)
        detection_count_history.append(len(detected_uavs))

        # Draw statistics
        ax_stats.clear()

        ax_stats_1 = ax_stats
        color_edges = "tab:blue"
        ax_stats_1.set_xlabel("Time (seconds)", fontsize=10)
        ax_stats_1.set_ylabel("Network Edges", color=color_edges, fontsize=10)
        ax_stats_1.plot(time_history, edge_history, color=color_edges, linewidth=2)
        ax_stats_1.tick_params(axis="y", labelcolor=color_edges)
        ax_stats_1.grid(True, alpha=0.3)

        ax_stats_2 = ax_stats_1.twinx()
        color_malicious = "tab:red"
        ax_stats_2.set_ylabel("Malicious UAVs", color=color_malicious, fontsize=10)
        ax_stats_2.plot(
            time_history, malicious_count_history, color=color_malicious, linewidth=2
        )
        ax_stats_2.tick_params(axis="y", labelcolor=color_malicious)

        # Highlight attack window
        if time_history and scenario.is_active(current_time):
            ax_stats_1.axvspan(
                scenario.start_time,
                scenario.start_time + scenario.duration,
                alpha=0.2,
                color="red",
            )

        ax_stats_1.set_title("Network Statistics Over Time", fontsize=11)

        # Status text
        status_text = f"Frame: {frame}\n"
        status_text += f"Time: {current_time:.1f}s\n"
        status_text += f"Legitimate: {stats['num_uavs'] - num_malicious}\n"
        status_text += f"Malicious: {num_malicious}\n"
        status_text += f"Total UAVs: {stats['num_uavs']}\n"
        status_text += f"Links: {stats['num_edges']}\n"
        if detectors:
            status_text += f"Detected: {len(detected_uavs)}"

        ax_main.text(
            0.02,
            0.02,
            status_text,
            transform=ax_main.transAxes,
            fontsize=10,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9),
        )

        # Legend
        legend_elements = [
            Patch(facecolor="green", edgecolor="darkgreen", label="Legitimate UAV"),
        ]
        if enable_crypto:
            legend_elements.append(
                Patch(
                    facecolor="blue", edgecolor="darkblue", label="Legitimate (crypto)"
                )
            )
        legend_elements.append(
            Patch(facecolor="red", edgecolor="darkred", label="Malicious UAV")
        )
        if detectors:
            legend_elements.append(
                Patch(
                    facecolor="white", edgecolor="yellow", linewidth=3, label="Detected"
                )
            )

        ax_main.legend(handles=legend_elements, loc="upper right", fontsize=9)

        # Step simulation
        swarm.step(dt=1.0)

    # Create animation - adjust duration based on attack timeline
    # Add 30s buffer after attack ends to observe recovery
    total_frames = int(attack_config["start_time"] + attack_config["duration"] + 30)
    _ = FuncAnimation(
        fig,
        update,
        frames=total_frames,
        interval=200,
        blit=False,
        repeat=False,
    )

    plt.tight_layout()
    plt.show()

    print(f"\n{Colors.OKGREEN}✅ Visualization complete!{Colors.ENDC}")


def run_performance_comparison(
    attack_type: AttackType,
    attack_config: dict,
    detector_names: List[str],
    swarm_config: dict,
    save_dir: Optional[Path] = None,
):
    """Run performance comparison and generate plots."""
    print_section("PERFORMANCE COMPARISON")

    if not detector_names:
        print(
            f"{Colors.FAIL}No detectors selected for comparison. Skipping.{Colors.ENDC}"
        )
        return

    print(
        f"{Colors.OKGREEN}Running experiments with {len(detector_names)} detector(s)...{Colors.ENDC}"
    )

    # Setup save directory
    if save_dir is None:
        save_dir = Path("results") / f"{attack_type.value}_comparison"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Run experiments
    results = {}

    for detector_name in detector_names:
        print(
            f"\n{Colors.OKCYAN}Testing {detector_name.upper()} detector...{Colors.ENDC}"
        )

        # Create fresh swarm
        enable_crypto = detector_name == "crypto"
        rng = np.random.default_rng(seed=42)
        swarm = Swarm(
            num_uavs=swarm_config["num_uavs"],
            comm_range=swarm_config["comm_range"],
            bounds=swarm_config["bounds"],
            rng=rng,
            enable_crypto=enable_crypto,
        )

        # Train detector - collect baseline after letting swarm stabilize
        baseline = []
        for _ in range(20):  # Collect 20 baseline samples
            swarm.step(dt=1.0)
            baseline.append(swarm.get_graph().copy())

        if detector_name == "spectral":
            detector = SpectralDetector(
                threshold=4.0
            )  # Further increased for lower FPR
        elif detector_name == "centrality":
            detector = CentralityDetector(threshold=3.0)  # Good as is
        elif detector_name == "crypto":
            detector = CryptoDetector()
        else:  # ml
            detector = Node2VecDetector(
                contamination=0.05
            )  # Lower contamination (less aggressive)

        detector.train(baseline)

        # Create fresh swarm for attack experiment (so timing starts from 0)
        # Exception: For crypto detector, keep same swarm since it needs the same UAVs/keys
        if detector_name != "crypto":
            swarm = Swarm(
                num_uavs=swarm_config["num_uavs"],
                comm_range=swarm_config["comm_range"],
                bounds=swarm_config["bounds"],
                rng=np.random.default_rng(seed=42),  # Same seed for reproducibility
                enable_crypto=enable_crypto,
            )
        else:
            # For crypto, reset simulation time but keep same swarm (same UAVs/keys)
            swarm.simulation_time = 0.0

        # Setup attack
        scenario = AttackScenario(
            attack_type=attack_type,
            start_time=attack_config["start_time"],
            duration=attack_config["duration"],
            phantom_count=attack_config.get("phantom_count", 0),
            falsification_magnitude=attack_config.get("falsification_magnitude", 0.0),
        )

        if attack_type == AttackType.PHANTOM:
            injector = PhantomInjector()
        elif attack_type == AttackType.POSITION_FALSIFICATION:
            injector = PositionFalsifier()
        else:
            injector = CoordinatedInjector()

        # Run simulation and collect metrics
        all_predictions = []
        all_ground_truths = []
        detection_times = []

        # Dynamic simulation duration based on attack timing
        sim_duration = int(
            scenario.start_time + scenario.duration + 20
        )  # Attack + 20s buffer

        for step in range(sim_duration):
            current_time = swarm.simulation_time

            if scenario.is_active(current_time) and step == int(scenario.start_time):
                injector.inject(swarm, scenario, current_time)

            if not scenario.is_active(current_time) and step == int(
                scenario.start_time + scenario.duration
            ):
                if hasattr(injector, "remove_phantoms"):
                    injector.remove_phantoms(swarm)
                elif hasattr(injector, "remove_attack"):
                    injector.remove_attack(swarm)

            # Detect
            import time

            start_time_detect = time.perf_counter()
            result = detector.detect(swarm.get_graph())
            detection_time = (time.perf_counter() - start_time_detect) * 1000
            detection_times.append(detection_time)

            # Collect results
            ground_truth = injector.get_ground_truth()
            all_predictions.append(result.anomalous_uav_ids)
            all_ground_truths.append(ground_truth)

            swarm.step(dt=1.0)

        # Compute aggregate metrics
        all_detected = set()
        for preds in all_predictions:
            all_detected.update(preds)

        final_ground_truth = all_ground_truths[-1]
        metrics = MetricsCalculator.compute_detection_metrics(
            all_detected, final_ground_truth
        )
        metrics["detection_time_ms"] = np.mean(detection_times)

        results[detector_name] = metrics

        print(
            f"  {Colors.OKGREEN}✓{Colors.ENDC} TPR: {metrics['tpr']:.3f}, FPR: {metrics['fpr']:.3f}, F1: {metrics['f1']:.3f}"
        )

    # Generate comparison visualizations
    print(f"\n{Colors.OKGREEN}Generating comparison plots...{Colors.ENDC}")

    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Detection Performance Comparison - {attack_type.value.title()} Attack",
        fontsize=14,
        fontweight="bold",
    )

    detector_labels = [d.capitalize() for d in detector_names]

    # Plot 1: TPR vs FPR
    ax = axes[0, 0]
    tprs = [results[d]["tpr"] for d in detector_names]
    fprs = [results[d]["fpr"] for d in detector_names]
    ax.scatter(fprs, tprs, s=200, alpha=0.6)
    for i, label in enumerate(detector_labels):
        ax.annotate(label, (fprs[i], tprs[i]), fontsize=9)
    ax.set_xlabel("False Positive Rate", fontsize=10)
    ax.set_ylabel("True Positive Rate", fontsize=10)
    ax.set_title("TPR vs FPR", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    # Plot 2: F1 Scores
    ax = axes[0, 1]
    f1_scores = [results[d]["f1"] for d in detector_names]
    colors = plt.cm.viridis(np.linspace(0, 1, len(detector_names)))
    bars = ax.bar(detector_labels, f1_scores, color=colors, alpha=0.7)
    ax.set_ylabel("F1 Score", fontsize=10)
    ax.set_title("F1 Score Comparison", fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.3, axis="y")
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Plot 3: Precision vs Recall
    ax = axes[1, 0]
    precisions = [results[d]["precision"] for d in detector_names]
    recalls = [results[d]["recall"] for d in detector_names]
    ax.scatter(recalls, precisions, s=200, alpha=0.6, c=colors)
    for i, label in enumerate(detector_labels):
        ax.annotate(label, (recalls[i], precisions[i]), fontsize=9)
    ax.set_xlabel("Recall", fontsize=10)
    ax.set_ylabel("Precision", fontsize=10)
    ax.set_title("Precision vs Recall", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    # Plot 4: Detection Time
    ax = axes[1, 1]
    times = [results[d]["detection_time_ms"] for d in detector_names]
    bars = ax.bar(detector_labels, times, color=colors, alpha=0.7)
    ax.set_ylabel("Detection Time (ms)", fontsize=10)
    ax.set_title("Average Detection Time", fontsize=11)
    ax.grid(True, alpha=0.3, axis="y")
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()

    # Save figure
    save_path = save_dir / "performance_comparison.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.savefig(save_path.with_suffix(".pdf"), bbox_inches="tight")
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Saved to {save_path}")

    plt.show()

    # Save results table
    table_path = save_dir / "results_table.md"
    with open(table_path, "w") as f:
        f.write("# Detection Performance Summary\n\n")
        f.write(
            "| Detector | TPR | FPR | Precision | Recall | F1 | Detection Time (ms) |\n"
        )
        f.write(
            "|----------|-----|-----|-----------|--------|----|--------------------||\n"
        )
        for detector_name in detector_names:
            m = results[detector_name]
            f.write(
                f"| {detector_name.capitalize()} | "
                f"{m['tpr']:.3f} | {m['fpr']:.3f} | {m['precision']:.3f} | "
                f"{m['recall']:.3f} | {m['f1']:.3f} | {m['detection_time_ms']:.2f} |\n"
            )

    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Results table saved to {table_path}")

    print(f"\n{Colors.OKGREEN}✅ Performance comparison complete!{Colors.ENDC}")
    print(f"\n{Colors.OKCYAN}Results saved to: {save_dir}{Colors.ENDC}")


def interactive_mode():
    """Run interactive CLI mode."""
    print_banner()

    # Swarm configuration
    print_section("SWARM CONFIGURATION")
    print(
        f"\n{Colors.OKCYAN}Number of UAVs (10-100) [default: 30]: {Colors.ENDC}", end=""
    )
    num_uavs = input().strip()
    num_uavs = int(num_uavs) if num_uavs else 30

    print(
        f"\n{Colors.OKCYAN}Communication range in meters (50-500) [default: 200]: {Colors.ENDC}",
        end="",
    )
    comm_range = input().strip()
    comm_range = float(comm_range) if comm_range else 200.0

    swarm_config = {
        "num_uavs": num_uavs,
        "comm_range": comm_range,
        "bounds": (500, 500, 100),
    }

    # Select attack
    attack_type, attack_config = select_attack()

    # Select detectors
    detector_names = select_detectors()

    # Select mode
    mode = select_mode()

    # Execute
    if mode == "live":
        run_live_visualization(attack_type, attack_config, detector_names, swarm_config)
    elif mode == "comparison":
        run_performance_comparison(
            attack_type, attack_config, detector_names, swarm_config
        )
    else:  # both
        run_live_visualization(attack_type, attack_config, detector_names, swarm_config)
        print(
            f"\n{Colors.WARNING}Live visualization complete. Starting performance comparison...{Colors.ENDC}"
        )
        run_performance_comparison(
            attack_type, attack_config, detector_names, swarm_config
        )

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ All operations complete!{Colors.ENDC}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Argus - UAV Swarm Security Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended for first-time users)
  argus

  # Quick phantom attack visualization
  argus --attack phantom --detectors spectral centrality --mode live

  # Full comparison of all methods
  argus --attack phantom --detectors all --mode comparison
        """,
    )

    parser.add_argument(
        "--attack",
        choices=["phantom", "position", "coordinated"],
        help="Attack type (if not specified, interactive mode will prompt)",
    )

    parser.add_argument(
        "--detectors",
        nargs="+",
        choices=["spectral", "centrality", "crypto", "ml", "all", "none"],
        help="Detection methods to test",
    )

    parser.add_argument(
        "--mode", choices=["live", "comparison", "both"], help="Execution mode"
    )

    parser.add_argument(
        "--num-uavs", type=int, default=30, help="Number of UAVs in swarm (default: 30)"
    )

    parser.add_argument(
        "--comm-range",
        type=float,
        default=200.0,
        help="Communication range in meters (default: 200)",
    )

    args = parser.parse_args()

    # If any required argument is missing, go to interactive mode
    if not args.attack or not args.detectors or not args.mode:
        interactive_mode()
    else:
        # Non-interactive mode
        print_banner()

        # Map attack type
        attack_map = {
            "phantom": AttackType.PHANTOM,
            "position": AttackType.POSITION_FALSIFICATION,
            "coordinated": AttackType.COORDINATED,
        }
        attack_type = attack_map[args.attack]

        # Default attack config
        attack_config = {
            "start_time": 10.0,
            "duration": 20.0,
            "phantom_count": 5,
            "falsification_magnitude": 50.0,
            "target_count": 5,
        }

        # Handle detector selection
        if "all" in args.detectors:
            detector_names = ["spectral", "centrality", "crypto", "ml"]
        elif "none" in args.detectors:
            detector_names = []
        else:
            detector_names = args.detectors

        swarm_config = {
            "num_uavs": args.num_uavs,
            "comm_range": args.comm_range,
            "bounds": (500, 500, 100),
        }

        # Execute
        if args.mode == "live":
            run_live_visualization(
                attack_type, attack_config, detector_names, swarm_config
            )
        elif args.mode == "comparison":
            run_performance_comparison(
                attack_type, attack_config, detector_names, swarm_config
            )
        else:  # both
            run_live_visualization(
                attack_type, attack_config, detector_names, swarm_config
            )
            run_performance_comparison(
                attack_type, attack_config, detector_names, swarm_config
            )


if __name__ == "__main__":
    main()
