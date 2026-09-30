"""
Phase 7 - Run the paper's experiments and write every table and figure for the thesis.

Usage:
    python -m dqc.run              everything (takes a few minutes)
    python -m dqc.run table1       only Table 1
    python -m dqc.run table2       only Table 2 and Figures 5-8

All files are written to the results/ folder.
"""

import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")                 # draw into files, never open a window
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

from dqc.circuit import load_qasm
from dqc.assignment import assign_qubits
from dqc.grouping import group_gates, count_epr
from dqc.scheduling import schedule, depth
from dqc.paper_data import TABLE1, TABLE2


RESULTS = "results"

# The paper's three compiler settings: name -> (dmax, lookahead)
SETTINGS = {"no opt": (1, 0), "limit=3": (3, 10), "unlimited": (None, 10)}

# One fixed colour and marker per setting (checked for colour-blind safety).
COLORS = {"no opt": "#2a78d6", "limit=3": "#eb6834", "unlimited": "#1baf7a"}
MARKERS = {"no opt": "o", "limit=3": "s", "unlimited": "^"}

# Table 2 of the paper: circuit -> list of (number of QPUs, data qubits per QPU)
TABLE2_SETUPS = {
    "adder_n118":      [(2, 64), (4, 32), (8, 16), (16, 8)],
    "qft_n320":        [(2, 256), (3, 128), (4, 128), (5, 64), (8, 64), (10, 32), (16, 32)],
    "multiplier_n350": [(2, 256), (3, 128), (4, 128), (6, 64), (8, 64), (11, 32), (16, 32)],
    "qugan_n395":      [(2, 256), (4, 128), (7, 64), (8, 64), (13, 32), (16, 32)],
    "swap_test_n83":   [(2, 64), (4, 32), (8, 16), (16, 8)],
}

# Figures 6-8: depth for 4, 8 and 16 communication qubits per QPU, with 2, 4, 8, 16 QPUs.
DEPTH_FIGURES = {"qugan_n395": "fig6", "qft_n320": "fig7", "multiplier_n350": "fig8"}
FIGURE_QPUS = [2, 4, 8, 16]
COMM_QUBITS = [4, 8, 16]


# ---------------------------------------------------------------- file writing

def write_csv(filename, header, rows):
    with open(os.path.join(RESULTS, filename), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_latex(filename, header, rows, caption):
    """A LaTeX table. Paste it into the thesis with \\input{results/<filename>}."""
    lines = ["\\begin{table}[ht]",
             "\\centering",
             "\\begin{tabular}{l" + "r" * (len(header) - 1) + "}",
             "\\hline",
             " & ".join(header) + " \\\\",
             "\\hline"]
    for row in rows:
        cells = [str(value).replace("_", "\\_") for value in row]
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\hline",
              "\\end{tabular}",
              "\\caption{" + caption + "}",
              "\\end{table}"]
    with open(os.path.join(RESULTS, filename), "w") as f:
        f.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- experiments

def largest_qpu(assignment):
    """Number of qubits on the fullest QPU."""
    sizes = {}
    for qpu in assignment.values():
        sizes[qpu] = sizes.get(qpu, 0) + 1
    return max(sizes.values())


def make_table1():
    print("Table 1: EPR pairs, 2 QPUs")
    header = ["circuit", "qubits",
              "paper no opt", "paper limit=3", "paper unlimited",
              "ours no opt", "ours limit=3", "ours unlimited"]
    rows = []
    for name, paper in TABLE1.items():
        circuit = load_qasm(f"benchmarks/{name}.qasm")
        assignment = assign_qubits(circuit, 2)
        ours = []
        for dmax, lookahead in SETTINGS.values():
            ours.append(count_epr(group_gates(circuit, assignment, dmax, lookahead)))
        rows.append([name, circuit.num_qubits] + list(paper) + ours)
        print(f"  {name:18s} paper {paper}   ours {tuple(ours)}")
    write_csv("table1.csv", header, rows)

    # In the LaTeX table every cell shows "ours (paper)".
    latex_rows = []
    for row in rows:
        paper, ours = row[2:5], row[5:8]
        cells = [f"{o} ({p})" for o, p in zip(ours, paper)]
        latex_rows.append(row[:2] + cells)
    write_latex("table1.tex", ["Circuit", "$n_q$", "no opt", "limit=3", "unlimited"],
                latex_rows, "EPR pairs with 2 QPUs. Each cell: ours (paper).")


def make_table2():
    """Runs every Table 2 setup. Returns all results for the figures:
    {(circuit, QPUs, setting, communication qubits): (EPR pairs, depth)}"""
    print("Table 2: several QPU counts, 4 communication qubits (and 8, 16 for Figures 6-8)")
    experiments = {}
    header = ["circuit", "qubits", "QPUs", "data qubits per QPU", "input depth",
              "depth no opt", "depth limit=3", "depth unlimited",
              "EPR no opt", "EPR limit=3", "EPR unlimited",
              "paper input depth",
              "paper depth no opt", "paper depth limit=3", "paper depth unlimited",
              "paper EPR no opt", "paper EPR limit=3", "paper EPR unlimited"]
    rows = []
    latex_rows = []
    for name, setups in TABLE2_SETUPS.items():
        circuit = load_qasm(f"benchmarks/{name}.qasm")
        input_depth = depth(schedule(circuit.gates, {}))     # one machine, no EPR pairs

        for num_qpus, capacity in setups:
            assignment = assign_qubits(circuit, num_qpus)
            if largest_qpu(assignment) > capacity:
                raise ValueError(f"{name}: a QPU got more than {capacity} qubits")

            comm_list = [4]
            if name in DEPTH_FIGURES and num_qpus in FIGURE_QPUS:
                comm_list = COMM_QUBITS

            for setting, (dmax, lookahead) in SETTINGS.items():
                output = group_gates(circuit, assignment, dmax, lookahead)
                epr = count_epr(output)
                for comm in comm_list:
                    program = schedule(output, assignment, comm)
                    experiments[(name, num_qpus, setting, comm)] = (epr, depth(program))

            ours_depth = [experiments[(name, num_qpus, s, 4)][1] for s in SETTINGS]
            ours_epr = [experiments[(name, num_qpus, s, 4)][0] for s in SETTINGS]
            paper = TABLE2[(name, num_qpus)]
            rows.append([name, circuit.num_qubits, num_qpus, capacity, input_depth]
                        + ours_depth + ours_epr + list(paper))
            latex_rows.append([name, num_qpus, capacity, f"{input_depth} ({paper[0]})"]
                              + [f"{o} ({p})" for o, p in zip(ours_depth, paper[1:4])]
                              + [f"{o} ({p})" for o, p in zip(ours_epr, paper[4:7])])
            print(f"  {name:16s} {num_qpus:2d} QPUs   depth {ours_depth}   EPR {ours_epr}")

    write_csv("table2.csv", header, rows)
    write_latex("table2.tex",
                ["Circuit", "QPUs", "$n_d$", "input depth",
                 "depth no opt", "depth limit=3", "depth unl.",
                 "EPR no opt", "EPR limit=3", "EPR unl."],
                latex_rows,
                "Several QPU counts, 4 communication qubits per QPU. Each cell: ours (paper). "
                "Our depths count basis gates after decomposition; the paper's input depth "
                "is that of the original file.")

    # Every result behind Figures 5-8, as a plain table.
    raw = []
    for (name, num_qpus, setting, comm), (epr, d) in experiments.items():
        raw.append([name, num_qpus, setting, comm, epr, d])
    write_csv("figure_data.csv",
              ["circuit", "QPUs", "setting", "communication qubits", "EPR pairs", "depth"], raw)
    return experiments

# ---------------------------------------------------------------- figures

def style(ax):
    """Quiet axes: no top/right frame, light horizontal grid behind the data."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))


def save(fig, filename):
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, filename), dpi=200)
    plt.close(fig)


def make_figure5(experiments):
    """EPR pairs versus number of QPUs (paper, Figure 5)."""
    circuits = ["adder_n118", "qft_n320", "qugan_n395", "multiplier_n350"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, name in zip(axes.flat, circuits):
        for setting in SETTINGS:
            eprs = [experiments[(name, q, setting, 4)][0] for q in FIGURE_QPUS]
            ax.plot(FIGURE_QPUS, eprs, color=COLORS[setting], marker=MARKERS[setting],
                    linewidth=2, markersize=6, label=setting)
        ax.set_xscale("log", base=2)
        ax.set_xticks(FIGURE_QPUS, [str(q) for q in FIGURE_QPUS])
        ax.set_title(f"{name}: EPR pairs vs QPUs")
        ax.set_xlabel("number of QPUs")
        ax.set_ylabel("EPR pairs")
        style(ax)
    axes.flat[0].legend(title="setting", frameon=False)
    save(fig, "fig5_epr_vs_qpus.png")


def make_depth_figure(experiments, name, filename):
    """Depth versus communication qubits, one panel per QPU count (paper, Figures 6-8)."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    width = 0.26
    for panel, (ax, num_qpus) in enumerate(zip(axes.flat, FIGURE_QPUS)):
        for i, setting in enumerate(SETTINGS):
            depths = [experiments[(name, num_qpus, setting, c)][1] for c in COMM_QUBITS]
            positions = [x + (i - 1) * width for x in range(len(COMM_QUBITS))]
            ax.bar(positions, depths, width=width * 0.9, color=COLORS[setting], label=setting)
        ax.set_xticks(range(len(COMM_QUBITS)), [str(c) for c in COMM_QUBITS])
        ax.set_title(f"{name}: {num_qpus} QPUs")
        ax.set_xlabel("communication qubits per QPU")
        if panel % 2 == 0:                      # left column only: the y axis is shared
            ax.set_ylabel("depth")
        style(ax)
    axes.flat[0].legend(title="setting", frameon=False)
    save(fig, filename)

if __name__ == "__main__":
    os.makedirs(RESULTS, exist_ok=True)
    parts = sys.argv[1:] or ["table1", "table2"]

    if "table1" in parts:
        make_table1()

    if "table2" in parts:
        experiments = make_table2()
        make_figure5(experiments)
        for name, prefix in DEPTH_FIGURES.items():
            make_depth_figure(experiments, name, f"{prefix}_{name}_depth.png")

    print("Done. Files are in results/")
