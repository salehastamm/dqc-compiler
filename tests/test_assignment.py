from dqc.circuit import load_qasm
from dqc.assignment import interaction_graph, assign_qubits


def test_graph_weights():
    g = interaction_graph(load_qasm("benchmarks/tiny.qasm"))
    assert g.number_of_nodes() == 4
    assert g[0][1]["weight"] == 1      # cx[0, 1]
    assert g[1][2]["weight"] == 1      # cz[1, 2]
    assert g[2][3]["weight"] == 1      # cx[2, 3]
    assert not g.has_edge(0, 3)        # no gate between 0 and 3


def test_tiny_split():
    a = assign_qubits(load_qasm("benchmarks/tiny.qasm"), 2)
    assert a[0] == a[1]                # 0 and 1 together
    assert a[2] == a[3]                # 2 and 3 together
    assert a[0] != a[2]                # the two pairs on different QPUs


def test_every_qubit_assigned_and_balanced():
    c = load_qasm("benchmarks/qft_n29.qasm")
    for num_qpus in (2, 3, 4):
        a = assign_qubits(c, num_qpus)
        assert sorted(a) == list(range(29))                     # every qubit has a QPU
        sizes = [list(a.values()).count(p) for p in range(num_qpus)]
        assert max(sizes) - min(sizes) <= 1                     # balanced
