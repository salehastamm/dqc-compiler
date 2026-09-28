from qiskit import qasm2, transpile

ALWAYS_DIAGONAL = {"z", "s", "sdg", "t", "tdg", "rz", "p", "cz"}

BASIS_GATES = ["cx", "cz", "h", "x", "y", "z", "s", "sdg", "t", "tdg",
               "rx", "ry", "rz", "sx", "sxdg"]

IGNORED = {"barrier", "measure"}


class Gate:
    """One instruction of the circuit, e.g. Gate("cx", [0, 1])."""

    def __init__(self, name, qubits, params=None):
        self.name = name              # e.g. "cx"
        self.qubits = list(qubits)    # e.g. [0, 1]  -> for cx: [control, target]
        if params is None:            # never use [] as a default value!
            params = []
        self.params = list(params)


    def is_diagonal_on(self, q):
        """True if this gate never changes the 0/1 value of wire q."""
        # 1) A gate that does not touch wire q cannot change it.
        if q not in self.qubits:
            return True
        # 2) Gates that only add a phase, on every wire they touch.
        if self.name in ALWAYS_DIAGONAL:
            return True
        # 3) cx keeps its control unchanged, but may flip its target.
        if self.name == "cx":
            return q == self.qubits[0]
        # 4) Everything else (h, x, rx, reset, unknown...) is assumed to change it.
        #    This is the SAFE choice: at worst we spend an extra EPR pair,
        #    but we never produce a wrong circuit.
        return False


    def __repr__(self):
        # How the gate looks when printed, e.g.  cx[0, 1]  or  rz[1](0.5)
        text = f"{self.name}{self.qubits}"
        if self.params:
            text += "(" + ", ".join(f"{p:.3g}" for p in self.params) + ")"
        return text



class Circuit:
    """A whole program: how many wires, and the list of gates in time order."""

    def __init__(self, num_qubits, gates):
        self.num_qubits = num_qubits
        self.gates = gates


def load_qasm(path):
    """Read an OpenQASM 2 file and return our own Circuit object."""
    # Step 1 : read the text file
    qc = qasm2.load(path, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)

    # Step 2 : rewrite big gates into small basis gates
    qc = transpile(qc, basis_gates=BASIS_GATES + ["measure", "reset"],
                   optimization_level=0)

    # Step 3 : copy each instruction into our own Gate
    gates = []
    for instruction in qc.data:
        name = instruction.operation.name
        if name in IGNORED:
            continue
        qubits = [qc.find_bit(q).index for q in instruction.qubits]
        params = [float(p) for p in instruction.operation.params]
        gates.append(Gate(name, qubits, params))

    # Step 4: package everything as a Circuit
    return Circuit(qc.num_qubits, gates)

if __name__ == "__main__":
    # Runs only when you type: python -m dqc.circuit benchmarks/tiny.qasm
    import sys
    circuit = load_qasm(sys.argv[1])
    print("qubits:", circuit.num_qubits)
    print("gates:", len(circuit.gates))
    for index, gate in enumerate(circuit.gates[:20]):
        print(f"{index:4d}  {gate}")
    if len(circuit.gates) > 20:
        print("   ... (only the first 20 gates are shown)")