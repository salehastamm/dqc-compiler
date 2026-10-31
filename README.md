# Distributed Quantum Circuit Compiler

A from-scratch Python reproduction of the compiler in *"Optimized Compilation for Distributed
Quantum Computing"* (Bandini, Ferrari, Carretta, Amoretti — arXiv:2602.24062). Bachelor's thesis
project, Islamic Azad University, Mashhad.

In distributed quantum computing, several small quantum processors (QPUs) are linked by a network.
A gate between qubits on different QPUs consumes an **EPR pair** — a slow, noisy network resource.
This compiler minimises EPR pairs in four passes:

1. **Qubit assignment** — balanced recursive Kernighan–Lin partitioning of the qubit interaction graph.
2. **Non-local gate grouping** — Algorithm 1 of the paper: consecutive non-local gates that keep a
   shared qubit's 0/1 value unchanged reuse one EPR pair.
3. **Reordering** — gates that provably commute are moved forward so groups grow longer.
4. **Scheduling** — each group becomes Cat-Ent → local gates → Cat-DisEnt on communication qubits,
   scheduled as soon as possible; reports circuit depth.

## Results (2 QPUs, EPR pairs)

| Circuit | No optimisation | Grouping + reordering |
|---|---|---|
| qugan_n395 | 404 | 5 |
| qft_n29 | 420 | 15 |
| multiplier_n350 | 11,470 | 6,747 |
| qv_n100 | 6,522 | 6,522 (random circuit, no structure to exploit) |

Full comparison with the paper for 27 QASMBench circuits: [`results/`](results/).

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                                  # 20 tests
python -m dqc.scheduling benchmarks/fig3.qasm 2   # compile the paper's Figure 3 example
python -m dqc.run                                 # reproduce every table and figure
```

## Verification

- 200 random circuits stay equivalent after grouping and reordering (checked with Qiskit operators).
- The commutation rule is checked exhaustively against gate matrices.
- The final distributed program, including communication qubits, is simulated and compared with
  the original circuit.

## Structure

| Path | Contents |
|---|---|
| `dqc/circuit.py` | Gate / Circuit representation, OpenQASM 2 loading |
| `dqc/assignment.py` | Pass 1: qubit assignment |
| `dqc/grouping.py`, `dqc/commutation.py` | Passes 2–3: grouping and reordering |
| `dqc/scheduling.py` | Pass 4: scheduling and depth |
| `dqc/run.py` | Experiments → `results/` |
| `tests/` | Automated tests |
| `docs/` | Concept notes (Persian) |

Qiskit is used only to read input files and to verify results; all compiler passes are hand-written.

## Acknowledgements

Benchmark circuits from [QASMBench](https://github.com/pnnl/QASMBench) (Li et al., PNNL),
© 2020 Battelle Memorial Institute, redistributed under its license (`benchmarks/QASMBench-LICENSE`).

