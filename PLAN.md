# Implementation Plan — DQC Compiler

Deadline: ~2026-10-10.  Paper: Bandini et al., arXiv 2602.24062.

Rule: every phase ends in something runnable that prints output.
No phase is "write code and hope".

## Phase 1 — Circuit IR      `dqc/circuit.py`          Sep 23-24
Gate(name, qubits, params) + Gate.is_diagonal_on(q)
Circuit(num_qubits, gates) + Circuit.from_qasm(path)
DONE WHEN: prints the gate table for benchmarks/tiny.qasm

## Phase 2 — Qubit Assignment `dqc/assignment.py`      Sep 25-26
Build weighted graph: nodes = qubits, edge weight = #2-qubit gates between them.
Partition into N parts (networkx kernighan_lin_bisection; recurse for N=4).
DONE WHEN: prints {qubit: qpu} for tiny.qasm and a real benchmark

## Phase 3 — Baseline metric  `dqc/metrics.py`         Sep 26
is_nonlocal(gate, assignment); count them.
DONE WHEN: reproduces the "no opt" column of Table 1 for >=2 circuits

## Phase 4 — Grouping         `dqc/grouping.py`        Sep 27-30  <-- THE HEART
Algorithm 1 of the paper. Group = (held control qubit, target QPU, [gates]).
Greedy scan with a working-memory dict M[qubit] -> Group. Cap group size at Dmax.
DONE WHEN: EPR count drops; ballpark of the "unlimited opt" column

## Phase 5 — Reordering       `dqc/commutation.py`     Oct 1-2
can_commute(g1, g2) per Figure 4. Hook into Phase 4 (Algorithm 1 lines 26-29).
DONE WHEN: EPR count drops further vs Phase 4 alone

## Phase 6 — Results runner   `dqc/run.py`             Oct 3-4
Loop benchmarks x {no opt, Dmax=3, unlimited}. Emit CSV + LaTeX table.
DONE WHEN: a table exists that can be pasted into the thesis

## Phase 7 — Verification     `tests/`                 Oct 5
pytest: is_diagonal_on checked against Qiskit matrices;
reordering checked to preserve the circuit's unitary on small circuits.

## Writing                    `thesis/`                Oct 5-10
docs/*.md (Persian) are the chapter drafts. Reshape into the LaTeX template.

---

## Total library surface of this project

qiskit:   qasm2.load(path) | circ.num_qubits | circ.data
          circ.find_bit(q).index | inst.operation.name | inst.operation.params
          Operator(qc).data          (tests only)
networkx: nx.Graph() | G.add_edge(a,b,weight=w) | kernighan_lin_bisection(G)

Everything else is list / dict / set / for / if.

## Known gaps in the paper (thesis material - keep adding to this list)

1. CZ is symmetric, so "which qubit is the control" is a free choice the paper
   never specifies. The choice changes the EPR count.
2. Algorithm 1 line 23 says "where g can be added" but never defines the
   condition. We derived it from the Figure 1 caption: a gate may join a group
   iff it is diagonal on the group's held control qubit.
3. Algorithm 1 line 26 checks GA[j+1] but never says what happens if commuting
   still does not help after several steps (termination is not argued).
