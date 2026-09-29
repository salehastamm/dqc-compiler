"""
Numbers copied from the paper (Bandini et al., arXiv 2602.24062), Table 1.

Each entry:  circuit file name -> (EPR no opt, EPR limit=3 opt, EPR unlimited opt)
All results use 2 QPUs.
"""

TABLE1 = {
    "adder_n28":        (11, 7, 5),
    "adder_n64":        (11, 7, 5),
    "adder_n118":       (11, 7, 5),
    "cat_n35":          (1, 1, 1),
    "dnn_n33":          (36, 20, 6),
    "dnn_n51":          (52, 28, 6),
    "ghz_n40":          (1, 1, 1),
    "ising_n34":        (2, 2, 2),
    "knn_n41":          (36, 18, 6),
    "multiplier_n45":   (290, 209, 159),
    "multiplier_n75":   (862, 604, 459),
    "multiplier_n350":  (13228, 11108, 8761),
    "qft_n29":          (410, 230, 118),
    "qft_n63":          (702, 364, 51),
    "qft_n320":         (702, 364, 51),
    "qugan_n39":        (40, 22, 6),
    "qugan_n71":        (72, 45, 13),
    "qugan_n111":       (112, 66, 14),
    "qugan_n395":       (408, 319, 29),
    "qv_n32":           (589, 589, 585),
    "qv_n100":          (6526, 6522, 6442),
    "swap_test_n25":    (24, 12, 4),
    "swap_test_n41":    (36, 18, 6),
    "swap_test_n83":    (80, 40, 4),
    "wstate_n76":       (2, 2, 2),
    "wstate_n118":      (2, 2, 2),
    "square_root_n45":  (5415, 4411, 3983),
}
