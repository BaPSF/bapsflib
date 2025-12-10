#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os

# =========================
# Configuration
# =========================

# Suffixes for all 9 combinations
SUFFIXES = ["BXPX", "BXPY", "BXPZ", "BYPX", "BYPY", "BYPZ", "BZPX", "BZPY", "BZPZ"]

# =========================
# Data loading
# =========================


def load_csv(filename):
    """
    Loads an E5100A-style CSV file, stripping quotes and skipping non-numeric header lines.
    Returns: freq, mag, phase (all numpy arrays)
    """
    data_lines = []
    if not os.path.exists(filename):
        print(f"WARNING: File {filename} not found. Skipping.")
        return None, None, None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip().strip('"')
            if line == "":
                continue
            if not line[0].isdigit() and not line[0] == "-":
                continue
            parts = line.split("\t") if "\t" in line else line.split(",")
            try:
                parts = [float(p) for p in parts]
                data_lines.append(parts)
            except ValueError:
                continue

    data = np.array(data_lines)
    freq = data[:, 0]
    mag = data[:, 1]
    phase = data[:, 2]

    return freq, mag, phase


# =========================
# Effective Area Calculation
# =========================


def calculate_effective_area_per_point(freq, mag):
    """
    Computes effective area point-by-point using physics formula:
    Ae(f) = (mag * 0.55) / (0.00180765 * freq)
    """
    Ae = (mag * 0.55) / (0.00180765 * freq)
    return Ae


def calculate_effective_area_linear_fit(freq, mag):
    """
    Linear fit of magnitude vs frequency for single-value Ae.
    """
    slope, intercept = np.polyfit(freq, mag, 1)
    Ae_single = slope * 307.1389  # calibration factor
    return Ae_single, slope, intercept


# =========================
# Plotting and Saving
# =========================


def save_plots_and_effective_area(freq, mag, phase, Ae, file_basename, output_dir):
    """
    Saves magnitude+effective area and phase plots as PNG,
    and saves effective area array to CSV.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Dual-axis plot: Magnitude & Effective Area
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(freq, mag, "b-", label="Magnitude")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Magnitude (linear)", color="b")
    ax1.tick_params(axis="y", labelcolor="b")
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(freq, Ae, "g-", label="Effective Area")
    ax2.set_ylabel("Effective Area", color="g")
    ax2.tick_params(axis="y", labelcolor="g")

    plt.title(f"{file_basename}: Magnitude & Effective Area vs Frequency")
    fig.tight_layout()
    mag_ae_file = os.path.join(output_dir, f"{file_basename}_mag_ae.png")
    plt.savefig(mag_ae_file)
    plt.close(fig)

    # Phase plot
    plt.figure(figsize=(10, 4))
    plt.plot(freq, phase, color="orange")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase (degrees)")
    plt.title(f"{file_basename}: Phase vs Frequency")
    plt.grid(True)
    phase_file = os.path.join(output_dir, f"{file_basename}_phase.png")
    plt.savefig(phase_file)
    plt.close()

    # Save effective area array to CSV
    ae_file = os.path.join(output_dir, f"{file_basename}_Ae.csv")
    np.savetxt(
        ae_file,
        np.column_stack((freq, Ae)),
        delimiter=",",
        header="Frequency,EffectiveArea",
        comments="",
    )


# =========================
# Main function
# =========================


def main():
    parser = argparse.ArgumentParser(
        description="Process E5100A CSV files by target prefix."
    )
    parser.add_argument("target", type=str, help="Target prefix (e.g., C19)")
    args = parser.parse_args()

    target = args.target.upper()  # Ensure uppercase
    output_dir = f"{target}_results"

    # Generate all 9 possible filenames
    filenames = [f"{target}{suffix}.csv" for suffix in SUFFIXES]

    for file in filenames:
        file_basename = os.path.splitext(os.path.basename(file))[0]
        print(f"Processing {file}...")
        freq, mag, phase = load_csv(file)
        if freq is None:
            continue

        # Compute effective area
        Ae = calculate_effective_area_per_point(freq, mag)
        Ae_single, slope, intercept = calculate_effective_area_linear_fit(freq, mag)

        # Print fitted single-value effective area
        print(f"{file_basename} Fitted Effective Area: {Ae_single:.6f}")

        # Save plots and Ae array
        save_plots_and_effective_area(freq, mag, phase, Ae, file_basename, output_dir)

    print(f"\nAll processed files saved in folder: {output_dir}")


if __name__ == "__main__":
    main()
