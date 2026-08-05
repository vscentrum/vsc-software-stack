import os
import sys
import traceback
import importlib.metadata as im

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import cassiopeia as cas


def get_version(*names):
    for name in names:
        try:
            return im.version(name)
        except Exception:
            pass
    return "unknown"


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"[OK] {msg}")


def main():
    print("Versions:")
    print("  cassiopeia:", get_version("cassiopeia-lineage", "cassiopeia"))
    print("  pandas:", get_version("pandas"))
    print("  matplotlib:", get_version("matplotlib"))

    cells = ["cell1", "cell2", "cell3", "cell4", "cell5", "cell6"]
    character_matrix = pd.DataFrame(
        [
            [1, 0, 0, 0, 0],
            [1, 1, 0, 0, 0],
            [1, 1, 2, 0, 0],
            [0, 2, 0, 1, 0],
            [0, 2, 0, 1, 1],
            [0, 2, 3, 1, 1],
        ],
        index=cells,
        columns=["r1", "r2", "r3", "r4", "r5"],
        dtype=int,
    )

    priors = {
        0: {1: 0.10},
        1: {1: 0.08, 2: 0.06},
        2: {2: 0.04, 3: 0.03},
        3: {1: 0.07},
        4: {1: 0.05},
    }

    cell_meta = pd.DataFrame(
        {
            "cluster": ["A", "A", "A", "B", "B", "B"],
            "sample": ["s1", "s1", "s1", "s2", "s2", "s2"],
        },
        index=cells,
    )

    print("\n== Build CassiopeiaTree ==")
    tree = cas.data.CassiopeiaTree(
        character_matrix=character_matrix,
        priors=priors,
        cell_meta=cell_meta,
    )
    check(tree.n_cell == 6, "n_cell == 6")
    check(tree.n_character == 5, "n_character == 5")
    check(set(tree.character_matrix.index) == set(cells), "all cells present in character matrix")

    print("\n== Compute dissimilarity map ==")
    tree.compute_dissimilarity_map(
        dissimilarity_function=cas.solver.dissimilarity_functions.weighted_hamming_distance
    )
    dm = tree.get_dissimilarity_map()
    check(dm is not None, "dissimilarity map exists")
    check(dm.shape == (6, 6), "dissimilarity map shape is 6x6")
    check((dm.values.diagonal() == 0).all(), "dissimilarity diagonal is zero")
    check(set(dm.index) == set(cells), "dissimilarity map row labels match cells")
    check(set(dm.columns) == set(cells), "dissimilarity map column labels match cells")

    print("\n== Reconstruct tree with VanillaGreedySolver ==")
    solver = cas.solver.VanillaGreedySolver()
    solver.solve(tree, collapse_mutationless_edges=True)

    check(tree.root is not None, "tree has a root")
    check(set(tree.leaves) == set(cells), "tree leaves match input cells")
    check(len(tree.internal_nodes) >= 1, "tree has internal nodes")
    check(len(tree.edges) >= len(cells) - 1, "tree has enough edges")

    print("\n== Newick export ==")
    newick = tree.get_newick()
    check(isinstance(newick, str) and len(newick) > 0, "newick export works")

    print("\n== Local plotting ==")
    cas.pl.plot_matplotlib(tree, orient="right")
    out_png = "cassiopeia_smoketest_tree.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()
    check(os.path.exists(out_png), f"{out_png} was created")
    check(os.path.getsize(out_png) > 0, f"{out_png} is non-empty")

    print("\n== Optional imports ==")
    import cassiopeia.preprocess as pp
    import cassiopeia.plotting as pl
    import cassiopeia.simulator as sim
    import cassiopeia.tools as tl
    check(True, "preprocess / plotting / simulator / tools modules import")

    print("\nAll Cassiopeia smoke tests passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)