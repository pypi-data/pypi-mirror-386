import sys
import argparse
import json
from pathlib import Path
from statistics import mean
import matplotlib.pyplot as plt


plt.rcParams.update(
    {
        "text.usetex": False,
        "font.family": "serif",
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 300,
    }
)


def load_experiment_data(file_path: Path) -> dict:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}") from e


def compute_averages(data, memory):
    train_data = data["train"]

    avg_memory_percent = (mean(d["memory_avg_mb"] for d in train_data) / memory) * 100

    avg_cpu_percent = mean(d["cpu_avg_percent"] for d in train_data)

    avg_exchange_time = mean(
        d["update_exchange_time"] for d in train_data if "update_exchange_time" in d
    )

    avg_train_time = mean(d["train_time"] for d in train_data)

    return {
        "Avg Memory Utilization (%)": avg_memory_percent,
        "Avg CPU Utilization (%)": avg_cpu_percent,
        "Avg Update Exchange Time (s)": avg_exchange_time,
        "Avg Training Time (s)": avg_train_time,
    }


def plot_horizontal_bar_chart(averages: dict):
    metrics = list(averages.keys())
    values = list(averages.values())
    colors = ["#27AE60"]

    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    y_pos = range(len(metrics))

    bars = ax.barh(y_pos, values, color=colors)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(metrics)
    ax.set_title("Behaviors of On-device", pad=15)
    ax.set_xlabel("")
    ax.set_xticks([])

    max_value = max(values)
    ax.set_xlim((0, max_value * 1.15))

    for i, bar in enumerate(bars):
        width = bar.get_width()
        label = f"{values[i]:.2f}"
        ax.text(
            width + (max_value * 0.01),
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            color="black",
            fontsize=9,
        )

    plt.tight_layout()
    output_path = "device_behaviors.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Figure saved as '{output_path}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Usage: python device_behaviors.py <path_to_experiment_result.json> --memory=<device_memory>"
    )
    parser.add_argument(
        "file_path", type=str, help="Path to experiment result JSON file"
    )
    parser.add_argument("--memory", type=int, required=True, help="Device memory in MB")

    try:
        args = parser.parse_args()
        file_path = Path(args.file_path)

        if args.memory <= 0:
            raise ValueError("Memory must be a positive integer")

        experiment_result = load_experiment_data(file_path)
        averages = compute_averages(experiment_result, args.memory)
        plot_horizontal_bar_chart(averages)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
