import random

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from dqc.circuit import Gate, Circuit, load_qasm
from dqc.assignment import assign_qubits
from dqc.metrics import count_nonlocal
from dqc.grouping import group_gates, count_epr, flatten


# The paper's Figure 3 idea: three CZ between qubit 0 (QPU 0) and qubit 1 (QPU 1),
# with an H on qubit 0 and an Rz on qubit 1 in between.
FIG3 = Circuit(2, [Gate("cz", [0, 1]), Gate("h", [0]), Gate("cz", [0, 1]),
                   Gate("rz", [1], [0.3]), Gate("cz", [0, 1])])
FIG3_ASSIGNMENT = {0: 0, 1: 1}


def test_fig3_unlimited_uses_one_epr_pair():
    assert count_epr(group_gates(FIG3, FIG3_ASSIGNMENT)) == 1


def test_fig3_dmax3_uses_two_epr_pairs():
    assert count_epr(group_gates(FIG3, FIG3_ASSIGNMENT, dmax=3)) == 2


def test_fig3_no_opt_uses_three_epr_pairs():
    assert count_epr(group_gates(FIG3, FIG3_ASSIGNMENT, dmax=1)) == 3


def test_dmax1_equals_baseline():
    for name in ("adder_n28", "qft_n29", "swap_test_n25"):
        c = load_qasm(f"benchmarks/{name}.qasm")
        a = assign_qubits(c, 2)
        assert count_epr(group_gates(c, a, dmax=1)) == count_nonlocal(c, a)


def to_qiskit(gates, n):
    """Build a Qiskit circuit from our gates, so Qiskit can compute its matrix."""
    qc = QuantumCircuit(n)
    for g in gates:
        getattr(qc, g.name)(*g.params, *g.qubits)
    return qc


def random_circuit(rng, n, length):
    gates = []
    for _ in range(length):
        kind = rng.random()
        if kind < 0.5:
            a, b = rng.sample(range(n), 2)
            gates.append(Gate(rng.choice(["cx", "cz"]), [a, b]))
        elif kind < 0.75:
            gates.append(Gate(rng.choice(["h", "x", "z", "s", "t", "sx"]), [rng.randrange(n)]))
        else:
            gates.append(Gate(rng.choice(["rx", "ry", "rz"]), [rng.randrange(n)],
                              [rng.uniform(0, 6.28)]))
    return Circuit(n, gates)


def test_grouping_keeps_the_circuit_equivalent():
    rng = random.Random(1)
    for _ in range(200):
        n = rng.randint(2, 6)
        c = random_circuit(rng, n, rng.randint(1, 40))
        assignment = {q: rng.randrange(3) for q in range(n)}
        original = Operator(to_qiskit(c.gates, n))
        for dmax in (None, 1, 3):
            grouped = flatten(group_gates(c, assignment, dmax))
            assert Operator(to_qiskit(grouped, n)).equiv(original)
