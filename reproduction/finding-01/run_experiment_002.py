"""Run Experiment 002 on versioned Zenodo-derived tables.

The experiment is intentionally restricted to simple, interpretable methods:
- experiment-level regression of mean top-decile performance;
- GroupKFold by organoid;
- training-fold mean baseline;
- StandardScaler + Ridge(alpha=1.0) for firing and network summaries;
- no learned embeddings, CEBRA, autoencoders or transformers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 2026
N_SPLITS = 5
N_PERMUTATIONS = 1000

FIRING_COLS = [
    "firing_rate_mean_hz",
    "firing_rate_median_hz",
    "firing_rate_max_hz",
    "burstiness_mean",
    "burstiness_median",
]
NETWORK_COLS = [
    "sttc_first_order_offdiag_mean",
    "sttc_multi_order_offdiag_mean",
    "connectivity_mean",
    "connectivity_median",
    "connectivity_max",
    "burst_percent_mean",
    "reactive_units",
]


def metric_record(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | None]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    try:
        if len(np.unique(y_true)) < 2 or len(np.unique(y_pred)) < 2:
            rho = None
        else:
            rho = float(spearmanr(y_true, y_pred).statistic)
    except Exception:
        rho = None
    if rho is not None and not np.isfinite(rho):
        rho = None
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "spearman": rho,
    }


def load_joined(data_dir: Path) -> pd.DataFrame:
    exp = pd.read_csv(data_dir / "experiments.csv")
    runs = pd.read_csv(data_dir / "cartpole_runs.csv")
    base = pd.read_csv(data_dir / "baseline_summary.csv")
    causal = pd.read_csv(data_dir / "causal_summary.csv")
    target = runs.groupby("exp_id", as_index=False).agg(
        experiment_mean_top_decile=("top_decile", "mean"),
        performance_run_count=("top_decile", "count"),
    )
    data = exp.merge(target, on="exp_id", how="left")
    data = data.merge(base, on="exp_id", how="left")
    data = data.merge(causal, on="exp_id", how="left", suffixes=("", "_causal"))
    return data


def estimator_for(name: str):
    if name == "mean_baseline":
        return DummyRegressor(strategy="mean")
    if name == "median_baseline":
        return DummyRegressor(strategy="median")
    if name in {"firing_rate", "network"}:
        return Pipeline([
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ])
    raise ValueError(name)


def evaluate_once(data: pd.DataFrame, feature_sets: dict[str, list[str]], fold_df: pd.DataFrame, y_override: np.ndarray | None = None):
    results: list[dict] = []
    predictions: list[pd.DataFrame] = []
    y = data["experiment_mean_top_decile"].to_numpy(dtype=float) if y_override is None else np.asarray(y_override, dtype=float)
    groups = data["organoid"].astype(str).to_numpy()
    ids = data["exp_id"].astype(str).to_numpy()
    fold_lookup = dict(zip(fold_df["exp_id"], fold_df["fold"]))

    for model_name, cols in feature_sets.items():
        X = np.zeros((len(data), 1), dtype=float) if model_name in {"mean_baseline", "median_baseline"} else data[cols].to_numpy(dtype=float)
        oof = np.full(len(data), np.nan, dtype=float)
        fold_rows = []
        for fold, (train_idx, test_idx) in enumerate(GroupKFold(n_splits=N_SPLITS).split(X, y, groups=groups)):
            assert set(groups[train_idx]).isdisjoint(set(groups[test_idx]))
            model = estimator_for(model_name)
            model.fit(X[train_idx], y[train_idx])
            pred = model.predict(X[test_idx])
            oof[test_idx] = pred
            fold_metric = metric_record(y[test_idx], pred)
            fold_rows.append({"model": model_name, "fold": fold, "n_train": len(train_idx), "n_test": len(test_idx), **fold_metric})
        assert np.isfinite(oof).all()
        pooled = metric_record(y, oof)
        results.append({"model": model_name, "n_samples": len(data), "n_groups": int(pd.Series(groups).nunique()), **pooled})
        predictions.append(pd.DataFrame({
            "exp_id": ids,
            "organoid": groups,
            "fold": [fold_lookup[i] for i in ids],
            "model": model_name,
            "y_true": y,
            "y_pred": oof,
            "residual": y - oof,
            "abs_error": np.abs(y - oof),
        }))
        fold_rows_df = pd.DataFrame(fold_rows)
        yield results[-1], predictions[-1], fold_rows_df


def build_folds(data: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    groups = data["organoid"].astype(str).to_numpy()
    exp_ids = data["exp_id"].astype(str).to_numpy()
    assignments = []
    splitter = GroupKFold(n_splits=N_SPLITS)
    for fold, (_, test_idx) in enumerate(splitter.split(data, data["experiment_mean_top_decile"], groups=groups)):
        for idx in test_idx:
            assignments.append({"exp_id": exp_ids[idx], "organoid": groups[idx], "fold": fold})
    folds = pd.DataFrame(assignments).sort_values("exp_id").reset_index(drop=True)
    assert folds["exp_id"].nunique() == len(data)
    assert folds.groupby("organoid")["fold"].nunique().max() == 1
    folds.to_csv(output_dir / "group_folds.csv", index=False)
    return folds


def permutation_pvalues(data: pd.DataFrame, feature_sets: dict[str, list[str]], folds: pd.DataFrame, observed: pd.DataFrame, output_dir: Path):
    rng = np.random.default_rng(SEED)
    values = {name: {metric: [] for metric in ["mae", "rmse", "r2", "spearman"]} for name in feature_sets}
    y = data["experiment_mean_top_decile"].to_numpy(dtype=float)
    for _ in range(N_PERMUTATIONS):
        shuffled = rng.permutation(y)
        for result, _, _ in evaluate_once(data, feature_sets, folds, shuffled):
            for metric in values[result["model"]]:
                if result[metric] is not None:
                    values[result["model"]][metric].append(result[metric])
    rows = []
    for _, obs in observed.iterrows():
        model = obs["model"]
        row = {"model": model, "n_permutations": N_PERMUTATIONS}
        for metric in ["mae", "rmse", "r2", "spearman"]:
            dist = np.asarray(values[model][metric], dtype=float)
            observed_value = obs[metric]
            if observed_value is None or not np.isfinite(float(observed_value)) or len(dist) == 0:
                row[f"{metric}_permutation_p"] = None
                row[f"{metric}_null_mean"] = None
            else:
                if metric in {"mae", "rmse"}:
                    tail = np.mean(dist <= float(observed_value))
                else:
                    tail = np.mean(dist >= float(observed_value))
                row[f"{metric}_permutation_p"] = float((1 + np.sum(dist <= float(observed_value) if metric in {"mae", "rmse"} else dist >= float(observed_value))) / (len(dist) + 1))
                row[f"{metric}_null_mean"] = float(np.mean(dist))
        rows.append(row)
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "permutation_results.csv", index=False)
    return result


def plot_results(predictions: pd.DataFrame, results: pd.DataFrame, output_dir: Path) -> None:
    order = ["mean_baseline", "median_baseline", "firing_rate", "network"]
    names = {"mean_baseline": "Mean baseline", "median_baseline": "Median baseline", "firing_rate": "Firing-rate", "network": "Network"}
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), dpi=160)
    for ax, model in zip(axes, order):
        sub = predictions[predictions["model"] == model]
        ax.scatter(sub["y_true"], sub["y_pred"], s=28, alpha=0.8)
        lo = float(min(sub["y_true"].min(), sub["y_pred"].min()))
        hi = float(max(sub["y_true"].max(), sub["y_pred"].max()))
        ax.plot([lo, hi], [lo, hi], "k--", linewidth=1)
        row = results[results["model"] == model].iloc[0]
        ax.set_title(names[model])
        ax.set_xlabel("Observed target")
        ax.set_ylabel("OOF prediction")
        ax.text(0.03, 0.97, f"MAE={row['mae']:.2f}\nRMSE={row['rmse']:.2f}", transform=ax.transAxes, va="top", bbox={"facecolor": "white", "alpha": 0.8})
        ax.grid(alpha=0.25)
    fig.suptitle("Experiment 002: group-held-out predictions")
    fig.tight_layout()
    fig.savefig(output_dir / "oof_predictions.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=160)
    x = np.arange(len(order))
    mae = [float(results.loc[results["model"] == m, "mae"].iloc[0]) for m in order]
    rmse = [float(results.loc[results["model"] == m, "rmse"].iloc[0]) for m in order]
    width = 0.36
    ax.bar(x - width / 2, mae, width, label="MAE")
    ax.bar(x + width / 2, rmse, width, label="RMSE")
    ax.set_xticks(x, [names[m] for m in order], rotation=15)
    ax.set_ylabel("Error (lower is better)")
    ax.set_title("Experiment 002: pooled out-of-fold errors")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "metric_comparison.png")
    plt.close(fig)


def main(data_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_data = load_joined(data_dir)
    common_cols = ["experiment_mean_top_decile", "organoid"] + FIRING_COLS + NETWORK_COLS
    data = all_data.dropna(subset=common_cols).copy().reset_index(drop=True)
    data.to_csv(output_dir / "analysis_dataset.csv", index=False)
    folds = build_folds(data, output_dir)
    feature_sets = {
        "mean_baseline": [],
        "median_baseline": [],
        "firing_rate": FIRING_COLS,
        "network": NETWORK_COLS,
    }
    result_rows = []
    prediction_frames = []
    fold_metric_frames = []
    for result, pred, fold_metrics in evaluate_once(data, feature_sets, folds):
        result_rows.append(result)
        prediction_frames.append(pred)
        fold_metric_frames.append(fold_metrics)
    results = pd.DataFrame(result_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    fold_metrics = pd.concat(fold_metric_frames, ignore_index=True)
    results.to_csv(output_dir / "results.csv", index=False)
    predictions.to_csv(output_dir / "oof_predictions.csv", index=False)
    fold_metrics.to_csv(output_dir / "fold_metrics.csv", index=False)
    permutations = permutation_pvalues(data, feature_sets, folds, results, output_dir)
    plot_results(predictions, results, output_dir)
    report = {
        "seed": SEED,
        "n_splits": N_SPLITS,
        "n_permutations": N_PERMUTATIONS,
        "n_all_experiments": int(len(all_data)),
        "n_common_complete_experiments": int(len(data)),
        "n_organoids": int(data["organoid"].nunique()),
        "models": results.to_dict(orient="records"),
        "permutations": permutations.to_dict(orient="records"),
        "sequence_spike_status": "unavailable in versioned derived tables; not forced",
        "leakage_check": "GroupKFold by organoid; each organoid occurs in one fold only; preprocessing is fitted inside each training fold.",
    }
    (output_dir / "experiment_002_results.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
