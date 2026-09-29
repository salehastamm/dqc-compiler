"""
Phase 6 - Non-local gate scheduling (paper, section 3.4).

Turns the output of the grouping pass into a distributed program:
every group becomes   cat_ent  ->  its gates  ->  cat_disent.
Inside a group, each non-local gate is rewritten to act on the communication
qubit that holds the mirror copy of the held qubit, so it runs locally.

It also gives every instruction a time step, so we can measure the depth
(the number of time steps the program needs).

Communication qubits are named like "Q1.c0" = QPU 1, communication qubit 0.
"""

from dqc.circuit import Gate
from dqc.metrics import is_nonlocal
from dqc.grouping import Group


class Scheduler:
    """Places instructions in time, as early as possible (ASAP)."""

    def __init__(self, assignment, comm_per_qpu):
        self.assignment = assignment
        self.comm_per_qpu = comm_per_qpu
        self.ready = {}       # qubit or communication qubit -> first free time step
        self.program = []     # list of (time step, instruction), in execution order

    def run(self, gate):
        """Schedule one instruction at the first time step all its qubits are free."""
        start = 0
        for q in gate.qubits:
            start = max(start, self.ready.get(q, 0))
        for q in gate.qubits:
            self.ready[q] = start + 1         # busy during this step
        self.program.append((start, gate))

    def free_comm_qubit(self, qpu):
        """The communication qubit of this QPU that becomes free the earliest."""
        best = None
        for slot in range(self.comm_per_qpu):
            label = f"Q{qpu}.c{slot}"
            if best is None or self.ready.get(label, 0) < self.ready.get(best, 0):
                best = label
        return best

    def run_group(self, group):
        """One TeleGate: cat_ent, the group's gates, cat_disent."""
        root = group.root()
        near = self.free_comm_qubit(self.assignment[root])   # EPR half next to the held qubit
        far = self.free_comm_qubit(group.roots[root])        # EPR half that holds the mirror copy

        # Cat-Ent: uses the held qubit and both halves of one EPR pair.
        self.run(Gate("cat_ent", [root, near, far]))

        for gate in group.gates:
            if is_nonlocal(gate, self.assignment):
                # Replace the held qubit by its mirror copy: the gate becomes local.
                qubits = [far if q == root else q for q in gate.qubits]
                self.run(Gate(gate.name, qubits, gate.params))
            else:
                self.run(gate)

        # Cat-DisEnt: measure the mirror copy and correct the held qubit.
        self.run(Gate("cat_disent", [root, far]))

def schedule(output, assignment, comm_per_qpu=4):
    """Build the distributed program from the grouping output."""
    scheduler = Scheduler(assignment, comm_per_qpu)
    for item in output:
        if isinstance(item, Group):
            scheduler.run_group(item)
        else:
            scheduler.run(item)
    return scheduler.program


def depth(program):
    """Number of time steps the program needs."""
    if not program:
        return 0
    return max(start for start, gate in program) + 1


if __name__ == "__main__":
    # Usage:  python -m dqc.scheduling benchmarks/fig3.qasm 2
    import sys
    from dqc.circuit import load_qasm
    from dqc.assignment import assign_qubits
    from dqc.grouping import group_gates, count_epr

    circuit = load_qasm(sys.argv[1])
    assignment = assign_qubits(circuit, int(sys.argv[2]))
    output = group_gates(circuit, assignment, dmax=None, lookahead=10)
    program = schedule(output, assignment, comm_per_qpu=4)

    print("EPR pairs:", count_epr(output))
    print("depth    :", depth(program))
    for start, gate in program[:40]:
        print(f"  step {start:4d}   {gate}")
    if len(program) > 40:
        print("  ... (only the first 40 instructions are shown)")
