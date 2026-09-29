"""
Phase 4 - Non-local gate grouping (Algorithm 1 of the paper).

A Group is a set of gates that share ONE EPR pair (one TeleGate).
While the group is open, one qubit (the "held" qubit, or root) has its 0/1 value
mirrored on a communication qubit in a far QPU. Gates can join the group as long
as they do not change the held qubit's 0/1 value.
"""

from dqc.metrics import is_nonlocal



class Group:
    """Gates that share one EPR pair."""

    def __init__(self, gate, assignment):
        # A group always starts with a non-local 2-qubit gate.
        a, b = gate.qubits
        self.gates = [gate]
        self.members = {a, b}          # qubits that belong to this group

        # Which qubit is held? We do not decide yet. We keep every possible choice:
        #   roots = {candidate held qubit: QPU where its mirror copy will live}
        # A qubit can be held only if the gate does not change its 0/1 value.
        self.roots = {}
        if gate.is_diagonal_on(a):
            self.roots[a] = assignment[b]
        if gate.is_diagonal_on(b):
            self.roots[b] = assignment[a]

    def surviving_roots(self, gate, assignment):
        """Candidate held qubits that stay valid if `gate` joins. Empty dict = gate cannot join."""
        survivors = {}
        for root, far_qpu in self.roots.items():
            # Rule 1: the gate must not change the held qubit's 0/1 value.
            if not gate.is_diagonal_on(root):
                continue
            # Rule 2: a non-local gate can only use this EPR pair if it acts on the
            #         held qubit and its other qubit is on the far QPU.
            if is_nonlocal(gate, assignment):
                if root not in gate.qubits:
                    continue
                a, b = gate.qubits
                other = b if a == root else a
                if assignment[other] != far_qpu:
                    continue
            survivors[root] = far_qpu
        return survivors

    def add(self, gate, survivors):
        self.gates.append(gate)
        self.members.update(gate.qubits)
        self.roots = survivors

    def root(self):
        """The held qubit finally used (any survivor is valid; take the smallest)."""
        return min(self.roots) if self.roots else None

    def __repr__(self):
        return f"Group(root={self.root()}, gates={self.gates})"


class Grouper:
    """Runs Algorithm 1. Keeps the working memory and the output."""

    def __init__(self, assignment, dmax=None):
        self.assignment = assignment
        self.dmax = dmax            # max gates per group; None = unlimited
        self.output = []            # the paper's OC: local gates and closed groups, in order
        self.memory = {}            # the paper's M: qubit -> open group it belongs to
        self.open_groups = []

    def groups_touched(self, gate):
        """The open groups that the gate's qubits belong to (0, 1 or 2 groups)."""
        touched = []
        for q in gate.qubits:
            group = self.memory.get(q)
            if group is not None and group not in touched:
                touched.append(group)
        return touched

    def try_place(self, gate):
        """Put the gate in the output or in a group. Return False if it is blocked."""
        touched = self.groups_touched(gate)

        # Case 1: none of its qubits is in an open group (Algorithm 1, lines 14-22).
        if not touched:
            if is_nonlocal(gate, self.assignment):
                group = Group(gate, self.assignment)       # start a new group
                self.open_groups.append(group)
                self.remember(group)
                self.close_if_full(group)
            else:
                self.output.append(gate)                   # local gate: output directly
            return True

        # Case 2: it touches exactly one open group and can join it (lines 23-25).
        if len(touched) == 1:
            group = touched[0]
            survivors = group.surviving_roots(gate, self.assignment)
            if survivors:
                group.add(gate, survivors)
                self.remember(group)
                self.close_if_full(group)
                return True

        # Case 3: blocked (it breaks the group, or touches two groups).
        return False

    def remember(self, group):
        for q in group.members:
            self.memory[q] = group

    def close_if_full(self, group):
        """Dmax: close the group when it reaches the maximum size (lines 35-38)."""
        if self.dmax is not None and len(group.gates) >= self.dmax:
            self.close(group)

    def close(self, group):
        """Finish the group: it goes to the output and its qubits are released."""
        self.output.append(group)
        self.open_groups.remove(group)
        for q in group.members:
            del self.memory[q]

    def close_first_group_of(self, gate):
        """Close the first open group the gate touches (lines 30-32)."""
        self.close(self.groups_touched(gate)[0])

    def close_all(self):
        for group in list(self.open_groups):
            self.close(group)

def group_gates(circuit, assignment, dmax=None):
    """Algorithm 1: return the output list (local gates and groups)."""
    grouper = Grouper(assignment, dmax)
    for gate in circuit.gates:
        while not grouper.try_place(gate):
            grouper.close_first_group_of(gate)
    grouper.close_all()
    return grouper.output

def count_epr(output):
    """One EPR pair per group."""
    count = 0
    for item in output:
        if isinstance(item, Group):
            count += 1
    return count


def flatten(output):
    """The output as a plain list of gates (groups unpacked), for checking."""
    gates = []
    for item in output:
        if isinstance(item, Group):
            gates.extend(item.gates)
        else:
            gates.append(item)
    return gates


if __name__ == "__main__":
    # Usage:  python -m dqc.grouping
    from dqc.circuit import load_qasm
    from dqc.assignment import assign_qubits
    from dqc.paper_data import TABLE1

    print(f"{'circuit':18s} {'no opt':>15s} {'limit=3':>15s} {'unlimited':>15s}")
    print(f"{'':18s} {'paper / ours':>15s} {'paper / ours':>15s} {'paper / ours':>15s}")
    for name in TABLE1:
        circuit = load_qasm(f"benchmarks/{name}.qasm")
        assignment = assign_qubits(circuit, 2)
        ours = [count_epr(group_gates(circuit, assignment, dmax)) for dmax in (1, 3, None)]
        paper = TABLE1[name]
        cells = [f"{p:>6d} / {o:<6d}" for p, o in zip(paper, ours)]
        print(f"{name:18s} " + " ".join(cells))
