"""
This module runs experiment of IDW method

@author: Jakub Walczak, PhD
"""

import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr
from rich.console import Console

import climatrix as cm

console = Console()

# Setting up the experiment parameters
NAN_POLICY = "resample"
console.print("[bold green]Using NaN policy: [/bold green]", NAN_POLICY)

SEED = 1
console.print("[bold green]Using seed: [/bold green]", SEED)

CLIMATRIX_EXP_DIR = Path(os.environ.get("CLIMATRIX_EXP_DIR", os.getcwd()))
if CLIMATRIX_EXP_DIR is None:
    raise ValueError(
        "CLIMATRIX_EXP_DIR environment variable is not set. "
        "Please set it to the path of your experiment directory."
    )
DSET_PATH = CLIMATRIX_EXP_DIR / "data"
console.print("[bold green]Using dataset path: [/bold green]", DSET_PATH)

OPTIM_STARTUP_TRIALS: int = 50
console.print(
    "[bold green]Using startup trials for optimization[/bold green]",
    OPTIM_STARTUP_TRIALS,
)
OPTIM_N_ITERS: int = 100
console.print(
    "[bold green]Using iterations for optimization[/bold green]", OPTIM_N_ITERS
)

RESULT_DIR: Path = Path(CLIMATRIX_EXP_DIR) / "results" / "idw"
PLOT_DIR: Path = RESULT_DIR / "plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
console.print("[bold green]Plots will be saved to: [/bold green]", PLOT_DIR)

METRICS_PATH: Path = RESULT_DIR / "metrics.csv"
console.print(
    "[bold green]Metrics will be saved to: [/bold green]", METRICS_PATH
)

HYPERPARAMETERS_SUMMARY_PATH: Path = RESULT_DIR / "hparams_summary.csv"
console.print(
    "[bold green]Hyperparameters summary will be saved to: [/bold green]",
    HYPERPARAMETERS_SUMMARY_PATH,
)

BOUNDS = {
    "k": (1, 50),
    "power": (1e-7, 5.0),
}
console.print("[bold green]Hyperparameter bounds: [/bold green]", BOUNDS)

EUROPE_BOUNDS = {"north": 71, "south": 36, "west": -24, "east": 35}
EUROPE_DOMAIN = cm.Domain.from_lat_lon(
    lat=slice(EUROPE_BOUNDS["south"], EUROPE_BOUNDS["north"], 0.1),
    lon=slice(EUROPE_BOUNDS["west"], EUROPE_BOUNDS["east"], 0.1),
    kind="dense",
)


def clear_result_dir():
    console.print(
        "[bold red]Clearing result directory for this experiment...[/bold red]"
    )
    shutil.rmtree(RESULT_DIR, ignore_errors=True)


def create_result_dir():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_dataset_idx() -> list[str]:
    return sorted(
        list({path.stem.split("_")[-1] for path in DSET_PATH.glob("*.nc")})
    )


def idw_scoring_callback(trial: int, hparams: dict, score: float) -> float:
    return score


def run_experiment(dataset_id: int | None = None):
    dset_idx = get_all_dataset_idx()
    if dataset_id is not None:
        dset_idx = [dset_idx[dataset_id]]
    with console.status("[magenta]Preparing experiment...") as status:
        all_metrics = []
        hyperparams = defaultdict(list)
        for i, d in enumerate(dset_idx):
            cm.seed_all(SEED)
            if (PLOT_DIR / f"{d}_reconstructed.png").exists():
                print(f"Skipping {d} as it already exists")
                continue
            status.update(
                f"[magenta]Processing date: {d} ({i + 1}/{len(dset_idx)})...",
                spinner="bouncingBall",
            )
            train_dset = xr.open_dataset(
                DSET_PATH / f"ecad_obs_europe_train_{d}.nc"
            ).cm
            val_dset = xr.open_dataset(
                DSET_PATH / f"ecad_obs_europe_val_{d}.nc"
            ).cm
            test_dset = xr.open_dataset(
                DSET_PATH / f"ecad_obs_europe_test_{d}.nc"
            ).cm
            status.update(
                f"[magenta]Optimizing hyper-parameters for date: {d}"
                f" ({i + 1}/{len(dset_idx)})...",
                spinner="bouncingBall",
            )
            finder = cm.optim.HParamFinder(
                "idw",
                train_dset,
                val_dset,
                metric="mae",
                n_iters=OPTIM_N_ITERS,
                n_startup_trials=OPTIM_STARTUP_TRIALS,
                bounds=BOUNDS,
                random_seed=SEED,
                scoring_callback=idw_scoring_callback,
                exclude=["k_min"],
                reconstructor_kwargs={"k_min": 1},
            )
            result = finder.optimize()
            console.print("[bold yellow]Optimized parameters:[/bold yellow]")
            console.print(
                "[yellow]Power:[/yellow]", result["best_params"]["power"]
            )
            console.print("[yellow]k:[/yellow]", result["best_params"]["k"])
            status.update(
                "[magenta]Reconstructing with optimised parameters...",
                spinner="bouncingBall",
            )
            status.update(
                "[magenta]Concatenating train and validation datasets...",
                spinner="bouncingBall",
            )
            train_val_dset = xr.concat(
                [train_dset.da, val_dset.da], dim="point"
            ).cm
            reconstructed_dset = train_val_dset.reconstruct(
                test_dset.domain,
                method="idw",
                k=result["best_params"]["k"],
                power=result["best_params"]["power"],
            )
            status.update(
                "[magenta]Saving reconstructed dset to "
                f"{PLOT_DIR}/{d}_reconstructed.png...",
                spinner="bouncingBall",
            )
            reconstructed_dset.plot(show=False).get_figure().savefig(
                PLOT_DIR / f"{d}_reconstructed.png"
            )

            status.update(
                "[magenta]Reconstructing to dense Europe domain...",
                spinner="bouncingBall",
            )
            reconstructed_dense = train_val_dset.reconstruct(
                EUROPE_DOMAIN,
                method="idw",
                k=result["best_params"]["k"],
                power=result["best_params"]["power"],
            )
            status.update(
                "[magenta]Saving reconstructed dense dset to "
                f"{PLOT_DIR}/{d}_reconstructed_dense.png...",
                spinner="bouncingBall",
            )
            reconstructed_dense.plot(show=False).get_figure().savefig(
                PLOT_DIR / f"{d}_reconstructed_dense.png"
            )
            status.update(
                "[magenta]Saving test dset to " f"{PLOT_DIR}/{d}_test.png...",
                spinner="bouncingBall",
            )
            test_dset.plot(show=False).get_figure().savefig(
                PLOT_DIR / f"{d}_test.png"
            )
            status.update("[magenta]Evaluating...", spinner="bouncingBall")
            cmp = cm.Comparison(reconstructed_dset, test_dset)
            cmp.diff.plot(show=False).get_figure().savefig(
                PLOT_DIR / f"{d}_diffs.png"
            )
            cmp.plot_signed_diff_hist().get_figure().savefig(
                PLOT_DIR / f"{d}_hist.png"
            )
            metrics: dict[str, Any] = cmp.compute_report()
            metrics["dataset_id"] = d
            all_metrics.append(metrics)

            hyperparams["dataset_id"].append(d)
            hyperparams["k"].append(result["best_params"]["k"])
            hyperparams["power"].append(result["best_params"]["power"])
            hyperparams["opt_loss"].append(result["best_score"])
        status.update(
            "[magenta]Saving quality metrics...", spinner="bouncingBall"
        )
        pd.DataFrame(all_metrics).to_csv(METRICS_PATH)
        status.update(
            "[magenta]Saving hyperparameters summary...",
            spinner="bouncingBall",
        )
        pd.DataFrame(hyperparams).to_csv(HYPERPARAMETERS_SUMMARY_PATH)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run SiNET experiments for a specific dataset."
    )
    parser.add_argument(
        "--dataset_id",
        type=int,
        default=None,
        help="ID of the dataset to run experiments on.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    clear_result_dir()
    create_result_dir()
    args = parse_args()
    run_experiment(args.dataset_id)
