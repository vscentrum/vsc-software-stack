
#!/usr/bin/env python3
"""
Optuna smoketest.

Tests core optimization, study persistence, pruning,
reproducibility, and optional visualization.

No external datasets or GPU required.
"""

import os
import sys
import tempfile
import traceback

import optuna


def test_import():
    print(f"Optuna version: {optuna.__version__}")
    assert optuna.__version__ == "5.0.0"
    print("PASS: Optuna import and version")



def test_optimization():
    import math

    def objective(trial):
        x = trial.suggest_float("x", -10, 10)
        y = trial.suggest_float("y", -10, 10)
        return (x - 2) ** 2 + (y + 3) ** 2

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=30)

    # Check that all trials completed successfully.
    assert len(study.trials) == 30
    assert all(
        t.state == optuna.trial.TrialState.COMPLETE
        for t in study.trials
    )

    # Check that all objective values are finite.
    assert all(
        math.isfinite(t.value)
        for t in study.trials
    )

    # Check that optimization actually improved the objective.
    assert math.isfinite(study.best_value)
    assert study.best_value < 169.0

    print(f"Best value: {study.best_value:.6f}")
    print(f"Best parameters: {study.best_params}")
    print("PASS: Basic optimization")


def test_reproducibility():
    def objective(trial):
        return trial.suggest_float("x", 0, 1)

    sampler = optuna.samplers.RandomSampler(seed=42)

    study1 = optuna.create_study(
        direction="minimize", sampler=sampler
    )
    study1.optimize(objective, n_trials=10)

    sampler = optuna.samplers.RandomSampler(seed=42)

    study2 = optuna.create_study(
        direction="minimize", sampler=sampler
    )
    study2.optimize(objective, n_trials=10)

    values1 = [t.value for t in study1.trials]
    values2 = [t.value for t in study2.trials]

    assert values1 == values2

    print("PASS: Random sampler reproducibility")


def test_sqlite_storage():
    def objective(trial):
        x = trial.suggest_float("x", -5, 5)
        return (x - 1) ** 2

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "optuna.db")
        storage = f"sqlite:///{db_path}"

        study = optuna.create_study(
            study_name="smoketest",
            storage=storage,
            direction="minimize",
        )
        study.optimize(objective, n_trials=10)

        loaded_study = optuna.load_study(
            study_name="smoketest",
            storage=storage,
        )

        assert len(loaded_study.trials) == 10
        assert loaded_study.best_value == study.best_value

    print("PASS: SQLite persistence and study loading")


def test_pruning():
    def objective(trial):
        x = trial.suggest_float("x", 0, 1)

        for step in range(5):
            value = (x - 0.2) ** 2 + (4 - step) * 0.01

            trial.report(value, step)

            if trial.should_prune():
                raise optuna.TrialPruned()

        return (x - 0.2) ** 2

    study = optuna.create_study(
        direction="minimize",
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=2,
            n_warmup_steps=0,
        ),
    )

    study.optimize(objective, n_trials=20)

    assert len(study.trials) == 20
    assert study.best_trial.value is not None

    print(
        f"Pruned trials: "
        f"{sum(t.state == optuna.trial.TrialState.PRUNED for t in study.trials)}"
    )
    print("PASS: Trial reporting and pruning")


def test_visualization():
    try:
        import plotly
        from optuna.visualization import plot_optimization_history

        study = optuna.create_study(direction="minimize")
        study.optimize(
            lambda trial: trial.suggest_float("x", 0, 1) ** 2,
            n_trials=5,
        )

        fig = plot_optimization_history(study)

        assert fig is not None
        assert len(fig.data) > 0

        print(f"Plotly version: {plotly.__version__}")
        print("PASS: Plotly visualization")

    except ImportError as exc:
        print(f"SKIP: Visualization dependency unavailable: {exc}")


def run_test(name, function):
    print(f"\n{'=' * 60}")
    print(f"Running: {name}")
    print("=" * 60)

    try:
        function()
        return True
    except Exception:
        traceback.print_exc()
        print(f"FAIL: {name}")
        return False


def main():
    tests = [
        ("Import", test_import),
        ("Optimization", test_optimization),
        ("Reproducibility", test_reproducibility),
        ("SQLite storage", test_sqlite_storage),
        ("Pruning", test_pruning),
        ("Visualization", test_visualization),
    ]

    results = []

    for name, function in tests:
        results.append((name, run_test(name, function)))

    print("\n" + "=" * 60)
    print("SMOKETEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")

    failed = [name for name, passed in results if not passed]

    print(f"\nPassed: {len(results) - len(failed)}/{len(results)}")

    if failed:
        print(f"Failed tests: {', '.join(failed)}")
        sys.exit(1)

    print("All Optuna smoketests passed!")


if __name__ == "__main__":
    main()
