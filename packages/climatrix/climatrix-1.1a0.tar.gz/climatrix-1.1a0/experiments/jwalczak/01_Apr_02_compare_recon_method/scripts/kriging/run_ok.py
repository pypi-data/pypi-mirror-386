"""
This module runs experiment of OK method

@author: Jakub Walczak, PhD
"""

import csv
import os
import shutil
from pathlib import Path
from typing import Any

import xarray as xr
from rich.console import Console
from rich.status import Status

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

RESULT_DIR: Path = Path(CLIMATRIX_EXP_DIR) / "results" / "ok"
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
    "nlags": (2, 50),
    "anisotropy_scaling": (1e-5, 5.0),
    "coordinates_type": ("euclidean", "geographic"),
    "variogram_model": (
        "linear",
        "power",
        "gaussian",
        "spherical",
        "exponential",
    ),
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


def update_hparams_csv(hparam_path: Path, hparams: dict[str, Any]):
    fieldnames = [
        "dataset_id",
        "nlags",
        "anisotropy_scaling",
        "coordinates_type",
        "variogram_model",
        "opt_loss",
    ]
    if not hparam_path.exists():
        with open(hparam_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    with open(hparam_path, "a") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(hparams)


def update_metric_csv(metrics_path: Path, metrics: dict[str, Any]):
    fieldnames = ["dataset_id", "RMSE", "MAE", "Max Abs Error", "R^2"]
    if not metrics_path.exists():
        with open(metrics_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    with open(metrics_path, "a") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(metrics)


def is_experiment_done(idx: int | str) -> bool:
    return (PLOT_DIR / f"{idx}_diffs.png").exists()


def run_single_experiment(
    d: str,
    i: int,
    all_samples: int,
    status: Status,
    continuous_update: bool = True,
    reconstruct_dense: bool = True,
):
    cm.seed_all(SEED)
    if is_experiment_done(d):
        console.print(
            f"[bold green]Skipping date {d} as it is already done.[/bold green]"
        )
        return
    status.update(
        f"[magenta]Processing date: {d} ({i + 1}/{all_samples})...",
        spinner="bouncingBall",
    )
    train_dset = xr.open_dataset(
        DSET_PATH / f"ecad_obs_europe_train_{d}.nc"
    ).cm
    val_dset = xr.open_dataset(DSET_PATH / f"ecad_obs_europe_val_{d}.nc").cm
    test_dset = xr.open_dataset(DSET_PATH / f"ecad_obs_europe_test_{d}.nc").cm
    status.update(
        f"[magenta]Optimizing hyper-parameters for date: {d} "
        f"({i + 1}/{all_samples})...",
        spinner="bouncingBall",
    )
    finder = cm.optim.HParamFinder(
        "ok",
        train_dset,
        val_dset,
        metric="mae",
        n_startup_trials=OPTIM_STARTUP_TRIALS,
        n_iters=OPTIM_N_ITERS,
        bounds=BOUNDS,
        random_seed=SEED,
        reconstructor_kwargs={"pseudo_inv": True},
    )
    result = finder.optimize()
    console.print("[bold yellow]Optimized parameters:[/bold yellow]")
    console.print(
        "[yellow]Number of lags:[/yellow]", result["best_params"]["nlags"]
    )
    console.print(
        "[yellow]Anisotropy scaling factor:[/yellow]",
        result["best_params"]["anisotropy_scaling"],
    )
    console.print(
        "[yellow]Coordinates type:[/yellow]",
        result["best_params"]["coordinates_type"],
    )
    console.print(
        "[yellow]Variogram model:[/yellow]",
        result["best_params"]["variogram_model"],
    )
    status.update(
        "[magenta]Reconstructing with optimised parameters...",
        spinner="bouncingBall",
    )
    status.update(
        "[magenta]Concatenating train and validation datasets...",
        spinner="bouncingBall",
    )
    train_val_dset = xr.concat([train_dset.da, val_dset.da], dim="point").cm
    reconstructed_dset = train_val_dset.reconstruct(
        test_dset.domain,
        method="ok",
        nlags=result["best_params"]["nlags"],
        anisotropy_scaling=result["best_params"]["anisotropy_scaling"],
        coordinates_type=result["best_params"]["coordinates_type"],
        variogram_model=result["best_params"]["variogram_model"],
        backend="vectorized",
        pseudo_inv=True,
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
    if reconstruct_dense:
        reconstructed_dense = train_val_dset.reconstruct(
            EUROPE_DOMAIN,
            method="ok",
            nlags=result["best_params"]["nlags"],
            anisotropy_scaling=result["best_params"]["anisotropy_scaling"],
            coordinates_type=result["best_params"]["coordinates_type"],
            variogram_model=result["best_params"]["variogram_model"],
            backend="loop",
            pseudo_inv=True,
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
        "[magenta]Saving test dset to " f"{PLOT_DIR} / {d}_test.png...",
        spinner="bouncingBall",
    )
    test_dset.plot(show=False).get_figure().savefig(PLOT_DIR / f"{d}_test.png")
    status.update("[magenta]Evaluating...", spinner="bouncingBall")
    cmp = cm.Comparison(reconstructed_dset, test_dset)
    cmp.diff.plot(show=False).get_figure().savefig(PLOT_DIR / f"{d}_diffs.png")
    cmp.plot_signed_diff_hist().get_figure().savefig(
        PLOT_DIR / f"{d}_hist.png"
    )
    metrics: dict[str, Any] = cmp.compute_report()
    metrics["dataset_id"] = d
    hyperparams = {
        "dataset_id": d,
        "nlags": result["best_params"]["nlags"],
        "anisotropy_scaling": result["best_params"]["anisotropy_scaling"],
        "coordinates_type": result["best_params"]["coordinates_type"],
        "variogram_model": result["best_params"]["variogram_model"],
        "opt_loss": result["best_score"],
    }
    if continuous_update:
        console.print("[bold green]Updating metrics file...[/bold green]")
        update_metric_csv(METRICS_PATH, metrics)

        console.print(
            "[bold green]Updating hyperparameters summary...[/bold green]"
        )
        update_hparams_csv(HYPERPARAMETERS_SUMMARY_PATH, hyperparams)

    return (metrics, hyperparams)


def run_all_experiments_sequentially(dataset_id: int | None = None):
    dset_idx = get_all_dataset_idx()
    if dataset_id is not None:
        dset_idx = [dset_idx[dataset_id]]
    with console.status("[magenta]Preparing experiment...") as status:
        for i, d in enumerate(dset_idx):
            if is_experiment_done(d):
                console.print(
                    f"[bold green]Skipping date {d} as it is already done.[/bold green]"
                )
                continue
            run_single_experiment(
                d,
                i,
                len(dset_idx),
                status,
                continuous_update=True,
                reconstruct_dense=False,
            )


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
    run_all_experiments_sequentially(args.dataset_id)
