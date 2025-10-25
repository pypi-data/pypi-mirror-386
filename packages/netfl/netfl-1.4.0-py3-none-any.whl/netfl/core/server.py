import json
from datetime import datetime

from flwr.server import ServerConfig, start_server
from flwr.common import ndarrays_to_parameters, NDArrays, Metrics, Scalar

from netfl.core.task import Task
from netfl.utils.log import log


class Server:
    def __init__(self, task: Task) -> None:
        self._dataset, self._dataset_length = task.batch_dataset(task.test_dataset())
        self._model = task.model()
        self._strategy = task.aggregation_strategy()
        self._train_configs = task.train_configs()
        self._train_metrics = []
        self._evaluate_metrics = []

        task.print_configs(self._model)

    def train_configs(self, round: int) -> dict[str, Scalar]:
        return {
            "round": round,
        }

    def train_metrics(self, metrics: list[tuple[int, Metrics]]) -> Metrics:
        train_metrics = [m for _, m in metrics]
        train_metrics = sorted(train_metrics, key=lambda m: m["client_id"])
        self._train_metrics.extend(train_metrics)
        return {}

    def evaluate(
        self, round: int, parameters: NDArrays, configs: dict[str, Scalar]
    ) -> tuple[float, dict[str, Scalar]]:
        self._model.set_weights(parameters)

        loss, accuracy = self._model.evaluate(
            self._dataset,
            verbose="2",
        )

        self._evaluate_metrics.append(
            {
                "round": round,
                "loss": loss,
                "accuracy": accuracy,
                "dataset_length": self._dataset_length,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return (
            loss,
            {"accuracy": accuracy},
        )

    def print_metrics(self):
        metrics = {
            "train": self._train_metrics,
            "evaluate": self._evaluate_metrics,
        }
        log(f"[METRICS]\n{json.dumps(metrics, indent=2, default=str)}")

    def start(self, server_port: int) -> None:
        strategy_type, strategy_args = self._strategy
        initial_parameters = ndarrays_to_parameters(self._model.get_weights())

        strategy = strategy_type(
            **strategy_args,
            on_fit_config_fn=self.train_configs,  # type: ignore[arg-type]
            fit_metrics_aggregation_fn=self.train_metrics,  # type: ignore[arg-type]
            fraction_evaluate=0,  # type: ignore[arg-type]
            initial_parameters=initial_parameters,  # type: ignore[arg-type]
            min_fit_clients=self._train_configs.num_clients,  # type: ignore[arg-type]
            min_evaluate_clients=self._train_configs.num_clients,  # type: ignore[arg-type]
            min_available_clients=self._train_configs.num_clients,  # type: ignore[arg-type]
            evaluate_fn=self.evaluate,  # type: ignore[arg-type]
        )

        start_server(
            config=ServerConfig(num_rounds=self._train_configs.num_rounds),
            server_address=f"0.0.0.0:{server_port}",
            strategy=strategy,
        )

        self.print_metrics()
        log("Server has stopped")
