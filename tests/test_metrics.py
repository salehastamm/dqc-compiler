from dqc.circuit import Gate, load_qasm
from dqc.assignment import assign_qubits
from dqc.metrics import is_nonlocal, count_nonlocal


def test_is_nonlocal():
    assignment = {0: 0, 1: 0, 2: 1, 3: 1}           # qubits 0,1 on QPU 0; 2,3 on QPU 1
    assert is_nonlocal(Gate("cz", [1, 2]), assignment) is True
    assert is_nonlocal(Gate("cx", [0, 1]), assignment) is False
    assert is_nonlocal(Gate("h", [2]), assignment) is False


def test_tiny_needs_one_epr_pair():
    c = load_qasm("benchmarks/tiny.qasm")
    assert count_nonlocal(c, assign_qubits(c, 2)) == 1


def test_chain_circuits_need_one_epr_pair():
    # GHZ and Cat are chains 0-1-2-...-n, so one cut in the middle is enough.
    for name in ("ghz_n40", "cat_n35"):
        c = load_qasm(f"benchmarks/{name}.qasm")
        assert count_nonlocal(c, assign_qubits(c, 2)) == 1
