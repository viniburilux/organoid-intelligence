# Reproduction Package for Finding 01

## What is Finding 01?

Finding 01 from the **Organoid Intelligence** project (https://github.com/viniburilux/organoid-intelligence) addresses the question:

> Can simple, interpretable features derived from organoid electrophysiology predict the organoid’s performance in a goal‑directed learning task (cart‑pole balancing)?

The finding shows that baseline statistics (mean firing rate, burstiness, connectivity) and network‑level features have limited predictive power, while a permutation test confirms that the observed Spearman correlation for firing‑rate summary is statistically significant (p ≈ 0.018).

## How to reproduce

1. **Install dependencies**  
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the experiment**  
   The script expects a directory with four CSV files:
   - `experiments.csv`
   - `cartpole_runs.csv`
   - `baseline_summary.csv`
   - `causal_summary.csv`

   Place these files in the `data/` directory (they are already included in this package). Then run:
   ```bash
   python run_experiment_002.py data/ outputs/
   ```

   The script will print a JSON summary with metrics for each model (mean_baseline, median_baseline, firing_rate, network) and permutation test results.

3. **Expected results** (rounded to 3 dp)

   | Model          | MAE   | RMSE  | R²     | Spearman ρ | Permutation p (Spearman) |
   |----------------|-------|-------|--------|------------|--------------------------|
   | mean_baseline  | 30.526| 55.934| -0.093 | -0.301     | 0.839                    |
   | median_baseline| 24.244| 55.871| -0.091 | -0.274     | 0.331                    |
   | firing_rate    | 53.050| 83.016| -1.408 | 0.359      | 0.018                    |
   | network        | 46.933| 70.048| -0.714 | -0.227     | 0.800                    |

   The numbers above match those reported in `evidence/findings.md` of the public repository.

4. **Outputs**  
   - `outputs/results.csv` – per‑fold predictions and metrics  
   - `outputs/oof_predictions.csv` – out‑of‑fold predictions  
   - `outputs/permutation_results.json` – detailed permutation test  
   - `outputs/mae_vs_model.png`, `outputs/r2_vs_model.png` – diagnostic plots (if matplotlib backend allows)

## Notes

- The analysis uses **GroupKFold cross‑validation** by organoid to avoid leakage.
- Seed is fixed (`SEED = 2026`) for reproducibility.
- No private LuxVerso infrastructure (ASIE, LuxMemory, etc.) is required; the script depends only on open‑source scientific libraries.
- The four input CSV files are derived from the public Zenodo dataset (DOI: 10.1038/s41467-022-32115-4, Zenodo 17684862) via a safe conversion script (`convert_goal_directed_safe.py`). If you prefer to regenerate the CSVs from the original Zenodo pickle, include that script and follow the instructions in its docstring.

## License

See the main repository's LICENSE file.