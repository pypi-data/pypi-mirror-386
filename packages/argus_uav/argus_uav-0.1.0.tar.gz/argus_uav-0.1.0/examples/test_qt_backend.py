#!/usr/bin/env python3
"""
Test PyQt5 backend configuration.

Verifies that matplotlib is using Qt5Agg for interactive plots.
"""

import matplotlib

matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
import numpy as np


def main():
    """Test PyQt5 backend."""
    print("\n" + "=" * 70)
    print("🔧 MATPLOTLIB BACKEND TEST")
    print("=" * 70)

    # Check backend
    current_backend = matplotlib.get_backend()
    print(f"\nCurrent matplotlib backend: {current_backend}")

    if current_backend == "Qt5Agg":
        print("✅ PyQt5 backend configured correctly!")
    else:
        print(f"⚠️  Backend is {current_backend}, not Qt5Agg")
        print("   Try: import matplotlib; matplotlib.use('Qt5Agg')")

    # Test interactive plot
    print("\n📊 Creating test plot...")
    print("   (Close the window to continue)")

    fig, ax = plt.subplots(figsize=(8, 6))

    # Simple sine wave
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    ax.plot(x, y, linewidth=2, color="steelblue", label="sin(x)")
    ax.set_xlabel("X", fontsize=12)
    ax.set_ylabel("Y", fontsize=12)
    ax.set_title("PyQt5 Backend Test - Interactive Plot", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    try:
        plt.show()  # This will open a Qt5 window
        print("\n✅ Interactive plot displayed successfully!")
    except Exception as e:
        print(f"\n❌ Error displaying plot: {e}")
        print("   Make sure PyQt5 is installed: uv pip install PyQt5")

    print("\n" + "=" * 70)
    print("✅ Backend test complete!")
    print("=" * 70)

    print("\n📝 Backend Info:")
    print(f"   • matplotlib version: {matplotlib.__version__}")
    print(f"   • Backend: {matplotlib.get_backend()}")
    print(f"   • Interactive: {matplotlib.is_interactive()}")

    # Check PyQt5 availability
    try:
        from PyQt5 import QtCore

        print(f"   • PyQt5 version: {QtCore.QT_VERSION_STR}")
        print("   ✅ PyQt5 is properly installed")
    except ImportError as e:
        print(f"   ❌ PyQt5 not found: {e}")
        print("   Install with: uv pip install PyQt5")

    print()


if __name__ == "__main__":
    main()
