import itertools

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from dqc.circuit import Gate
from dqc.commutation import can_commute


def test_figure4_rules():
    assert can_commute(Gate("rx", [1], [0.5]), Gate("cx", [0, 1]))   # (a) Rx on CX target
    assert can_commute(Gate("rz", [0], [0.5]), Gate("cx", [0, 1]))   # (b) Rz on CX control
    assert can_commute(Gate("rz", [1], [0.5]), Gate("cz", [0, 1]))   # (c) Rz and CZ
    assert can_commute(Gate("cx", [0, 1]), Gate("cx", [0, 2]))       # (d) CX sharing control
    assert can_commute(Gate("cx", [0, 2]), Gate("cx", [1, 2]))       # (e) CX sharing target
    assert can_commute(Gate("cz", [0, 1]), Gate("cz", [1, 2]))       # (f) CZ and CZ


def test_non_commuting_pairs():
    assert not can_commute(Gate("h", [0]), Gate("cz", [0, 1]))
    assert not can_commute(Gate("cx", [0, 1]), Gate("cx", [1, 0]))
    assert not can_commute(Gate("rx", [0], [0.5]), Gate("cx", [0, 1]))   # Rx on control
    assert not can_commute(Gate("rz", [1], [0.5]), Gate("cx", [0, 1]))   # Rz on target


def all_gates_on_3_qubits():
    gates = []
    for q in range(3):
        for name in ["h", "x", "y", "z", "s", "sdg", "t", "tdg", "sx", "sxdg"]:
            gates.append(Gate(name, [q]))
        for name in ["rx", "ry", "rz"]:
            gates.append(Gate(name, [q], [0.7]))
    for a, b in itertools.permutations(range(3), 2):
        gates.append(Gate("cx", [a, b]))
        gates.append(Gate("cz", [a, b]))
    return gates


def matrix(gate):
    qc = QuantumCircuit(3)
    getattr(qc, gate.name)(*gate.params, *gate.qubits)
    return Operator(qc)


def test_rule_is_never_wrong():
    # For every pair of gates: if the rule says "commute", the matrices must agree.
    gates = all_gates_on_3_qubits()
    for g1, g2 in itertools.product(gates, repeat=2):
        if can_commute(g1, g2):
            a, b = matrix(g1), matrix(g2)
            assert (a @ b).equiv(b @ a), f"{g1} and {g2} do not commute"
