import os, sys, tempfile, subprocess
import polars as pl

root = os.environ["EBROOTDIAMINNN"]
stats_py = os.path.join(root, "diann-stats.py")

tmpdir = tempfile.mkdtemp(prefix="diann-stats-")
parquet = os.path.join(tmpdir, "mini.parquet")

rows = []
for run, run_idx, rt_shift in [("run1", 1, 0.0), ("run2", 2, 0.3)]:
    for pid, mz, charge, pg, irt, im in [
        ("PEPTIDE1", 500.2, 2, "PG1", 10.0, 1.05),
        ("PEPTIDE2", 650.3, 3, "PG2", 20.0, 1.15),
        ("PEPTIDE3", 800.4, 2, "PG3", 30.0, 1.25),
    ]:
        rt = 25.0 + irt * 0.4 + rt_shift
        rows.append({
            "Run": run,
            "Run.Index": run_idx,
            "Precursor.Id": pid,
            "Protein.Group": pg,
            "PG.Q.Value": 0.005,
            "Q.Value": 0.005,
            "Global.Q.Value": 0.005,
            "RT": rt,
            "Predicted.RT": rt - 0.1,
            "iRT": irt,
            "IM": im,
            "Predicted.IM": im - 0.01,
            "Precursor.Mz": mz,
            "Precursor.Charge": charge,
            "Ms1.Apex.Area": 1_000_000.0 + run_idx * 1000 + charge,
            "Ms1.Profile.Corr": 0.95,
            "Normalisation.Factor": 1.0 + 0.01 * run_idx,
            "Ms1.Apex.Mz.Delta": 0.002,
            "Evidence": 5.0,
            "Best.Fr.Mz": 150.0 + charge,
            "Best.Fr.Mz.Delta": 0.001,
            "FWHM": 0.20 + 0.01 * run_idx,
        })

df = pl.DataFrame(rows)
df.write_parquet(parquet)

subprocess.run([sys.executable, stats_py, parquet], cwd=tmpdir, check=True)

runs_pdf = os.path.join(tmpdir, "mini_runs.pdf")
trends_pdf = os.path.join(tmpdir, "mini_trends.pdf")

for path in [runs_pdf, trends_pdf]:
    assert os.path.isfile(path), f"Missing output: {path}"
    assert os.path.getsize(path) > 0, f"Empty output: {path}"

print("Generated:")
print(runs_pdf)
print(trends_pdf)
print("OK")