"""
Phase 2 - Qubit assignment: decide which QPU (machine) each qubit lives on.

Goal (paper, section 3.1): split the qubits evenly over the QPUs so that
as few two-qubit gates as possible connect qubits on different QPUs.
"""

import networkx as nx
from networkx.algorithms.community import kernighan_lin_bisection


def interaction_graph(circuit):
    """One node per qubit. Edge weight = number of 2-qubit gates between the two qubits."""
    graph = nx.Graph()
    graph.add_nodes_from(range(circuit.num_qubits))   # every qubit is a node, even unused ones

    for gate in circuit.gates:
        if len(gate.qubits) != 2:
            continue                                  # 1-qubit gates never need an EPR pair
        a, b = gate.qubits
        if graph.has_edge(a, b):
            graph[a][b]["weight"] += 1                # one more gate between a and b
        else:
            graph.add_edge(a, b, weight=1)            # first gate between a and b

    return graph


def split(graph, qubits, num_parts):
    """Split `qubits` into `num_parts` equal-sized sets, cutting as little weight as possible."""
    # Base case: one part means nothing to split.
    if num_parts == 1:
        return [set(qubits)]

    # Divide the parts into two halves, e.g. 4 -> 2 + 2, 3 -> 1 + 2.
    left_parts = num_parts // 2
    right_parts = num_parts - left_parts
    left_size = round(len(qubits) * left_parts / num_parts)

    # Starting guess: the lowest-numbered qubits on the left, the rest on the right.
    ordered = sorted(qubits)
    start = (set(ordered[:left_size]), set(ordered[left_size:]))

    # Kernighan-Lin improves the guess by swapping qubits between the two sides.
    left, right = kernighan_lin_bisection(graph.subgraph(qubits),
                                          partition=start, weight="weight")

    # networkx may return the two sides in either order. If they came back swapped, swap them back.
    if len(left) != left_size:
        left, right = right, left

    # Split each half again until every part is one QPU.
    return split(graph, left, left_parts) + split(graph, right, right_parts)


def assign_qubits(circuit, num_qpus):
    """Return a dict {qubit: qpu number}, with the qubits spread evenly over num_qpus QPUs."""
    graph = interaction_graph(circuit)
    parts = split(graph, list(range(circuit.num_qubits)), num_qpus)

    assignment = {}
    for qpu, part in enumerate(parts):
        for q in part:
            assignment[q] = qpu
    return assignment


if __name__ == "__main__":
    # Usage:  python -m dqc.assignment benchmarks/tiny.qasm 2
    import sys
    from dqc.circuit import load_qasm

    circuit = load_qasm(sys.argv[1])
    num_qpus = int(sys.argv[2])
    assignment = assign_qubits(circuit, num_qpus)

    for qpu in range(num_qpus):
        members = sorted(q for q in assignment if assignment[q] == qpu)
        print(f"QPU {qpu}: {len(members)} qubits -> {members}")
