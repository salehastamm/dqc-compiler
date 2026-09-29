"""
Phase 5 - Commutation rules (paper, section 3.3 and Figure 4).

Two gates COMMUTE if running them in either order gives the same result.
Then the compiler may swap them. That lets it move a gate earlier, so that it
can still join an open group before the group has to be closed.
"""

# Gates that never change a qubit's value in the X basis (the "+/-" basis).
# They are to the X basis what rz, s, t, cz are to the 0/1 basis.
X_DIAGONAL = {"x", "rx", "sx", "sxdg"}


def is_x_diagonal_on(gate, q):
    """True if the gate never changes wire q's value in the X basis."""
    if q not in gate.qubits:
        return True
    if gate.name in X_DIAGONAL:
        return True
    # cx flips its target with an X, which does not change the target's X-basis value.
    if gate.name == "cx":
        return q == gate.qubits[1]
    return False


def can_commute(g1, g2):
    """True if g1 and g2 can safely be swapped.

    Rule: on every qubit the two gates share, both gates must be diagonal in the
    same basis (both 0/1-diagonal, or both X-diagonal). This covers all six rules
    of the paper's Figure 4. It is conservative: it may say False for a pair that
    does commute, but it never says True for a pair that does not.
    """
    for q in g1.qubits:
        if q not in g2.qubits:
            continue                      # not shared: no conflict on this wire
        both_z = g1.is_diagonal_on(q) and g2.is_diagonal_on(q)
        both_x = is_x_diagonal_on(g1, q) and is_x_diagonal_on(g2, q)
        if not (both_z or both_x):
            return False
    return True
