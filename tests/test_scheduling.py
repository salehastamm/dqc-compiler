import random

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, random_statevector

from dqc.circuit import Gate, Circuit
from dqc.grouping import group_gates
from dqc.scheduling import schedule, depth
from tests.test_grouping import FIG3, FIG3_ASSIGNMENT, random_circuit


def test_fig3_program():
    program = schedule(group_gates(FIG3, FIG3_ASSIGNMENT), FIG3_ASSIGNMENT)
    names = [gate.name for start, gate in program]
    assert names.count("cat_ent") == 1
    assert names.count("cat_disent") == 1
    assert names[0] == "cat_ent" and names[-1] == "cat_disent"
    assert depth(program) == 6


def test_depth_without_groups():
    # Everything on one QPU: no EPR pairs, plain as-early-as-possible depth.
    c = Circuit(4, [Gate("h", [0]), Gate("cx", [0, 1]), Gate("rz", [1], [0.5]),
                    Gate("cz", [1, 2]), Gate("cx", [2, 3]), Gate("h", [3])])
    program = schedule(group_gates(c, {0: 0, 1: 0, 2: 0, 3: 0}), {0: 0, 1: 0, 2: 0, 3: 0})
    assert depth(program) == 6


def simulate(program, n):
    """Run the distributed program on a simulator.

    Communication qubits become extra qubits n, n+1, ...
    cat_ent / cat_disent are replaced by their measurement-free equivalent:
    a CX from the held qubit to its mirror copy (copies the 0/1 value, then
    uncopies it). The uncopy only works if the group never changed that value.
    """
    comm = sorted({q for start, g in program for q in g.qubits if isinstance(q, str)})
    index = {}
    for i, label in enumerate(comm):
        index[label] = n + i
    qc = QuantumCircuit(n + len(comm))
    for start, g in program:
        qubits = [index.get(q, q) for q in g.qubits]
        if g.name == "cat_ent":
            qc.cx(qubits[0], qubits[2])
        elif g.name == "cat_disent":
            qc.cx(qubits[0], qubits[1])
        else:
            getattr(qc, g.name)(*g.params, *qubits)
    return qc, len(comm)


def test_distributed_program_is_physically_correct():
    rng = random.Random(3)
    for trial in range(60):
        n = rng.randint(2, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        assignment = {q: rng.randrange(3) for q in range(n)}

        for dmax, lookahead in ((None, 10), (3, 10), (1, 0)):
            for comm_per_qpu in (1, 2):
                output = group_gates(c, assignment, dmax, lookahead)
                qc, extra = simulate(schedule(output, assignment, comm_per_qpu), n)

                # Expected: the original circuit, communication qubits stay |0>.
                reference = QuantumCircuit(n + extra)
                for g in c.gates:
                    getattr(reference, g.name)(*g.params, *g.qubits)

                state = random_statevector(2 ** n, seed=trial)
                if extra:
                    state = Statevector.from_label("0" * extra).tensor(state)
                assert state.evolve(qc).equiv(state.evolve(reference))
