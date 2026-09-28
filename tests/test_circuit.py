from dqc.circuit import Gate, load_qasm


def test_is_diagonal_on():
    assert Gate("cx", [0, 1]).is_diagonal_on(0) is True     # control
    assert Gate("cx", [0, 1]).is_diagonal_on(1) is False    # target
    assert Gate("cz", [4, 7]).is_diagonal_on(4) is True     # both ends
    assert Gate("cz", [4, 7]).is_diagonal_on(7) is True
    assert Gate("h", [3]).is_diagonal_on(3) is False
    assert Gate("rz", [1], [0.5]).is_diagonal_on(1) is True
    assert Gate("h", [3]).is_diagonal_on(0) is True         # untouched wire


def test_load_tiny():
    c = load_qasm("benchmarks/tiny.qasm")
    assert c.num_qubits == 4
    assert len(c.gates) == 6
    assert c.gates[3].name == "cz"
    assert c.gates[3].qubits == [1, 2]
    assert c.gates[2].params == [0.5]
