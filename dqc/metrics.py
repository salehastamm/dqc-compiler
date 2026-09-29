"""
Phase 3 - Baseline metric: how many EPR pairs does a circuit need WITHOUT optimisation?

Without optimisation, every non-local gate uses its own EPR pair.
So:  baseline EPR pairs = number of non-local gates.
This is the "no opt" column of the paper's Table 1.
"""


def is_nonlocal(gate, assignment):
    """True if the gate touches two qubits that live on different QPUs."""
    if len(gate.qubits) != 2:
        return False
    a, b = gate.qubits
    return assignment[a] != assignment[b]

def count_nonlocal(circuit, assignment):
    """Number of non-local gates in the circuit."""
    count = 0
    for gate in circuit.gates:
        if is_nonlocal(gate, assignment):
            count += 1
    return count

if __name__ == "__main__":
    # Usage:  python -m dqc.metrics
    # Compares our baseline with the "no opt" column of Table 1 (2 QPUs).
    from dqc.circuit import load_qasm
    from dqc.assignment import assign_qubits
    from dqc.paper_data import TABLE1

    print(f"{'circuit':18s} {'qubits':>6s} {'paper':>7s} {'ours':>7s} {'diff':>7s}")
    for name in TABLE1:
        circuit = load_qasm(f"benchmarks/{name}.qasm")
        assignment = assign_qubits(circuit, 2)
        ours = count_nonlocal(circuit, assignment)
        paper = TABLE1[name][0]
        diff = (ours - paper) / paper * 100
        print(f"{name:18s} {circuit.num_qubits:6d} {paper:7d} {ours:7d} {diff:+6.0f}%")
